# Draft: studio-1 to robin-box via a restricted SSH jump

Status: proposal only. No firewall deployment, account, VM or Hermes profile
has been created for this spike. The spike is blocked on host firewall approval.

The existing agents guard rejects host output to agentbr0 and input replies
from that bridge. The Incus agents-egress ACL also has no ingress allow.
An Incus proxy or ordinary ProxyJump therefore needs firewall exceptions.

## Proposed path

studio-1 -> existing evo SSH listener (22) -> dedicated jump UID -> one pinned
robin-box IPv4 address (22). The TCP connection to the VM is host originated;
no FORWARD exception, extra LAN listener, Pipelock change or NAT rule is needed.
The VM authenticates a separate dedicated public key for unprivileged `robin`.
Private keys remain on studio-1; agent forwarding is disabled.

`agents_guard.ssh_jumps` defaults to empty. One example, **not a site setting**:

```yaml
# Add inside the complete existing agents_guard dictionary; do not replace it.
ssh_jumps:
  - uid: 61234                 # example only: allocate an unused dedicated UID
    local_address: 10.250.0.1  # agentbr0 gateway
    vm_address: 10.250.0.10    # example only: reserve/check availability first
```

The guard permits only that UID's output from the gateway to that VM on TCP22,
and that VM's established TCP22 replies to the gateway. Bridge forwarding drops
remain unchanged. The dormant openclaw template receives the same output rule;
its existing established-input rule covers replies. An accept in one base chain
does not override a drop in another. No claim of complete network isolation is
made until all base chains and the Incus ACL have been inspected again.

## Prerequisites for a later, separately approved deployment

1. Snapshot all nft rules, Incus network/ACL config and the existing guard file.
   Check the full ruleset again: evo currently has **no live inet openclaw**.
   **Never run the full playbook or load /etc/nftables.conf on evo for this
   spike.** Its dormant output policy previously caused a production outage.
2. Reserve a free IPv4 address on agentbr0 for robin-box and an unused dedicated
   non-root jump UID. Confirm bridge source address selection. Provisioning
   those and the identity is outside this draft's implemented tasks.
3. Configure the jump account with public-key-only authentication, no password,
   no session/shell/exec/subsystem access (`MaxSessions 0`), no TTY, no user rc,
   no agent/X11 forwarding, `AllowTcpForwarding local`, `PermitOpen VM_IP:22`,
   and `PermitListen none`. Restrict its authorized key to studio-1's actual
   source IP (192.168.50.13 for the LAN path). Use `restrict,port-forwarding`
   together with `permitopen="VM_IP:22"` on the key. A forced command alone does
   not restrict `ssh -W` forwarding. Verify effective sshd policy and OpenSSH
   syntax before any separately coordinated host change. Do not reuse a
   general host login or permit any other destination.
4. Add one Incus agents-egress **ingress** allow: source 10.250.0.1/32,
   destination the pinned VM /32, protocol tcp, destination port 22; preserve
   all existing rules/default rejects. Verify stateful return handling and
   that a second VM and arbitrary LAN sources cannot reach the target. No
   general VM egress exception is intended.
5. Render the guard with one exact tuple; `nft -c -f` it without loading first.
   Only after approval, apply the **agents_guard table only**, using its
   existing atomic table replacement. Do not load the main ruleset or restart
   shared services. Re-run the fence proof matrix and SSH negative tests.
6. Pin and independently verify both SSH host keys on studio-1. Use a dedicated
   SSH host alias with ProxyJump, IdentitiesOnly yes, IdentityFile and
   StrictHostKeyChecking yes. Do not use accept-new for the spike path.
7. Resume the throwaway Hermes spike. Audit/disable its default SSH file sync
   and environment passthrough before connecting: credentials must not move
   into the VM. Inspect Hermes's effective SSH arguments/config to verify the
   alias and strict host-key settings are honored.

This PR implements only optional nft template rules, validation and offline
render checks. It does not deploy the jump account, sshd configuration, Incus
ACL or site config. Those require a reviewed deployment plan before unblocking.

## Rollback

For a later deployment, first remove/disable only the dedicated jump key to
prevent new sessions. Restore the saved guard file and replace only the
agents_guard table, then remove just the added Incus ACL rule and jump identity.
Check for and terminate that dedicated UID's remaining forwarding sessions;
the existing output established accept is not a per-UID session revocation.
Never flush the ruleset, load the dormant main ruleset or restart Incus.
No live rollback is needed for this un-applied draft.

## Offline checks

Use an existing Python with Jinja2 (the Ansible Python works):

```sh
python -B -m unittest discover -s tests -v
ANSIBLE_YAML_FILENAME_EXT=.yml,.yaml,.json,.example ansible-playbook -i examples/hosts.yml.example playbook.yml --syntax-check
```

These checks do not prove nft kernel acceptance, effective sshd restrictions,
Incus conntrack behavior or reachability. Those remain deployment gates.
