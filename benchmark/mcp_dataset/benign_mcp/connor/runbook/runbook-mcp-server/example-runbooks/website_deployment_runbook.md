# Website Deployment Runbook

## Overview
This runbook outlines the standard procedures for deploying website updates to production environments. It covers code pull, dependency installation, testing, and web server restart procedures. All deployments should follow this standardized process to ensure consistency and reliability.

## Prerequisites
- Access to production server with deployment privileges
- Code changes reviewed and approved
- Deployment window scheduled (if required)
- Backup of current production state completed
- Monitoring team notified
- Rollback plan prepared

## Safety Checks (Pre-Deployment)

### 1.1 Verify Deployment Readiness
```bash
# Check current system status
uptime
free -h
df -h

# Verify backup completion
ls -la /backups/website/
```

### 1.2 Check Environment Variables
```bash
# Verify required environment variables
echo $NODE_ENV
echo $DATABASE_URL
echo $API_KEY
```

### 1.3 Validate Configuration Files
```bash
# Check configuration files exist
ls -la config/
cat config/production.json
```

### 1.4 Notify Stakeholders
- Send deployment notification to team channel
- Update deployment tracker
- Set monitoring to "maintenance mode"

## Section 1: Code Pull and Preparation

### 1.1 Navigate to Deployment Directory
```bash
cd /var/www/website
```

### 1.2 Create Backup of Current Version
```bash
# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp -r /var/www/website /backups/website_backup_$TIMESTAMP
```

### 1.3 Pull Latest Code Changes
```bash
# For Git repositories
git fetch origin
git checkout main
git pull origin main

# Verify the commit hash
git log --oneline -1
```

### 1.4 Check for Uncommitted Changes
```bash
git status
# Should show "nothing to commit, working tree clean"
```

### 1.5 Verify Pulled Changes
```bash
# Show what changed
git log --oneline --graph -10

# Check specific files if needed
git diff HEAD~1 HEAD -- config/
```

## Section 2: Dependency Installation

### 2.1 Node.js Projects
```bash
# Install dependencies
npm ci --only=production

# Verify installation
npm list --depth=0
```

### 2.2 Python Projects
```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### 2.3 PHP Projects
```bash
# Install dependencies with Composer
composer install --no-dev --optimize-autoloader

# Verify installation
composer show
```

### 2.4 Ruby Projects
```bash
# Install dependencies with Bundler
bundle install --without development test

# Verify installation
bundle list
```

### 2.5 Verify Dependency Integrity
```bash
# Check for security vulnerabilities
npm audit --production
# OR
safety check -r requirements.txt
# OR
bundle audit
```

## Section 3: Testing Procedures

### 3.1 Unit Tests
```bash
# Run unit tests
npm test -- --passWithNoTests
# OR
python -m pytest tests/unit/
# OR
phpunit --testsuite unit
```

### 3.2 Integration Tests
```bash
# Run integration tests
npm run test:integration
# OR
python -m pytest tests/integration/
```

### 3.3 Smoke Tests
```bash
# Quick smoke test script
./scripts/smoke_test.sh

# Verify basic functionality
curl -f http://localhost:3000/health
```

### 3.4 Database Migration Tests
```bash
# Test database migrations (dry run)
npm run migrate:test
# OR
python manage.py migrate --plan
```

### 3.5 Security Scans
```bash
# Run security checks
npm run security:scan
# OR
./scripts/security_check.sh
```

## Section 4: Build and Compilation

### 4.1 Frontend Build (if applicable)
```bash
# Build frontend assets
npm run build

# Verify build output
ls -la dist/
```

### 4.2 Backend Compilation
```bash
# For TypeScript/compiled languages
npm run build:server
# OR
tsc --project tsconfig.prod.json
```

### 4.3 Asset Optimization
```bash
# Optimize images and assets
npm run optimize:assets
```

### 4.4 Cache Busting
```bash
# Generate cache-busting hashes
npm run generate:hashes
```

## Section 5: Web Server Restart Procedures

### 5.1 Graceful Restart Order

#### 5.1.1 Nginx Configuration
```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx (graceful)
sudo systemctl reload nginx
# OR restart if needed
sudo systemctl restart nginx
```

#### 5.1.2 Apache Configuration
```bash
# Test Apache configuration
sudo apachectl configtest

# Graceful restart
sudo systemctl reload apache2
# OR
sudo apachectl graceful
```

#### 5.1.3 Application Server Restart
**Node.js with PM2:**
```bash
# Reload application
pm2 reload website

# Check status
pm2 status website
```

**Python with Gunicorn:**
```bash
# Restart Gunicorn
sudo systemctl restart gunicorn

# Check status
sudo systemctl status gunicorn
```

**PHP with PHP-FPM:**
```bash
# Restart PHP-FPM
sudo systemctl restart php-fpm

# Check status
sudo systemctl status php-fpm
```

### 5.2 Verify Service Health
```bash
# Check all services
systemctl status nginx
systemctl status gunicorn
systemctl status php-fpm

# Verify ports are listening
netstat -tulpn | grep -E ':80|:443|:3000'
```

## Section 6: Post-Deployment Verification

### 6.1 Health Checks
```bash
# Application health endpoint
curl -f http://localhost:3000/health

# Database connectivity
curl -f http://localhost:3000/api/health/db

# External service connectivity
curl -f http://localhost:3000/api/health/external
```

### 6.2 Functional Testing
```bash
# Run post-deployment tests
./scripts/post_deploy_test.sh

# Test critical user journeys
./scripts/test_critical_paths.sh
```

### 6.3 Performance Checks
```bash
# Quick performance test
ab -n 100 -c 10 http://localhost:3000/

# Check response times
curl -o /dev/null -s -w "Total: %{time_total}s\n" http://localhost:3000/
```

### 6.4 Log Monitoring
```bash
# Check for errors in logs
tail -50 /var/log/nginx/error.log
tail -50 /var/log/website/application.log

# Monitor real-time logs
tail -f /var/log/website/application.log | grep -i error
```

## Section 7: Rollback Procedures

### 7.1 When to Rollback
- Critical errors in application logs
- Health checks failing consistently
- Performance degradation > 50%
- User reports of broken functionality

### 7.2 Quick Rollback Steps
```bash
# Stop current deployment
pm2 stop website
# OR
sudo systemctl stop gunicorn

# Restore from backup
cd /var/www
rm -rf website
cp -r /backups/website_backup_$TIMESTAMP website

# Restart services
pm2 start website
# OR
sudo systemctl start gunicorn
```

### 7.3 Database Rollback
```bash
# If migrations need to be rolled back
npm run migrate:down
# OR
python manage.py migrate app_name previous_migration
```

## Section 8: Monitoring and Alerting

### 8.1 Post-Deployment Monitoring
```bash
# Monitor error rates
./scripts/monitor_error_rate.sh

# Check response times
./scripts/monitor_response_times.sh
```

### 8.2 Alert Configuration
- Re-enable monitoring alerts
- Set up deployment-specific dashboards
- Configure anomaly detection

### 8.3 Performance Metrics
- Track error rates for 1 hour post-deployment
- Monitor response time percentiles
- Watch for memory leaks

## Section 9: Documentation and Communication

### 9.1 Update Deployment Log
```bash
# Log deployment details
echo "$(date): Deployed commit $(git rev-parse --short HEAD)" >> /var/log/deployments.log
```

### 9.2 Stakeholder Communication
- Send deployment completion notification
- Update status page
- Post in team communication channels

### 9.3 Knowledge Base Updates
- Update deployment documentation if process changed
- Document any issues encountered
- Update runbook with lessons learned

## Section 10: Emergency Procedures

### 10.1 Immediate Issues
**Problem**: Website completely down
**Solution**: 
1. Check service status: `systemctl status nginx`
2. Check logs: `tail -100 /var/log/nginx/error.log`
3. Rollback if necessary

**Problem**: Database connection errors
**Solution**:
1. Verify database is running
2. Check connection strings
3. Rollback database migrations if needed

### 10.2 Performance Issues
**Problem**: High response times
**Solution**:
1. Check server resources: `top`, `free -h`
2. Review recent changes
3. Consider rolling back

### 10.3 Security Issues
**Problem**: Security vulnerability detected
**Solution**:
1. Immediately rollback deployment
2. Notify security team
3. Investigate and patch

## Section 11: Contacts and Escalation

### 11.1 Primary Contacts
- **Deployment Lead**: [Name] - [Phone] - [Slack]
- **DevOps Engineer**: [Name] - [Phone] - [Slack]
- **Application Owner**: [Name] - [Phone] - [Slack]
- **Database Administrator**: [Name] - [Phone] - [Slack]

### 11.2 Escalation Path
1. Deployment Lead (immediate)
2. DevOps Manager (15 minutes)
3. Director of Engineering (30 minutes)
4. CTO (60 minutes)

### 11.3 Emergency Contacts
- **24/7 Operations**: [Phone]
- **Security Incident**: [Phone]
- **Hosting Provider**: [Phone]

## Appendix

### A. Deployment Checklists
**Pre-Deployment Checklist**: [Attached as separate file]
**Post-Deployment Checklist**: [Attached as separate file]
**Rollback Checklist**: [Attached as separate file]

### B. Script Templates
- Deployment script template
- Rollback script template
- Health check script template

### C. Environment-Specific Configurations
**Development**: Auto-deploy on merge
**Staging**: Manual approval required
**Production**: Scheduled maintenance windows

### D. Common Deployment Issues
1. **Permission issues**: Check file ownership with `ls -la`
2. **Port conflicts**: Check with `netstat -tulpn`
3. **Memory issues**: Monitor with `top` and `free -h`

---

**Document Version**: 3.0
**Last Updated**: 2024-12-29
**Review Cycle**: Monthly
**Approved By**: [DevOps Lead], [Engineering Director]

**Next Review Date**: 2025-01-29