<!--
ts: 2026-01-27T12:30:00Z | git: <to-be-filled> | path: /opt/bootstrap
-->

# {Project Name}

{Brief one-line description of what this project does}

## Project Overview

**Status:** {Bootstrap Complete | In Development | Testing | Production}
**Purpose:** {Detailed purpose and goals}
**Repository:** {GitHub URL}
**Development:** `/opt/projects/{name}` (source of truth)
**Production:** `/opt/tools/{name}` or `/opt/products/{name}`

## Documentation

- [START.md](START.md) - Project bootstrap instructions and file index
- [STATUS.md](STATUS.md) - Current project status and progress
- [BACKLOG.md](BACKLOG.md) - Prioritized work items and tasks
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture and design decisions
- [DESIGN.md](DESIGN.md) - UI/UX design specifications
- [DEPLOY.md](DEPLOY.md) - Deployment procedures and environments
- [SECRETS.md](SECRETS.md) - Secrets management and credential locations
- [VERSIONS.md](VERSIONS.md) - Multi-environment version tracking
- [APIMCP.md](APIMCP.md) - API and MCP implementation details (if applicable)

## Quick Start

{Instructions to get the project running locally}

**Prerequisites:**
- {List dependencies}
- {List required services}

**Installation:**
```bash
cd /opt/projects/{name}
# {Setup commands}
```

**Running:**
```bash
# {Run commands}
```

## Standards

**Language:**
- Code and documentation: English
- UI: Multilingual (Dutch default for uNiek Solutions projects)

**Coding Standards:**
- Follow `/opt/bootstrap/CODING_RULES.md`
- See project-specific CODING_RULES.md if exists (for exceptions only)

**Ticket Integration:**
- All work items tracked in `/opt/tickets` service
- BACKLOG.md synced with ticket service

---

## For MODIFYING existing services - MANDATORY:

### Migration Requirements

⚠️ **BEFORE making any changes:**
- Create backup of current working state using `/opt/tools/scripts/backup_snapshot.sh`
- Test migration path for existing data/users
- Verify backwards compatibility (existing features still work)
- Document rollback procedure if changes break functionality
- Update VERSIONS.md with migration notes

**Rule: If current functionality works, preserve it. Only extend, don't replace.**

### Pre-Modification Checklist

- [ ] Current state backed up to `/opt/backups/{project}_{timestamp}/`
- [ ] Migration tested on sample data (if data changes)
- [ ] Existing tests still pass (if test suite exists)
- [ ] New tests added for new functionality
- [ ] BACKLOG.md updated with migration task
- [ ] VERSIONS.md documents pre/post migration state
- [ ] Rollback procedure documented in DEPLOY.md

### Migration Process

1. **Backup first:** Always create backup before any changes
   ```bash
   /opt/tools/scripts/backup_snapshot.sh /opt/projects/{name}
   ```

2. **Test in development:** Verify changes work in `/opt/projects/{name}/`

3. **Deploy to acceptance:** Use deployment script
   ```bash
   ./scripts/deploy_dev_to_accept.sh
   ```

4. **Verify in acceptance:** Test all functionality in `/opt/accept/{name}/`

5. **Deploy to production:** Use deployment script (with validation)
   ```bash
   ./scripts/deploy_accept_to_prod.sh
   ```

6. **Monitor:** Watch for errors, check health endpoints

7. **Update documentation:** Update STATUS.md, VERSIONS.md, NEXT_SESSION.md

### Rollback If Issues

If production has issues after deployment:

```bash
# Restore from backup
cp -r /opt/backups/{project}_{timestamp}/* /opt/products/{name}/

# OR use rollback script if available
./scripts/rollback_production.sh {project}

# Restart services
systemctl restart {service-name}
```

---

## Development Workflow

### Starting Work

1. Read START.md (project overview)
2. Read STATUS.md (current state)
3. Check BACKLOG.md (what needs to be done)
4. Update NEXT_SESSION.md if starting new task

### During Work

1. Make frequent commits: `git add -A && git commit -m "message" && git push`
2. Update BACKLOG.md as tasks progress
3. Create backups before risky changes
4. Test in development before deploying

### Ending Session

1. Update STATUS.md (what's working now)
2. Update BACKLOG.md (remaining tasks)
3. Update NEXT_SESSION.md (context for next session)
4. Commit and push all changes
5. Note context window usage (update docs if >50%)

### Deployment

**Never deploy directly to production!** Use deployment scripts:

```bash
# Development → Acceptance
./scripts/deploy_dev_to_accept.sh

# Acceptance → Production (with validation)
./scripts/deploy_accept_to_prod.sh
```

---

## Project Structure

```
/opt/projects/{name}/
├── README.md                   # This file
├── START.md                    # Bootstrap entry point
├── STATUS.md                   # Current status
├── BACKLOG.md                  # Work items
├── ARCHITECTURE.md             # Technical design
├── DESIGN.md                   # UI/UX specs
├── DEPLOY.md                   # Deployment guide
├── SECRETS.md                  # Credential management
├── VERSIONS.md                 # Environment tracking
├── NEXT_SESSION.md             # Session continuation prompt
├── scripts/                    # Deployment and utility scripts
├── src/ or api/                # Source code
├── tests/                      # Test suite
├── .env                        # Local config (gitignored)
└── .gitignore                  # Excluded files
```

---

## Environment

### Development
- **Location:** `/opt/projects/{name}/`
- **Access:** Full read/write
- **Purpose:** Active development, testing

### Acceptance
- **Location:** `/opt/accept/{name}/`
- **Access:** Read-only (deploy via script)
- **Purpose:** Pre-production testing

### Production
- **Location:** `/opt/tools/{name}/` or `/opt/products/{name}/`
- **Access:** Read-only (deploy via script)
- **Purpose:** Live service

See VERSIONS.md for current versions and endpoints per environment.

---

## Support

**Issues:** Create ticket in `/opt/tickets` or GitHub issues
**Questions:** See project ARCHITECTURE.md or DESIGN.md
**Deployment:** Follow DEPLOY.md procedures
