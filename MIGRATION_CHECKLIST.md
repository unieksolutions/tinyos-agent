# MIGRATION CHECKLIST

Use this checklist when migrating/upgrading a project or service.

**CRITICAL:** Complete ALL items before claiming "migration complete"

## 1. Code Migration

- [ ] Files moved to new structure
- [ ] Import paths updated (grep old paths)
- [ ] Dependencies updated (package.json, requirements.txt, etc.)
- [ ] Old code removed or archived
- [ ] Git commit created with migration changes

## 2. Configuration

- [ ] .env files updated with new values
- [ ] /opt/bootstrap/TOOLS.md (service registry) updated
- [ ] Systemd unit files updated
- [ ] /opt/CODERULES.md references updated (if applicable)
- [ ] /opt/tools/INDEX.md updated (if applicable)
- [ ] Project VERSIONS.md updated
- [ ] Project SECRETS.md documents new credential locations
- [ ] Project DEPLOY.md has deployment procedures

## 3. Testing (MANDATORY - DO NOT SKIP)

### Service Health
- [ ] Service starts: `systemctl status <service>`
- [ ] No errors in startup logs: `journalctl -u <service> -n 50`
- [ ] Ports listening: `ss -tlnp | grep <port>`
- [ ] Process not crashing (check after 1 minute)

### Functional Testing
- [ ] Health endpoint responds: `curl <url>/health` or equivalent
- [ ] API endpoints functional (test 2-3 key endpoints)
- [ ] Database connections working
- [ ] Authentication working (if applicable)

### Integration Testing
- [ ] Dependent services can connect
- [ ] Integration tests pass (if they exist)
- [ ] User-facing functionality verified

## 4. Documentation

- [ ] README.md updated with migration notes
- [ ] API.md reflects new endpoints/changes
- [ ] VERSIONS.md shows migration (commit, date, deployer)
- [ ] BACKLOG.md migration item marked complete
- [ ] ARCHITECTURE.md updated (if structure changed)

## 5. Rollback Plan

- [ ] Backup created: `./backups/YYYY-MM-DDThh-mm/` or git tag
- [ ] Rollback procedure documented in DEPLOY.md
- [ ] Old configuration preserved (archived, not deleted)
- [ ] Tested rollback process (at least mentally walked through)

## 6. Per-Environment Verification

### Development
- [ ] Works on local machine
- [ ] .env file has correct values
- [ ] Can start/stop service manually

### Staging  
- [ ] Deployed to staging location
- [ ] .env.staging loaded correctly
- [ ] SSH access works
- [ ] Health check passes
- [ ] Manual testing completed

### Production
- [ ] Credentials in vault verified
- [ ] Deployment procedure tested on staging
- [ ] Monitoring configured
- [ ] Rollback plan ready
- [ ] Approval obtained (if required)

## Common Mistakes to Avoid

❌ **Claiming "complete" after code changes only**
✅ **Verify service actually starts and works**

❌ **Assuming old ports/paths still work**
✅ **Test actual endpoints with curl/API calls**

❌ **Skipping documentation updates**  
✅ **Update all 3: VERSIONS.md, SECRETS.md, DEPLOY.md**

❌ **No rollback plan**
✅ **Always create backup before migration**

❌ **Not testing across environments**
✅ **Verify dev, staging, and production procedures**

## Sign-Off

Migration completed by: _________________
Date: _________________
Verified by: _________________ (optional, for production)

**All items above checked?** ✅ Then migration is complete.
**Any unchecked items?** ❌ Migration is NOT complete - continue work.
