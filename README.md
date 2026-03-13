# openclaw-hardened

Security-hardened deployment framework for [OpenClaw](https://github.com/openclaw) with defense-in-depth.

## What's Included

- **Bootstrap** — prepares a bare Ubuntu host: system user, Docker, Node.js, OpenClaw binary
- **Ansible roles** for Docker hardening (gVisor), egress control (Pipelock), firewall (nftables), LLM proxy (LlamaFirewall), credential proxy (Locksmith), telemetry stack (OTel/Prometheus/Phoenix/Grafana/Caddy)
- **Agent state management** — clone repos, link workspaces, restore memory
- **Verification** — automated security posture checks

## Prerequisites

- A target host running Ubuntu 22.04+ (Debian also supported)
- SSH access with sudo privileges
- Ansible 2.15+ on the control machine
- Required Ansible collections:
  ```bash
  ansible-galaxy collection install -r requirements.yml
  ```

## Quick Start

1. Clone this repo and create a site config repo:
   ```bash
   git clone https://github.com/SentientSwarm/openclaw-hardened.git
   mkdir my-site && cd my-site
   cp -r ../openclaw-hardened/examples/* .
   ```

2. Edit the example files with your deployment values (see [Site Config Schema](docs/site-config-schema.md))

3. Bootstrap vault secrets:
   ```bash
   ansible-playbook bootstrap-vault.yml --ask-vault-pass
   ```

4. Deploy (all phases):
   ```bash
   ./run.sh --ask-vault-pass --ask-become-pass
   ```

## Deployment Phases

| Phase | Tag | What it does |
|-------|-----|-------------|
| Bootstrap | `bootstrap` | System user, Docker, Node.js, pnpm, OpenClaw binary, fail2ban |
| Hardening | `phase2` | gVisor, Pipelock, nftables, LlamaFirewall, Locksmith, telemetry |
| Configuration | `phase3` | Onboard, render openclaw.json, systemd service, agent state |
| Verification | `verify` | Security posture checks |

Run individual phases with `--tags`:
```bash
./run.sh --ask-vault-pass --ask-become-pass --tags bootstrap
./run.sh --ask-vault-pass --ask-become-pass --tags verify
```

### Skipping Bootstrap

If you manage Phase 1 externally (e.g., your own provisioning tooling), set `bootstrap.enabled: false` in your site config. The playbook will verify that the openclaw user and Docker exist before proceeding to Phase 2.

## Documentation

- [Site Config Schema](docs/site-config-schema.md) — all variables documented
- [Design](docs/2026-03-08-platform-site-split-design.md) — architecture overview

## License

MIT
