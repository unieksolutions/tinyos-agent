<!--
ts: 2026-01-27T12:30:00Z | git: <to-be-filled> | path: /opt/bootstrap
-->

# SPI Tools & Shared Resources

## Service Discovery (Use This First!)

**Instead of reading this entire file, query the Service Discovery API:**

```bash
# Get all available services (lightweight JSON, ~10-20 tokens)
curl http://localhost:63100/api/v1/services?env=prod

# Returns:
# - Service name, type (api/mcp/both), URLs
# - Health status (optional: ?health=true)
# - Real-time, auto-discovered from /opt/projects/*/APIMCP.md
```

**Endpoints:**
- Development: `http://localhost:61100/api/v1/services`
- Production: `http://localhost:63100/api/v1/services`

**Why Use Service Discovery:**
- **100x context window savings** (vs reading this 200+ line file)
- Always up-to-date (scans APIMCP.md files automatically)
- Programmatic access (JSON response)
- Only read detailed docs when you need specific service

**When to Read This File:**
- Understanding shared resources (venv, SSL, backups)
- Learning about non-service resources (models, scripts)

---

## Overview

This document describes shared resources and infrastructure (not services - use Service Discovery for services).

## Shared Resources

### Python Virtual Environment

**Generic (shared):** ✅ EXISTS
- **Location:** `/opt/tools/venv/`
- **Purpose:** Shared Python packages for multiple projects
- **Usage:** `source /opt/tools/venv/bin/activate`
- **Status:** Active and in use by system services

**Project-specific (isolated):**
- **Location:** `/opt/projects/{name}/venv/`
- **Purpose:** Project-isolated dependencies
- **Usage:** `source ./venv/bin/activate`

**When to use which:**
- Shared: Development tools, common libraries (requests, flask, etc.)
- Project-specific: Project has unique versions or conflicts with shared venv

### SSL Certificates

**Generic (development):** ✅ READY
- **Location:** `/opt/tools/ssl/`
- **Purpose:** Self-signed certs for local HTTPS testing
- **Files:** Place `cert.pem`, `key.pem` here (not yet populated)
- **Created:** 2026-01-27 (directory ready for use)

**Project-specific:**
- **Location:** `/opt/projects/{name}/ssl/`
- **Purpose:** Project needs custom certificates

**Production:**
- Managed per environment (see SECRETS.md in each project)
- Never commit certificates to git

### Utility Scripts

**Location:** `/opt/projects/coding/scripts/` ✅ ACTIVE
- **smart_backup.sh** - Smart backup with compression + deduplication
- **scan_references.sh** - Find outdated path/port references
- **fix_references.sh** - Auto-fix outdated references
- **sync_bootstrap_to_projects.sh** - Sync template changes to all projects
- **cleanup_backups.sh** - Remove old/redundant backups
- **find_duplicates.sh** - Find duplicate files across /opt

### AI Models

**Location:** `/opt/models/` (organized by type)
- **`llm/gguf/`** - Quantized LLMs (Llama, Mistral, Phi, DeepSeek, Qwen, etc.)
- **`llm/hf/`** - HuggingFace LLM model directories
- **`vision/hf/`** - Vision-Language models (Qwen-VL, etc.)
- **`checkpoints/`** - Diffusion base models (SDXL, FLUX, WAN, Qwen Image Edit)
- **`loras/`** - LoRA fine-tuned adapters (character, style, pose)
- **`diffusion_models/`** - UNet/DiT weights
- **`text_encoders/`** - CLIP, T5, UMT5 encoders
- **`vae/`** - VAE models
- **`audio/`** - TTS/voice models (EmotiVoice, XTTS)
- **`utility/`** - Embedding models, face detection, pose estimation
- **`ollama/`** - Ollama model blobs
- Backward-compatible symlinks at root for all moved files

### Characters

**Location:** `/opt/characters/`
- **`{Name}_{6hexID}/`** - Per-character directory with reference images, datasets, LoRAs, output
- **`templates/`** - Shared assets: `clothing/`, `poses/`, `scenes/`, `backgrounds/`
- **`_archive/`** - Archived/test characters

**Access:** Always via API, never direct file access
- **SPI Manager API:**
  - Development: `https://localhost:61115`
  - Production: `https://localhost:63115`
  - Documentation: `/opt/projects/spi-manager/API.md`
  - Features: 422+ models, GPU/VRAM management, prompt enhancement

**Image Generation:**
- **ComfyUI API:** Evolving to generic 'model request' system
  - Development: Port 61XXX (see project PORTS.md)
  - Production: Port 63XXX (see project PORTS.md)

---

## Services (Use Service Discovery API)

**For service endpoints and availability, use the Service Discovery API instead:**

```bash
curl http://localhost:63100/api/v1/services?env=prod
```

**Common services include:**
- SPI Manager - AI/LLM access (422+ models)
- Tickets - Task tracking and backlog management
- Neo4j - Graph database
- ChromaDB - Vector database
- Memory - Unified Chroma + Neo4j API

**For detailed API docs:** Read `/opt/projects/{service}/API.md` only when needed

### Screenshots

**Location:** `/opt/screenshots/`

**Purpose:** Screenshots shared from laptop to agents for visual context

**Access:** Read-only for agents

**Usage:** Agent reads screenshot files to understand UI/UX issues

### Backups

**Location:** `/opt/backups/{project}_{timestamp}/`

**Format:** `{project}_YYYY-MM-DDTHH-MM/`

**Examples:**
- `/opt/backups/coding_2026-01-27T12-25/`
- `/opt/backups/spi-manager_2026-01-26T15-30/`

**Includes:** Code, text files, configuration (compressed in tar.gz)
**Excludes:** `.git`, `__pycache__`, `node_modules`, `venv` (auto-excluded)
**Deduplication:** Large files (>20MB) hardlinked from previous backups

**Script:** `/opt/projects/coding/scripts/smart_backup.sh <path> [description]`

---

## Utility Scripts

### Smart Backup Script (RECOMMENDED)

**Path:** `/opt/projects/coding/scripts/smart_backup.sh` ✅ ACTIVE

**Usage:**
```bash
bash /opt/projects/coding/scripts/smart_backup.sh /opt/projects/myproject "description"
```

**Features:**
- ✅ **Compression:** Creates tar.gz (saves space)
- ✅ **Deduplication:** Hardlinks large files (>20MB) from previous backups
- ✅ **Metadata:** Stores git hash, timestamp, file list
- ✅ **Space efficient:** Only stores changed files, deduplicates unchanged large files

**Output:**
- Backup directory: `/opt/backups/YYYY-MM-DDTHH-MM_{project}_{description}/`
- Contains: `backup.tar.gz`, `.backup_metadata`, hardlinked large files

**Example:**
```bash
# Before making changes
bash /opt/projects/coding/scripts/smart_backup.sh /opt/projects/aiid "before_refactor"

# Shows: Deduplicated 15 files, saved 2.3GB
```

### Legacy Backup Script (DEPRECATED)

**Path:** `/opt/tools/scripts/backup_snapshot.sh` ⚠️ DEPRECATED

Use `smart_backup.sh` instead for compression and deduplication.

### Deployment Scripts

**Location:** Per-project in `/opt/projects/{name}/scripts/`

**Standard scripts:**
- `deploy_dev_to_accept.sh` - Deploy to acceptance with validation
- `deploy_accept_to_prod.sh` - Deploy to production (strict checks)
- `deploy_prod_to_accept.sh` - Reverse flow for investigation
- `deploy_prod_to_dev.sh` - Emergency hotfix flow

**See:** DEPLOY.md in each project for detailed procedures

---

## Active Services Registry (DEPRECATED)

**⚠️ This section is DEPRECATED. Use Service Discovery API instead:**

```bash
# Get real-time service list with health checks
curl http://localhost:63100/api/v1/services?env=prod&health=true
```

**Why Service Discovery API is better:**
- Always up-to-date (auto-scans APIMCP.md files)
- No manual maintenance needed
- Includes health status
- Supports filtering by environment (dev/accept/prod)
- Lightweight JSON response (~500 bytes)

---

## Development Tools

### CLI Coding Tool

**Location:** `/opt/tools/coding/`

**Purpose:** Interactive menu for launching AI coding agents (Claude, Codex, Gemini, OpenCode)

**Features:**
- Tmux session management
- Project directory switching
- Ticket integration
- Bootstrap workflow support

**Usage:** Run `coding` from any directory

### Database Tools

**Neo4j (Graph Database):**
- Endpoint: `bolt://localhost:5216`
- Web UI: `http://localhost:5217`
- Credentials: See `/opt/tools/.env` or project `.env`

**ChromaDB (Vector Database):**
- Endpoint: `http://localhost:5206`
- Purpose: Embeddings, semantic search, RAG
- Collections: Per-project namespaces

---

## Configuration Files

### Shared Configuration

**Location:** `/opt/tools/.env` (if needed for shared services)

**Contains:**
- Neo4j credentials
- SPI Manager API keys
- Shared service tokens

**Note:** Project-specific credentials go in project `.env` files

### Per-Project Configuration

**Location:** `/opt/projects/{name}/.env`

**Standard variables:**
```bash
GITHUB_PAT=<token>              # For git operations
DATABASE_URL=<connection>        # Database connection
API_KEY=<key>                   # External API keys
MODEL_ROUTER_URL=<url>          # Model router endpoint
```

**Security:**
- Always add `.env` to `.gitignore`
- Never commit credentials to git
- See SECRETS.md for credential management

---

## Notes

- **Source of truth:** Always `/opt/projects/{name}/` for development
- **Deployment flow:** dev → accept → production (via scripts only)
- **Shared vs project-specific:** Default to project-specific unless truly shared
- **Model files:** Large files (>100MB) stay in `/opt/models/` (organized by type), accessed via API
- **Character data:** All character assets in `/opt/characters/{Name}_{ID}/` (reference, dataset, LoRA, output)
