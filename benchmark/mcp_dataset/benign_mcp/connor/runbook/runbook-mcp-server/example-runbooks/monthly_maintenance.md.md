# Monthly Server Maintenance Runbook

## Overview
This runbook outlines the standard monthly maintenance procedures for production servers. These procedures should be performed during the designated maintenance window (typically first Sunday of each month, 2:00 AM - 4:00 AM local time).

## Prerequisites
- Access to server with sudo/root privileges
- Maintenance window scheduled and communicated to stakeholders
- Backup of critical data completed
- Monitoring alerts temporarily disabled or set to maintenance mode

## Safety Checks (Pre-Maintenance)
1. **Check Current System Status**
   ```bash
   uptime
   systemctl status --all
   ```

2. **Verify Backups**
   ```bash
   # Check backup status
   ls -la /backups/
   # Verify recent backup integrity
   ```

3. **Notify Stakeholders**
   - Send maintenance notification email
   - Update status page
   - Post in team communication channels

## Section 1: Disk Usage Check and Cleanup

### 1.1 Check Disk Usage
```bash
# Check overall disk usage
df -h

# Check specific mount points
df -h / /home /var /tmp

# Check largest directories
du -sh /* 2>/dev/null | sort -rh | head -20
```

### 1.2 Identify Large Files
```bash
# Find files larger than 100MB
find / -type f -size +100M 2>/dev/null | head -20

# Check /var/log for large log files
find /var/log -type f -size +50M 2>/dev/null
```

### 1.3 Cleanup Procedures
```bash
# Clear package manager cache
sudo apt-get clean  # For Debian/Ubuntu
# OR
sudo yum clean all  # For RHEL/CentOS

# Remove old log files (keep last 30 days)
find /var/log -type f -name "*.log" -mtime +30 -delete

# Clear temporary files
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*
```

### 1.4 Log Rotation Check
```bash
# Verify logrotate configuration
sudo logrotate -d /etc/logrotate.conf
```

## Section 2: Package Updates

### 2.1 Update Package Lists
```bash
# Debian/Ubuntu
sudo apt-get update

# RHEL/CentOS
sudo yum check-update
```

### 2.2 Check Available Updates
```bash
# Debian/Ubuntu
sudo apt list --upgradable

# RHEL/CentOS
sudo yum list updates
```

### 2.3 Perform Security Updates
```bash
# Debian/Ubuntu - Security updates only
sudo apt-get upgrade --only-upgrade security

# RHEL/CentOS - Security updates
sudo yum update --security
```

### 2.4 Full System Update (Optional - during extended maintenance)
```bash
# Debian/Ubuntu
sudo apt-get upgrade -y

# RHEL/CentOS
sudo yum update -y
```

### 2.5 Kernel Update Handling
```bash
# Check if kernel was updated
uname -r
# Note: Kernel updates require reboot
```

## Section 3: Service Restart Procedures

### 3.1 Identify Services to Restart
```bash
# List all running services
systemctl list-units --type=service --state=running

# Check services that were updated
systemctl list-units --type=service --state=running | grep -E "(nginx|apache|mysql|postgres|redis)"
```

### 3.2 Graceful Service Restart Order
1. **Web Servers**
   ```bash
   # Nginx
   sudo systemctl reload nginx
   # OR
   sudo systemctl restart nginx
   
   # Apache
   sudo systemctl reload apache2
   # OR
   sudo systemctl restart apache2
   ```

2. **Application Servers**
   ```bash
   # Node.js/PM2
   pm2 reload all
   
   # Python/Gunicorn
   sudo systemctl reload gunicorn
   ```

3. **Database Services**
   ```bash
   # MySQL/MariaDB
   sudo systemctl restart mysql
   
   # PostgreSQL
   sudo systemctl restart postgresql
   ```

4. **Caching Services**
   ```bash
   # Redis
   sudo systemctl restart redis
   
   # Memcached
   sudo systemctl restart memcached
   ```

### 3.3 Verify Service Health After Restart
```bash
# Check service status
systemctl status nginx
systemctl status mysql
systemctl status redis

# Verify connectivity
curl -I http://localhost
mysql -e "SELECT 1"
redis-cli ping
```

## Section 4: System Health Verification

### 4.1 Post-Maintenance Checks
```bash
# Verify all services are running
systemctl list-units --type=service --state=failed

# Check disk space after cleanup
df -h

# Verify memory usage
free -h

# Check CPU load
top -bn1 | head -20
```

### 4.2 Application Health Checks
```bash
# Run application-specific health checks
curl -f http://localhost/health
# OR application-specific health endpoint
```

### 4.3 Log Monitoring
```bash
# Check for errors in logs
tail -100 /var/log/syslog | grep -i error
tail -100 /var/log/nginx/error.log
tail -100 /var/log/mysql/error.log
```

## Section 5: Post-Maintenance Tasks

### 5.1 Documentation
- Update maintenance log with date, time, and actions performed
- Note any issues encountered and resolutions
- Document any configuration changes made

### 5.2 Monitoring Re-enablement
- Remove maintenance mode from monitoring systems
- Verify alerts are active
- Check dashboards for normal operation

### 5.3 Stakeholder Communication
- Send completion notification
- Update status page to "Operational"
- Post completion notice in team channels

## Section 6: Rollback Procedures

### 6.1 When to Rollback
- Critical service failure after restart
- Application errors post-update
- Performance degradation

### 6.2 Package Rollback
```bash
# Debian/Ubuntu
sudo apt-get install --reinstall <package-name>

# RHEL/CentOS (if using yum history)
sudo yum history undo <transaction-id>
```

### 6.3 Configuration Rollback
```bash
# Restore from backup
sudo cp /backups/configs/nginx.conf /etc/nginx/nginx.conf
sudo systemctl reload nginx
```

## Section 7: Emergency Contacts

### 7.1 Primary Contacts
- System Administrator: [Name] - [Phone]
- DevOps Lead: [Name] - [Phone]
- On-call Engineer: [Name] - [Phone]

### 7.2 Escalation Path
1. Primary contact (30 minutes)
2. Team lead (60 minutes)
3. Director (90 minutes)

## Appendix

### A. Command Reference
```bash
# Quick status check
./scripts/health-check.sh

# Backup verification
./scripts/verify-backups.sh

# Log analysis
./scripts/analyze-logs.sh
```

### B. Common Issues and Solutions
1. **Service won't start**: Check logs at `/var/log/<service>/error.log`
2. **Disk full after cleanup**: Check for open files with `lsof +L1`
3. **Package conflicts**: Use `apt-get -f install` or `yum-complete-transaction`

### C. Maintenance Schedule
- First Sunday of each month
- Duration: 2 hours
- Backup window: Saturday 10 PM
- Communication: 24 hours notice required

---

**Last Updated**: $(date +%Y-%m-%d)
**Version**: 1.0
**Approved By**: [System Administrator Name]