<!--
ts: 2026-01-29T13:00:00Z | git: <to-be-filled> | path: PORTS.md
-->
# PORTS

Port allocations for this project.

**⚠️ NOTE:** This file lists ports THIS PROJECT uses. For global port scheme, see `/opt/bootstrap/PORTS.md`

---

## Port Allocation Type

**This project uses:** [Select one]
- ☐ **Type A: SPI-Hosted** - Uses port scheme from `/opt/bootstrap/PORTS.md`
- ☐ **Type B: External Webhosting** - No ports needed (runs on webhost)
- ☐ **Type C: VPS/Cloud** - Custom ports on VPS

---

## TYPE A: SPI-Hosted Services

### Development Ports (61xxx)

| Port | Service | Type | Description | Status |
|------|---------|------|-------------|--------|
| 61XXY | <service>-api | API | <description> | Active |
| 61XXY | <service>-ui | Web UI | <description> | Active |
| 61XXY | <service>-ws | WebSocket | <description> | Reserved |
| 61XXY | <service>-db | Database | <description> | Active |

### Acceptance Ports (64xxx)

| Port | Service | Type | Description | Status |
|------|---------|------|-------------|--------|
| 64XXY | <service>-api | API | <description> | Active |
| 64XXY | <service>-ui | Web UI | <description> | Active |

### Production Ports (63xxx)

| Port | Service | Type | Description | Status |
|------|---------|------|-------------|--------|
| 63XXY | <service>-api | API | <description> | Active |
| 63XXY | <service>-ui | Web UI | <description> | Active |

---

## TYPE B: External Webhosting

**No ports needed** - Service runs on external webhost.

**Deployment targets:**
- Acceptance: `accept.domain.tld`
- Production: `domain.tld`

**Note:** See DEPLOY.md for webhosting deployment procedures.

---

## TYPE C: VPS/Cloud Hosted

### VPS Ports

| Port | Service | Environment | Description | Access |
|------|---------|-------------|-------------|--------|
| XXXX | <service>-api | Staging | API endpoint | VPN |
| XXXX | <service>-api | Production | API endpoint | Public |
| XXXX | <service>-ui | Staging | Web interface | VPN |
| XXXX | <service>-ui | Production | Web interface | Public |

**Firewall Rules:** See VPS provider console or infrastructure-as-code config.

---

## Port Reservation

**Reserved in global registry:** [Yes/No]
**Global registry location:** `/opt/bootstrap/PORTS.md`
**Category:** [Platform/Education/Organization/Healthcare/AI/Media/Communication/Analytics/Utilities]

---

## Firewall Configuration

### Type A: SPI-Hosted

```bash
# Development (61xxx) - LAN only, no firewall changes needed
# Acceptance (64xxx) - Tailscale VPN, configure in Tailscale ACLs
# Production (63xxx) - Configure based on access scope

# Example: Allow public access to production web UI (63XXX)
sudo ufw allow 63XXX/tcp comment '<project>-prod-ui'
```

### Type C: VPS/Cloud

```bash
# VPS firewall rules (example: DigitalOcean, AWS Security Groups)
# Configure in provider console or via infrastructure-as-code

# Example: Allow HTTPS traffic
ufw allow 443/tcp
ufw allow 80/tcp  # Redirect to HTTPS
```

---

## Health Checks

### Type A Endpoints

- Development: `http://localhost:61XXY/health`
- Acceptance: `http://localhost:64XXY/health` (via Tailscale)
- Production: `http://localhost:63XXY/health` (via Tailscale)

### Type C Endpoints

- Staging: `https://staging.domain.tld/health`
- Production: `https://domain.tld/health`

---

## Monitoring

**Port monitoring:** [Tool name, e.g., Prometheus, UptimeRobot]
**Alert threshold:** [Response time, downtime duration]
**On-call:** [Contact info or escalation path]

---

## Migration Notes

**Legacy ports:** [List any old ports this project migrated from]
**Migration date:** [Date when migrated to new scheme]
**Old port mapping:**

| Old Port | New Port | Migrated On | Notes |
|----------|----------|-------------|-------|
| 5XXX | 61XXY | YYYY-MM-DD | Description |

---

## Related Documentation

- `/opt/bootstrap/PORTS.md` - Global port allocation scheme
- `DEPLOY.md` - Deployment procedures (includes port configuration)
- `ARCHITECTURE.md` - Technical architecture
- `/opt/tools/scripts/` - Deployment helper scripts

---

**Last Updated:** [YYYY-MM-DD]
**Maintained By:** [Project team]
