<!--
ts: 2025-12-31T14:55:00Z | git: <to-be-filled> | path: PORTS.md
-->

# PORT ALLOCATION REGISTRY

This file documents the port allocation scheme for all SPI services and provides a global registry of reserved ports.

## PORT ALLOCATION SCHEME (61000-65999)

**⚠️ CRITICAL: TCP/IP ports are limited to 0-65535 (16-bit). The original 5-digit scheme was invalid.**

**Revised 4-digit scheme using high port ranges:**

### Primary Digit Structure (Position 1-2)

| Range | Environment | Purpose |
|-------|-------------|---------|
| **61xxx** | Development | Local development on SPI (6**1** = dev) |
| **65xxx** | Testing | Testing environment (6**5** = test/max) |
| **64xxx** | Acceptance | Staging/acceptance environment (6**4** = accept) |
| **63xxx** | Production | Live production services (6**3** = prod) |

### Secondary Digit Structure (Position 3)

| Range | Service Type | Examples |
|-------|--------------|----------|
| **6x1xx** | API Services | REST APIs, GraphQL, RPC |
| **6x3xx** | MCP Servers | Model Context Protocol servers |
| **6x5xx** | Databases | MySQL, PostgreSQL, MongoDB, Neo4j, ChromaDB |
| **6x6xx** | AI Model Backends | llama.cpp, vLLM, Ollama inference servers |
| **6x7xx** | WebSockets | Real-time communication, live updates |
| **6x9xx** | Web UIs | Dashboards, admin panels, user interfaces |

### Tertiary Digit Structure (Position 4)

| Range | Network Scope | Access Level |
|-------|---------------|--------------|
| **6xx1x** | LAN Only | Local network (192.168.x.x, 100.x.x.x) |
| **6xx3x** | Personal VPN | Tailscale/Headscale/VPN only |
| **6xx5x** | Group/Cooperation | Shared access for teams |
| **6xx7x** | External Non-Prod | Public internet (test/demo) |
| **6xx9x** | External Production | Public internet (production) |

### Quaternary Digit Structure (Position 5)

**6xxxY** - Service Instance (Y = 0-9, for multiple instances of same service)

Examples:
- 0 = Primary instance
- 1-9 = Additional instances, different projects, or service variants

---

## PORT ALLOCATION EXAMPLES

**Format:** `6[ENV][TYPE][SCOPE][INSTANCE]`
- ENV: 1=Dev, 3=Prod, 4=Accept, 5=Test
- TYPE: 1=API, 3=MCP, 5=DB, 6=AIModel, 7=WS, 9=Web
- SCOPE: 1=LAN, 3=VPN, 5=Group, 7=ExtNonProd, 9=ExtProd
- INSTANCE: 0-9 (service instance/variant)

### Development Environment (61xxx)

| Port | Service | Type | Scope | Description |
|------|---------|------|-------|-------------|
| 61110 | platform-api | API | LAN | Platform API (dev) |
| 61310 | platform-mcp | MCP | LAN | Platform MCP server (dev) |
| 61510 | postgres-dev | Database | LAN | PostgreSQL development |
| 61710 | platform-ws | WebSocket | LAN | Platform WebSocket (dev) |
| 61910 | platform-ui | Web UI | LAN | Platform web dashboard (dev) |
| 61119 | tickets-api | API | LAN | Ticket service API (dev) |
| 61319 | tickets-mcp | MCP | LAN | Ticket service MCP (dev) |
| 61919 | tickets-ui | Web UI | LAN | Ticket service web UI (dev) |
| 61614 | llama-chat-model | AI Model | LAN | Local chat model (Dolphin-Mistral-24B) |
| 61615 | llama-reasoning-model | AI Model | LAN | Local reasoning model (DeepSeek-R1-14B) |
| 61616 | llama-coding-model | AI Model | LAN | Local coding model (Qwen2.5-Coder-32B) |
| 61617 | llama-vision-model | AI Model | LAN | Local vision model (reserved) |

### Testing Environment (65xxx)

| Port | Service | Type | Scope | Description |
|------|---------|------|-------|-------------|
| 65110 | platform-api | API | LAN | Platform API (test) |
| 65910 | platform-ui | Web UI | LAN | Platform web dashboard (test) |
| 65119 | tickets-api | API | LAN | Ticket service API (test) |
| 65919 | tickets-ui | Web UI | LAN | Ticket service web UI (test) |

### Acceptance Environment (64xxx)

| Port | Service | Type | Scope | Description |
|------|---------|------|-------|-------------|
| 64130 | platform-api | API | VPN | Platform API (accept, Tailscale) |
| 64930 | platform-ui | Web UI | VPN | Platform web dashboard (accept) |
| 64119 | tickets-api | API | LAN | Ticket service API (accept) |
| 64319 | tickets-mcp | MCP | LAN | Ticket service MCP (accept) |
| 64919 | tickets-ui | Web UI | LAN | Ticket service web UI (accept) |
| 64614 | llama-chat-model | AI Model | LAN | Local chat model (accept) |
| 64615 | llama-reasoning-model | AI Model | LAN | Local reasoning model (accept) |
| 64616 | llama-coding-model | AI Model | LAN | Local coding model (accept) |

### Production Environment (63xxx)

| Port | Service | Type | Scope | Description |
|------|---------|------|-------|-------------|
| 63130 | platform-api | API | VPN | Platform API (prod, Tailscale) |
| 63190 | public-api | API | Ext Prod | Public-facing API (production) |
| 63930 | platform-ui | Web UI | VPN | Platform web dashboard (prod) |
| 63990 | public-ui | Web UI | Ext Prod | Public-facing web UI (production) |
| 63119 | tickets-api | API | LAN | Ticket service API (prod) |
| 63319 | tickets-mcp | MCP | LAN | Ticket service MCP (prod) |
| 63919 | tickets-ui | Web UI | LAN | Ticket service web UI (prod) |
| 63614 | llama-chat-model | AI Model | LAN | Local chat model (prod) |
| 63615 | llama-reasoning-model | AI Model | LAN | Local reasoning model (prod) |
| 63616 | llama-coding-model | AI Model | LAN | Local coding model (prod) |

---

## GLOBAL PORT REGISTRY

### Platform/Infrastructure (Category 0)

#### Development (1x1x0)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11100 | platform-core-api | Platform core API (dev) | Reserved |
| 13100 | platform-core-mcp | Platform MCP server (dev) | Reserved |
| 15100 | postgres-dev | PostgreSQL development database | Reserved |
| 61514 | neo4j-http-dev | Neo4j HTTP API (dev) | Active |
| 61515 | neo4j-bolt-dev | Neo4j Bolt protocol (dev) | Active |
| 61517 | chromadb-dev | ChromaDB development | Active |
| 19100 | platform-core-ui | Platform web dashboard (dev) | Reserved |

#### Production (9x3x0)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 91300 | platform-core-api | Platform core API (prod) | Reserved |
| 93300 | platform-core-mcp | Platform MCP server (prod) | Reserved |
| 63514 | neo4j-http-prod | Neo4j HTTP API (prod) | Reserved |
| 63515 | neo4j-bolt-prod | Neo4j Bolt protocol (prod) | Reserved |
| 63517 | chromadb-prod | ChromaDB production | Reserved |
| 99300 | platform-core-ui | Platform web dashboard (prod) | Reserved |

### Education Services (Category 1)

#### Development (1x1x1)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11111 | sis-api | School info screens API (dev) | Reserved |
| 19111 | sis-ui | School info screens web UI (dev) | Reserved |
| 11121 | mijnschool-api | Mijnschool Keycloak API (dev) | Reserved |
| 19121 | mijnschool-ui | Mijnschool web UI (dev) | Reserved |

#### Acceptance (7x3x1)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 71311 | sis-api | School info screens API (accept) | Reserved |
| 79311 | sis-ui | School info screens web UI (accept) | Reserved |

#### Production (9x9x1)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 91911 | sis-api | School info screens API (prod) | Reserved |
| 99911 | sis-ui | School info screens web UI (prod, public) | Reserved |

### Organization Services (Category 2)

#### Development (1x1x2)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11112 | eventkaart-api | Event mapping API (dev) | Reserved |
| 19112 | eventkaart-ui | Event mapping web UI (dev) | Reserved |
| 11122 | bubbles-api | 3D Bubbles API (dev) | Reserved |
| 19122 | bubbles-ui | 3D Bubbles web UI (dev) | Reserved |

#### Production (9x9x2)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 91912 | eventkaart-api | Event mapping API (prod) | Reserved |
| 99912 | eventkaart-ui | Event mapping web UI (prod, public) | Reserved |

### Public/Identity Services (Category 3)

#### Development (1x1x3)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11113 | uniek-iam-api | uNiek IAM API (dev) | Reserved |
| 19113 | uniek-iam-ui | uNiek IAM web UI (dev) | Reserved |
| 11123 | idm-keycloak | Keycloak identity mgmt (dev) | Reserved |
| 19123 | idm-ui | IDM admin UI (dev) | Reserved |

#### Production (9x3x3)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 91313 | uniek-iam-api | uNiek IAM API (prod, Tailscale) | Reserved |
| 99313 | uniek-iam-ui | uNiek IAM web UI (prod, Tailscale) | Reserved |

### Healthcare Services (Category 4)

#### Development (1x1x4)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11114 | meneer-zorg-api | Meneer Zorg API (dev) | Reserved |
| 19114 | meneer-zorg-ui | Meneer Zorg web UI (dev) | Reserved |

#### Acceptance (7x7x4)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 71714 | meneer-zorg-api | Meneer Zorg API (accept, ext non-prod) | Reserved |
| 79714 | meneer-zorg-ui | Meneer Zorg web UI (accept, ext non-prod) | Reserved |

#### Production (9x9x4)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 91914 | meneer-zorg-api | Meneer Zorg API (prod, ext) | Reserved |
| 99914 | meneer-zorg-ui | Meneer Zorg web UI (prod, public) | Reserved |

### AI Services (Category 5)

#### Development (61xx5)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 61115 | spi-manager-api | Model router API (dev) | Reserved |
| 61315 | spi-manager-mcp | Model router MCP (dev) | Reserved |
| 61915 | spi-manager-ui | Model router web UI (dev) | Reserved |
| 61614 | llama-chat-model | Local chat model backend (dev) | Active |
| 61615 | llama-reasoning-model | Local reasoning model backend (dev) | Active |
| 61616 | llama-coding-model | Local coding model backend (dev) | Active |
| 61617 | llama-vision-model | Local vision model backend (dev) | Reserved |
| 61610 | localai-server | LocalAI inference platform (dev) | Active |
| 11125 | scg-api | Character generator API (dev) | Reserved |
| 11135 | sag-api | Avatar generator API (dev) | Reserved |
| 11145 | sig-api | Image generator API (dev) | Reserved |
| 11155 | ssg-api | Sound generator API (dev) | Reserved |

#### Production (63xx5)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 63115 | spi-manager-api | Model router API (prod, VPN) | Reserved |
| 63315 | spi-manager-mcp | Model router MCP (prod, VPN) | Reserved |
| 63915 | spi-manager-ui | Model router web UI (prod, VPN) | Reserved |
| 63614 | llama-chat-model | Local chat model backend (prod) | Reserved |
| 63615 | llama-reasoning-model | Local reasoning model backend (prod) | Reserved |
| 63616 | llama-coding-model | Local coding model backend (prod) | Reserved |
| 91325 | scg-api | Character generator API (prod) | Reserved |
| 91335 | sag-api | Avatar generator API (prod) | Reserved |

### Media/Content Services (Category 6)

#### Development (1x1x6)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11116 | svg-api | Video generator API (dev) | Reserved |
| 11126 | vn-media | VN media conversation logs (dev) | Reserved |

### Communication Services (Category 7)

#### Development (1x1x7)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11117 | gmr-api | Message router API (dev) | Reserved |
| 19117 | gmr-ui | Message router web UI (dev) | Reserved |
| 11127 | aiid-api | AI Identity API (dev) | Reserved |
| 17127 | aiid-ws | AI Identity WebSocket (dev) | Reserved |
| 19127 | aiid-ui | AI Identity web UI (dev) | Reserved |

### Analytics Services (Category 8)

#### Development (1x1x8)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11118 | analytics-api | Analytics API (dev) | Reserved |
| 19118 | analytics-ui | Analytics dashboard (dev) | Reserved |

### Utilities (Category 9)

#### Development (1x1x9)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 11119 | tickets-api | Ticket system API (dev) | Reserved |
| 13119 | tickets-mcp | Ticket system MCP (dev) | Reserved |
| 19119 | tickets-ui | Ticket system web UI (dev) | Reserved |
| 61138 | ntfy-api | Notification service (dev, Tailscale) | Active |
| 61120 | tickets-chat-api | RocketChat API (dev) | Active |
| 61520 | tickets-chat-db | MongoDB for chat (dev) | Active |
| 61920 | tickets-chat-web | RocketChat Web UI (dev) | Active |
| 61921 | tickets-chat-video | Jitsi Meet Web (dev) | Active |
| 11129 | scheduler-api | Scheduler API (dev) | Reserved |
| 11139 | sds-api | Design system API (dev) | Reserved |
| 19139 | sds-ui | Design system gallery (dev) | Reserved |

#### Acceptance (64xx9)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 64138 | ntfy-api | Notification service (accept, Tailscale) | Reserved |

#### Production (63xx9)
| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 63138 | ntfy-api | Notification service (prod, Tailscale) | Reserved |
| 91319 | tickets-api | Ticket system API (prod, Tailscale) | Active |
| 93319 | tickets-mcp | Ticket system MCP (prod, Tailscale) | Active |
| 99319 | tickets-ui | Ticket system web UI (prod, Tailscale) | Active |

---

## MIGRATION FROM LEGACY PORTS (5000-5999)

**⚠️ NOTE:** Legacy port mappings updated to use corrected 4-digit scheme (61xxx/63xxx instead of invalid 5-digit scheme).

### Legacy Port Mapping

The following services need to migrate from legacy 5xxx ports to new 61xxx (dev) / 63xxx (prod) ports:

| Old Port | Service | New Dev Port | New Prod Port | Status |
|----------|---------|--------------|---------------|--------|
| 5311 | spi-manager API | 61115 | 63115 | ✅ Migrated |
| 5312 | spi-manager MCP | 61315 | 63315 | Pending |
| 5319 | spi-manager Web | 61915 | 63915 | Pending |
| 5330 | ntfy (notifications) | 61138 | 63138 | 🚧 In Progress |
| 5401 | tickets API | 61119 | 63119 | ✅ Migrated |
| 5402 | tickets MCP | 61319 | 63319 | Pending |
| 5549 | tickets Web | 61919 | 63919 | ✅ Migrated |
| 5509 | SCG | 61125 | 63125 | Pending |
| 5601 | SAG API | 61135 | 63135 | Pending |
| 5701 | SIG | 61145 | 63145 | Pending |
| 5008 | SSG API | 61155 | 63155 | Pending |
| 5801 | AIID API | 61127 | 63127 | Pending |
| 5809 | AIID WebSocket | 61727 | 63727 | Pending |
| 5819 | AIID UI | 61927 | 63927 | Pending |
| 5129 | C4S Dashboard | (archived) | - | Archive to backups |
| 5999 | Control Deck | 61910 | 63910 | Pending |
| 5344 | Llama Chat Model | 61614 | 63614 | In Progress |
| 5345 | Llama Reasoning Model | 61615 | 63615 | In Progress |
| 5346 | Llama Coding Model | 61616 | 63616 | In Progress |
| 5347 | Llama Vision Model | 61617 | 63617 | Reserved |
| 5011 | LocalAI Server | 61610 | 63610 | ✅ Migrated |

---

## PORT RESERVATION PROCESS

When reserving a new port for a service:

1. **Determine Environment:** Development (1), Testing (5), Acceptance (7), Production (9)
2. **Select Service Type:** API (1), MCP (3), Database (5), WebSocket (7), Web UI (9)
3. **Choose Network Scope:** LAN (1), Personal VPN (3), Group (5), Ext Non-Prod (7), Ext Prod (9)
4. **Assign Product Category:** Platform (0), Education (1), Organization (2), Public (3), Healthcare (4), AI (5), Media (6), Communication (7), Analytics (8), Utilities (9)
5. **Reserve in this file:** Add entry to relevant category table
6. **Update service_registry.yaml:** Add entry to /opt/bootstrap/TOOLS.md (service registry consolidated)
7. **Configure service:** Update service configuration files (.env, config.yaml, etc.)
8. **Update firewall:** Configure firewall rules if needed
9. **Test connectivity:** Verify port is accessible from intended scope
10. **Document:** Update service README.md with port information

---

## QUICK REFERENCE

**Development API:** 11XYZ (X = service type, Y = category, Z = instance)
**Development Web UI:** 19XYZ
**Production API (Internal):** 91XYZ (Tailscale/VPN)
**Production API (Public):** 91YXZ or 91ZXZ (depends on scope)
**Production Web UI (Internal):** 99XYZ (Tailscale)
**Production Web UI (Public):** 99YXZ or 99ZXZ

---

## NOTES

- **Port conflicts:** If a port is already in use, increment the last digit (xxxY0 → xxxY1)
- **Firewall:** All external production ports (9x9xx) require firewall configuration
- **SSL/TLS:** All public-facing ports (9x9xx) require SSL/TLS termination
- **Monitoring:** All production ports should be monitored for uptime
- **Documentation:** Always update this file when reserving new ports

---

**Last Updated:** 2025-12-31
**Maintained By:** SPI Platform Team
**Review Schedule:** Quarterly or when new services are added
