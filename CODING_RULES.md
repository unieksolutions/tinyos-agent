# CODING RULES - SPI Development Standards

Essential coding standards for all SPI development work.

## Essential Rules

### Output & Communication
- **One-line steps:** Maximum 10 words per step
- **Multi-line blocks:** Only for scripts/config, note context clearly
- **SSH sessions:** Keep responses ≤25 lines (limited scroll-back)
- **Exact commands:** Use absolute paths, concrete commands
- **Ask questions:** When >50% unclear about requirements

### Git Workflow
- **Commit regularly:** After each logical change
- **ALWAYS push:** `git push` after every commit (backup protection)
- **Update README:** With every commit
- **PAT location:** `/opt/tools/.env` for github.com/unieksolutions/*
- **Commit messages:** Clear, concise, explain WHY not just WHAT

### Backups
- **Before modifying:** Create snapshot in `/opt/backups/{project}_{datetime}/`
- **Backup tool:** `/opt/projects/scripts/backup_snapshot.sh <path>`
- **Timestamp format:** Canonical NL (YYYY-MM-DDThh-mm)
- **Include metadata:** `.backup_info` with git hash, repo URL, source path

### Command Execution
- **NEVER sudo:** CLI agents hang with sudo commands
- **When sudo needed:** Write exact command, ask user to run it, wait for output
- **Do yourself:** Don't ask user to run what agent can execute
- **Port scanning:** ALWAYS scan before starting new services

### External Resources
- **SPI Manager:** Use https://localhost:5311 (include `agent_id` or `service_id`)
- **Shared config:** `/opt/tools/.env` for credentials
- **Virtual env:** `/opt/tools/venv` for Python (check existing packages first)
- **PHP CLI:** Installed system-wide for linting/tests
- **SSL certs:** `/opt/tools/ssl/` (see README.md for framework setup)

### Development Environment
- **Source of truth:** `/opt/projects/{project}` (development)
- **Acceptance:** `/opt/accept/{project}` (staging)
- **Production:** `/opt/tools/{project}` or `/opt/products/{project}`
- **Deploy via scripts:** Never write directly to accept/production

### Deployment Security (CRITICAL)
- **NO .md files in deployment:** Project docs stay in /opt/projects ONLY
  - Exclude: `--exclude '*.md'` in rsync
  - Exception: User-facing docs (user guides, help pages)
- **SECRETS.md with real secrets:** MUST be .gitignored
  - Template SECRETS.md (no real values) → OK to commit
  - Actual SECRETS.md (real values) → .gitignore required

### Web Development
- **Default:** Responsive web interfaces
- **Design system:** Follow `/opt/bootstrap/DESIGN.md`
- **Multilingual:** Support NL as default (see DESIGN.md)
- **Accessibility:** WCAG 2.1 AA minimum

### Testing
- **Before deployment:** Test in development environment
- **Migration testing:** Test with existing data/users
- **Rollback plan:** Document in DEPLOY.md before deploying

### Temporary Files & Cleanup
- **Naming convention:** Use `_test` or `_temp` suffix for temporary files
  - Examples: `config_test.yaml`, `backup_temp.sql`, `output_test.txt`
- **After testing:** Either move to `/opt/backups/` OR delete completely
- **Never leave behind:** Clean up temp files before finishing work
- **Pattern to find:** `find . -name "*_test*" -o -name "*_temp*"`
- **Session end:** Remove ALL temporary files created during session

### Documentation
- **Bootstrap structure:** Use templates from `/opt/bootstrap/`
- **File limit:** ~15K tokens per file
- **Don't create new:** Update existing bootstrap docs
- **Reference details:** Link to specific sections, don't duplicate

## Key References

For detailed information, see:
- **Shared tools:** `/opt/bootstrap/TOOLS.md`
- **API/MCP patterns:** `/opt/bootstrap/APIMCP.md`
- **Port allocation:** `/opt/bootstrap/PORTS.md`
- **Deployment workflows:** `/opt/bootstrap/DEPLOY.md`
- **Design/UX:** `/opt/bootstrap/DESIGN.md`
- **SPI Manager API:** `/opt/projects/spi-manager/API.md`
- **Project bootstrap:** `/opt/bootstrap/START.md`

## Quick Commands

```bash
# Create backup
/opt/tools/scripts/backup_snapshot.sh /opt/projects/myproject

# Scan ports
ss -tlnp | grep :61

# Check service status
systemctl status myservice

# Git workflow
git add -A && git commit -m "message" && git push

# Model router health (dev)
curl -k https://localhost:61115/healthz

# Model router health (prod)
curl -k https://localhost:63115/healthz
```

## Common Mistakes to Avoid

❌ Running sudo in CLI agents (hangs)
❌ Running systemctl in CLI agents (not allowed)
❌ Forgetting to push after commit (no backup)
❌ Starting service without scanning ports (conflicts)
❌ Writing to /opt/accept or /opt/products directly (use deploy scripts)
❌ Creating new .md files (update existing bootstrap docs)
❌ Hardcoding credentials (use /opt/{stage}/{projectname}/.env or SECRETS.md)
❌ Single environment database (split dev/staging/prod)
❌ Skipping migration testing (breaks existing data)

---

**Last Updated:** 2026-01-08
**Maintained by:** SPI Development Team

---

## Feature Flags - MANDATORY for Production Services

**CRITICAL:** All services deployed to `/opt/products/` MUST implement feature flags.

### Why This Is Mandatory

Feature flags enable:
- Automated testing with features enabled/disabled
- Safe deployments (rollback without code changes)
- A/B testing and gradual rollouts
- Emergency killswitch for broken features

### Minimum Implementation

Every production service MUST have:

1. **config/feature_flags.yaml** - Feature flag definitions
2. **Feature flag library** - Code to check flags (see ARCHITECTURE.md)
3. **Admin API** - Endpoints to view/toggle flags
4. **Tests** - Use feature flag overrides in tests

### Example Structure

```
/opt/products/myservice/
├── config/
│   └── feature_flags.yaml        # ← REQUIRED
├── utils/
│   └── feature_flags.py          # ← REQUIRED
├── api/
│   └── admin_features.py         # ← REQUIRED (admin endpoints)
└── tests/
    └── test_features.py          # ← REQUIRED (flag tests)
```

### Deployment Validation

Before `deploy_accept_to_prod.sh`:
- Script CHECKS for `config/feature_flags.yaml`
- Script FAILS if feature flags not implemented
- Script VERIFIES admin API responds

### Non-Compliance

Services without feature flags:
- ❌ Cannot deploy to `/opt/products/`
- ❌ Cannot pass acceptance testing
- ❌ Blocked by deployment scripts

See `/opt/bootstrap/ARCHITECTURE.md` for full implementation guide.

