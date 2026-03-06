<!--
ts: 2025-12-31T13:20:05Z | git: <to-be-filled> | path: <relative-path>
-->

# Project Bootstrap – START

This file is the single entrypoint for starting a new project.

## Bootstrap File Index

All projects use these standard files:

### Core Documentation
- **README.md** - Project index and overview
- **START.md** - This file, bootstrap instructions
- **STATUS.md** - Current project status and progress
- **BACKLOG.md** - Prioritized work items (synced with /opt/tickets)
- **NEXT_SESSION.md** - Session continuation prompt (update at >50% context)

### Technical Documentation
- **ARCHITECTURE.md** - System design and technical decisions
- **DESIGN.md** - UI/UX specifications and guidelines
- **APIMCP.md** - API and MCP implementation details (if applicable)
- **VERSIONS.md** - Multi-environment version tracking and deployments, contains DTAP staging locations
- **TOOLS.md** - Available shared tools and resources (see /opt/bootstrap/TOOLS.md)

### Operations
- **DEPLOY.md** - Deployment procedures per environment (dev/staging/prod)
- **SECRETS.md** - Credential locations per environment
- **MIGRATION_CHECKLIST.md** - Verification checklist for migrations
- **PORTS.md** - Port allocation registry (if needed)
- **SSH_KEYS.md** - SSH key management per environment (if needed)

### Development
- **ticket.md** - Ticket template for /opt/tickets integration

## Bootstrap Steps

1. Copy all templates from /opt/bootstrap into project root.
2. Fill README.md first (project overview and file index).
3. Define STATUS, BACKLOG, ARCHITECTURE, DESIGN.
4. Initialize VERSIONS.md with development environment.
5. Setup dev/test environments.
6. Generate SSH keys per environment (acceptance, production).
7. Configure deployment (one-off by default).
8. IAM integration is OPTIONAL and deferred.

## Important Rules

- No agent may start work without reading this file. 
- Source of truth is always /opt/projects/<project-name> 
- Update VERSIONS.md after each 
deployment 
- All backlog items synced with /opt/tickets service
- Update documentation when you're over 50% context window and write the prompt for
the next session in NEXT_SESSION.md
- Commit to Github when this context window is reached (see SECRETS.md for GitHub PAT location)
- Only edit files in /opt/projects directly, never in /opt/tools or /opt/products unless specifically instructed to

## 🛠️ Tool Discovery (Zero Context Window Cost!)

**Discover available services programmatically:**

```bash
# Get all available services (10-20 tokens vs 2,000+ from docs)
curl http://localhost:63100/api/v1/services?env=prod

# Returns: service name, type (api/mcp/both), URLs, health status
# Only read detailed docs (/opt/projects/{service}/API.md) when you need them
```

**Service Discovery API:**
- Development: `http://localhost:61100/api/v1/services`
- Production: `http://localhost:63100/api/v1/services`
- Query params: `?env=dev|accept|prod` and `?health=true|false`
- Auto-scans `/opt/projects/*/APIMCP.md` for service metadata
- **100x context window savings** (lightweight JSON vs reading full docs)

### Core Documentation (Read As Needed)
- **`/opt/bootstrap/TOOLS.md`** - Shared resources guide (venv, SSL, backups)
- **`/opt/bootstrap/CODING_RULES.md`** - Mandatory coding standards
- **`/opt/bootstrap/APIMCP.md`** - API and MCP design patterns
- **`/opt/projects/spi-manager/API.md`** - AI models and GPU access (422+ models)

### Key Locations
- **Development:** `/opt/projects/<project-name>/` (READ/WRITE access, source of truth)
- **Acceptance:** `/opt/accept/<project-name>/` (read-only, deploy via scripts)
- **Production (tools):** `/opt/tools/<project-name>/` (shared tools, deploy via scripts)
- **Production (services):** `/opt/products/<project-name>/` (web services, deploy via scripts)
- **Shared resources:** `/opt/tools/venv/`, `/opt/tools/ssl/`, `/opt/models/` (organized by type, see TOOLS.md)
- **Characters:** `/opt/characters/{Name}_{ID}/` (centralized character data, see TOOLS.md)
- **Backups:** `/opt/backups/{project}_{timestamp}/` (code/text only, not media/models)
- **Credentials:** Project-specific in `/opt/projects/{projectname}/.env` (see SECRETS.md)

### Working in SSH Sessions (25-line limit)
- **Output visibility:** Last ≤25 lines only (limited scroll-back)
- **Summarize actions:** Always use last few lines for summary/next steps
- **Never run sudo:** Write exact command, ask user to run it
- **Commit AND push:** Always `git push` after commit (local = no backup)

### Documentation Rules
- **NEVER create new .md files** unless explicitly requested
- **Update existing bootstrap files:** README, STATUS, BACKLOG, ARCHITECTURE, etc.
- **Single intent per file:** Max ~15K tokens
- **Read as needed:** Don't read all docs upfront, lazy load when task requires

## 🤖 AI Model & GPU Access (For All Agents)

**All SPI services have access to centralized AI models and GPU resources via spi-manager.**

### Quick Reference:
- **API Documentation:** `/opt/projects/spi-manager/API.md` - Complete guide for agents
- **Available models:** 422+ models (OpenAI, Anthropic, Google, Venice, Mistral, Groq, local)
- **Development API:** http://localhost:61115
- **Production API:** http://localhost:63115
- **Interactive docs:** http://localhost:61115/docs (Swagger UI)

### Common Operations for Agents:

**Discover available models:**
```bash
GET http://localhost:61115/models
# Returns 422+ models with availability, cost, and capabilities
```

**Get LLM completion:**
```bash
POST http://localhost:61115/invoke
{
  "prompt": "Your prompt here",
  "agent_id": "your-service-name",  # REQUIRED for tracking
  "model": "auto"  # or specify: "claude-3-7-sonnet-20250219"
}
```

**Check GPU/VRAM availability:**
```bash
GET http://localhost:61115/gpu/status
# Returns: total_vram_gb, used_vram_gb, free_vram_gb, loaded_models
```

**Request VRAM for GPU workload:**
```bash
POST http://localhost:61115/gpu/allocate
{
  "requester": "your-service-name",
  "required_vram_gb": 10.0,
  "priority": 7  # 1-10: Video(9) > Image(7) > LLM(5)
}
# Workload-manager will evict idle models if needed
# Returns: allocation_id for cleanup later
```

**Release VRAM allocation:**
```bash
POST http://localhost:61115/gpu/release
{
  "allocation_id": "alloc_abc123",
  "restore_models": false
}
```

### Agent Requirements:
⚠️ **ALWAYS include `agent_id` in all requests** - Required for:
- Usage tracking and analytics
- Budget management per service
- Cost attribution
- Performance monitoring

### Full Documentation:
📚 **Complete API guide:** `/opt/projects/spi-manager/API.md`
🛠️ **All available tools:** `/opt/tools/INDEX.md`
📋 **Coding standards:** `/opt/CODERULES.md`
