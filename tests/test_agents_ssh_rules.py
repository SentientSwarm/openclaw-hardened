"""Offline rendering checks only; never load the generated firewall rules."""
from pathlib import Path
import unittest

from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]


def render(template, jumps=None):
    guard = {
        "enabled": True, "bridge": "agentbr0", "bridge_cidr": "10.250.0.0/24",
        "pipelock_address": "192.0.2.20",
        "locksmith_forward": {
            "listen_address": "10.250.0.1", "port": 9200,
            "upstream_ip": "192.0.2.13", "upstream_port": 9200,
            "upstream_interface": "eth0",
        },
    }
    if jumps is not None:
        guard["ssh_jumps"] = jumps
    env = Environment(loader=FileSystemLoader(ROOT / "roles/nftables/templates"),
                      undefined=StrictUndefined)
    return env.get_template(template).render(
        agents_guard=guard, pipelock={"listen": "0.0.0.0:8888"},
        inventory_hostname="test", network={
            "mgmt_cidrs": [], "allowed_lan_ips": [],
            "docker_cidr": "172.16.0.0/12", "inference_ports": [443],
            "gateway_ip": "192.0.2.1",
        }, openclaw={"gateway_port": 18789},
        llamafirewall={"enabled": False}, telemetry={"enabled": False})


class SSHRulesTest(unittest.TestCase):
    def test_missing_and_empty_list_leave_ssh_closed(self):
        for template in ("agents-guard.nft.j2", "nftables.conf.j2"):
            self.assertEqual(render(template), render(template, []))
            self.assertNotIn("agents-ssh-", render(template))

    def test_jump_is_scoped_and_does_not_allow_forwarding(self):
        jumps = [{"uid": 61234, "local_address": "10.250.0.1",
                  "vm_address": "10.250.0.10"}]
        guard = render("agents-guard.nft.j2", jumps)
        outgoing = ('oifname "agentbr0" ip saddr 10.250.0.1 ip daddr 10.250.0.10 '
                    'meta skuid 61234 tcp dport 22 accept comment "agents-ssh-jump"')
        reply = ('iifname "agentbr0" ip saddr 10.250.0.10 ip daddr 10.250.0.1 '
                 'tcp sport 22 ct state established accept comment "agents-ssh-return"')
        self.assertIn(outgoing, guard)
        self.assertIn(reply, guard)
        self.assertLess(guard.index(reply), guard.index('drop comment "agents-no-ingress"'))
        self.assertLess(guard.index(outgoing), guard.index('drop comment "agents-no-host-output"'))
        forward = guard.split("chain forward {", 1)[1].split("chain output {", 1)[0]
        self.assertNotIn("accept", "\n".join(line for line in forward.splitlines()
                                           if not line.lstrip().startswith("#")
                                           and "policy accept" not in line))
        # An accept in agents_guard cannot override a drop in another base chain.
        main = render("nftables.conf.j2", jumps)
        self.assertIn(outgoing, main)
        self.assertIn("ct state established,related accept", main)

    def test_multiple_jumps_do_not_form_address_uid_cross_product(self):
        jumps = [{"uid": 61234, "local_address": "10.250.0.1", "vm_address": "10.250.0.10"},
                 {"uid": 61235, "local_address": "10.250.0.1", "vm_address": "10.250.0.11"}]
        for template in ("agents-guard.nft.j2", "nftables.conf.j2"):
            rules = render(template, jumps)
            self.assertIn("ip daddr 10.250.0.10 meta skuid 61234 tcp dport 22", rules)
            self.assertIn("ip daddr 10.250.0.11 meta skuid 61235 tcp dport 22", rules)
            self.assertNotIn("ip daddr 10.250.0.10 meta skuid 61235", rules)
            self.assertNotIn("ip daddr 10.250.0.11 meta skuid 61234", rules)


if __name__ == "__main__":
    unittest.main()
