<!--
ts: 2026-01-29T13:00:00Z | git: <to-be-filled> | path: <relative-path>
-->
# DEPLOY

Deployment procedures and environment configuration.

**⚠️ CRITICAL: Choose the correct deployment type for your project below.**

---

## Deployment Types

This project uses one of three deployment types. Identify your type and follow the corresponding procedures:

### Type A: SPI-Hosted Services
**Deployment Flow:** `/opt/projects/{name}` → `/opt/accept/{name}` → `/opt/products/{name}`
**Examples:** tickets, spi-manager, chromadb, aiid
**Hosting:** Services run on SPI server itself
**Access:** localhost, LAN, or Tailscale VPN

### Type B: External Webhosting
**Deployment Flow:** `/opt/projects/{name}` → `accept.domain.tld` → `domain.tld`
**Examples:** sis (schoolinfoscherm.nl), public websites
**Hosting:** Shared hosting (A2, TransIP, etc.) or managed webhosting
**Access:** Public internet via domain names

### Type C: VPS/Cloud Hosted
**Deployment Flow:** `/opt/projects/{name}` → VPS staging → VPS production
**Examples:** Scalable services, containerized apps
**Hosting:** DigitalOcean, AWS, Azure, custom VPS
**Access:** Public internet or VPN-protected

---

## TYPE A: SPI-Hosted Services

### Environments

#### Development
**Location:** `/opt/projects/<project-name>`
**Purpose:** Active development, testing
**Port Range:** 61xxx (see PORTS.md)
**Access:** Direct filesystem access on SPI

**Start service:**
```bash
cd /opt/projects/<project-name>
source .env  # Load development credentials
<start-command>
```

#### Acceptance
**Location:** `/opt/accept/<project-name>`
**Purpose:** Pre-production testing, QA
**Port Range:** 64xxx (see PORTS.md)
**Access:** Tailscale VPN or LAN

**Deploy to acceptance:**
```bash
# 1. Backup current version
/opt/tools/scripts/backup_snapshot.sh /opt/accept/<project-name>

# 2. Sync from development
rsync -av --delete \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '*.md' \
  --exclude 'SECRETS.md' \
  --exclude '*_test*' \
  --exclude '*_temp*' \
  /opt/projects/<project-name>/ \
  /opt/accept/<project-name>/

# 3. Copy acceptance credentials
cp /opt/accept/<project-name>/.env.accept \
   /opt/accept/<project-name>/.env

# 4. Restart service
systemctl restart <project>-accept
```

#### Production
**Location:** `/opt/products/<project-name>` OR `/opt/tools/<project-name>`
**Purpose:** Live service
**Port Range:** 63xxx (see PORTS.md)
**Access:** Tailscale VPN (internal) or configured public access

**Deploy to production:**
```bash
# 1. MANDATORY: Backup current version
/opt/tools/scripts/backup_snapshot.sh /opt/products/<project-name>

# 2. Sync from acceptance (NEVER from development!)
rsync -av --delete \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '*.md' \
  /opt/accept/<project-name>/ \
  /opt/products/<project-name>/

# 3. Copy production credentials
cp /opt/products/<project-name>/.env.production \
   /opt/products/<project-name>/.env

# 4. Run migrations if needed
cd /opt/products/<project-name>
<migration-command>

# 5. Restart service
systemctl restart <project>-prod

# 6. Verify deployment
curl http://localhost:<prod-port>/health
```

---

## TYPE B: External Webhosting

### Environments

#### Development
**Location:** `/opt/projects/<project-name>`
**Purpose:** Active development, testing
**Access:** Local SPI filesystem

**Start local development:**
```bash
cd /opt/projects/<project-name>
source .env  # Load development credentials
<start-command>  # e.g., php -S localhost:8000
```

#### Acceptance (Webhosting)
**Location:** `accept.domain.tld` (remote webhost)
**Purpose:** Pre-production testing, client review
**Access:** Public URL (accept.domain.tld)

**Deploy to acceptance webhosting:**
```bash
cd /opt/projects/<project-name>

# 1. Verify credentials are loaded
source /opt/tools/.env

# 2. Deploy using deployment script
/opt/tools/scripts/deploy_to_webhost.sh \
  /opt/projects/<project-name> \
  accept.domain.tld

# OR manual rsync:
rsync -avz --delete \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '*.md' \
  --exclude 'node_modules' \
  -e "sshpass -p \"$WEBHOST_SSH_PASSWORD\" ssh -p $WEBHOST_SSH_PORT -o StrictHostKeyChecking=no" \
  ./ \
  $WEBHOST_SSH_USER@$WEBHOST_SSH_HOST:~/accept.domain.tld/
```

**Run database migrations on acceptance:**
```bash
source /opt/tools/.env

# SSH to webhost and run migration
sshpass -p "$WEBHOST_SSH_PASSWORD" ssh \
  -p $WEBHOST_SSH_PORT \
  -o StrictHostKeyChecking=no \
  $WEBHOST_SSH_USER@$WEBHOST_SSH_HOST \
  "cd ~/accept.domain.tld && php migrations/run_migration.php"
```

#### Production (Webhosting)
**Location:** `domain.tld` (remote webhost)
**Purpose:** Live public service
**Access:** Public URL (domain.tld)

**Deploy to production webhosting:**
```bash
cd /opt/projects/<project-name>

# 1. MANDATORY: Create backup
/opt/tools/scripts/backup_snapshot.sh /opt/projects/<project-name>

# 2. Verify credentials
source /opt/tools/.env

# 3. Deploy using deployment script
/opt/tools/scripts/deploy_to_webhost.sh \
  /opt/projects/<project-name> \
  domain.tld

# 4. Run migrations if needed
sshpass -p "$WEBHOST_SSH_PASSWORD" ssh \
  -p $WEBHOST_SSH_PORT \
  -o StrictHostKeyChecking=no \
  $WEBHOST_SSH_USER@$WEBHOST_SSH_HOST \
  "cd ~/domain.tld && php migrations/run_migration.php"

# 5. Verify deployment
curl https://domain.tld/VERSION
```

**⚠️ CRITICAL for Type B:**
- `.md` files are project docs - NEVER deploy to webhosting
- Update `.gitignore` and rsync `--exclude` to prevent deployment
- Always test on acceptance before production deployment
- Keep webhost credentials in `/opt/tools/.env`

---

## TYPE C: VPS/Cloud Hosted

### Environments

#### Development
**Location:** `/opt/projects/<project-name>`
**Purpose:** Active development, testing
**Access:** Local SPI filesystem

**Start local development:**
```bash
cd /opt/projects/<project-name>
docker-compose up -d  # If using Docker
# OR
source .env && <start-command>
```

#### Staging (VPS)
**Location:** Remote VPS (staging instance)
**Purpose:** Pre-production testing
**Access:** SSH to staging VPS or Kubernetes staging namespace

**Deploy to VPS staging:**
```bash
# Docker-based deployment:
cd /opt/projects/<project-name>

# 1. Build image
docker build -t <project>:staging .

# 2. Push to registry
docker push registry.example.com/<project>:staging

# 3. Deploy to VPS
ssh <project>-staging "cd /opt/services/<project> && docker-compose pull && docker-compose up -d"

# OR Kubernetes:
kubectl apply -f k8s/staging/ --namespace=<project>-staging
```

#### Production (VPS)
**Location:** Remote VPS (production instance)
**Purpose:** Live service
**Access:** SSH to production VPS (via bastion) or Kubernetes prod namespace

**Deploy to VPS production:**
```bash
# 1. MANDATORY: Backup and verify staging
ssh <project>-staging "docker exec <container> /backup.sh"

# 2. Tag production image
docker tag <project>:staging <project>:production
docker push registry.example.com/<project>:production

# 3. Deploy via SSH (traditional)
ssh -J bastion <project>-prod \
  "cd /opt/services/<project> && \
   docker-compose pull && \
   docker-compose up -d"

# OR Kubernetes:
kubectl apply -f k8s/production/ --namespace=<project>-prod
kubectl rollout status deployment/<project> -n <project>-prod
```

---

## Deployment Checklist

### Pre-Deployment (All Types)
- [ ] Code reviewed and approved
- [ ] Tests passing (manual or CI/CD)
- [ ] VERSIONS.md updated with new version
- [ ] BACKLOG.md checked for migration tasks
- [ ] **Backup created** (MANDATORY)
- [ ] Rollback procedure documented
- [ ] Credentials verified (see SECRETS.md)

### Type A Specific
- [ ] Port conflicts checked (see PORTS.md)
- [ ] Systemd service files updated if needed
- [ ] Firewall rules configured for new ports

### Type B Specific
- [ ] `.md` files excluded from deployment
- [ ] Webhost credentials available in `/opt/tools/.env`
- [ ] Database migrations tested on acceptance first
- [ ] SSL certificates valid on webhost

### Type C Specific
- [ ] Docker images built and pushed
- [ ] Environment variables configured on VPS
- [ ] Health checks configured
- [ ] Load balancer/ingress configured

### Post-Deployment (All Types)
- [ ] Health check passing
- [ ] Logs monitored for errors
- [ ] Critical functionality tested
- [ ] VERSIONS.md updated with deployment timestamp
- [ ] STATUS.md updated if significant changes

---

## Rollback Procedures

### Type A: SPI-Hosted
```bash
# Restore from backup
/opt/tools/scripts/restore_snapshot.sh \
  /opt/backups/<timestamp>/ \
  /opt/products/<project-name>/

systemctl restart <project>-prod
```

### Type B: External Webhosting
```bash
# Re-deploy previous version from git
cd /opt/projects/<project-name>
git checkout <previous-commit>

/opt/tools/scripts/deploy_to_webhost.sh \
  /opt/projects/<project-name> \
  domain.tld

# Rollback database if needed
sshpass -p "$WEBHOST_SSH_PASSWORD" ssh \
  -p $WEBHOST_SSH_PORT \
  $WEBHOST_SSH_USER@$WEBHOST_SSH_HOST \
  "cd ~/domain.tld && mysql < backups/rollback.sql"
```

### Type C: VPS/Cloud
```bash
# Docker: Roll back to previous image
ssh <project>-prod \
  "cd /opt/services/<project> && \
   docker-compose down && \
   docker pull registry.example.com/<project>:<previous-tag> && \
   docker-compose up -d"

# Kubernetes: Roll back deployment
kubectl rollout undo deployment/<project> -n <project>-prod
```

---

## Emergency Contacts

**Critical Production Issues:**
- On-call: [Contact info]
- Escalation: [Contact info]

**Webhost Support:**
- Provider: [e.g., A2 Hosting, TransIP]
- Support URL: [URL]
- Account: [Account details in SECRETS.md]

**VPS/Cloud Support:**
- Provider: [e.g., DigitalOcean, AWS]
- Support URL: [URL]
- Account: [Account details in SECRETS.md]

---

## Related Documentation

- **SECRETS.md** - Credential management and locations
- **VERSIONS.md** - Multi-environment version tracking
- **PORTS.md** - Port allocations (Type A only)
- **ARCHITECTURE.md** - Technical architecture and dependencies
- **/opt/bootstrap/PORTS.md** - Global port allocation scheme (Type A)
- **/opt/tools/scripts/** - Deployment helper scripts

---

**Last Updated:** 2026-01-29
**Template Version:** 2.0 (Multi-deployment type support)
