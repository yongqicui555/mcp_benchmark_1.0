# Monthly Server Maintenance Runbook

## Overview
This runbook documents the standard monthly maintenance procedure for production servers. The procedure includes disk usage checks, package updates, and service restarts to ensure system stability and security.

## Prerequisites
- Access to server with sudo/root privileges
- Maintenance window scheduled (recommended: off-peak hours)
- Backup of critical data completed
- Notification sent to stakeholders about maintenance window

## Procedure

### Step 1: Pre-Maintenance Checks
1. **Verify Backup Status**
   ```bash
   # Check if recent backups exist
   ls -la /backups/ | tail -5
   ```

2. **Check System Uptime**
   ```bash
   uptime
   ```

3. **Review System Logs**
   ```bash
   tail -50 /var/log/syslog
   ```

### Step 2: Disk Usage Check
1. **Check Disk Space**
   ```bash
   df -h
   ```

2. **Check Inode Usage**
   ```bash
   df -i
   ```

3. **Identify Large Files/Directories**
   ```bash
   # Top 10 largest directories in /var
   sudo du -sh /var/* | sort -rh | head -10
   
   # Top 10 largest files in /var/log
   sudo find /var/log -type f -exec du -sh {} + | sort -rh | head -10
   ```

4. **Cleanup Old Logs**
   ```bash
   # Clean old journal logs (keep last 2 weeks)
   sudo journalctl --vacuum-time=14d
   
   # Clean old package cache
   sudo apt-get clean
   ```

### Step 3: Package Updates
1. **Update Package Lists**
   ```bash
   sudo apt-get update
   ```

2. **Check Available Updates**
   ```bash
   sudo apt list --upgradable
   ```

3. **Perform Security Updates**
   ```bash
   sudo apt-get upgrade --only-upgrade security
   ```

4. **Perform Full System Upgrade (Optional)**
   ```bash
   # For non-critical updates
   sudo apt-get upgrade -y
   ```

5. **Cleanup After Updates**
   ```bash
   sudo apt-get autoremove -y
   sudo apt-get autoclean
   ```

### Step 4: Service Management
1. **Check Service Status**
   ```bash
   # List all running services
   sudo systemctl list-units --type=service --state=running
   ```

2. **Restart Critical Services**
   ```bash
   # Restart web server
   sudo systemctl restart nginx
   # or
   sudo systemctl restart apache2
   
   # Restart database
   sudo systemctl restart mysql
   # or
   sudo systemctl restart postgresql
   
   # Restart application services
   sudo systemctl restart your-application-service
   ```

3. **Verify Service Health**
   ```bash
   # Check service status
   sudo systemctl status nginx
   sudo systemctl status mysql
   ```

### Step 5: Post-Maintenance Verification
1. **Verify System Functionality**
   ```bash
   # Check if services are responding
   curl -I http://localhost
   
   # Check database connectivity
   mysql -e "SELECT 1;" || psql -c "SELECT 1;"
   ```

2. **Monitor System Metrics**
   ```bash
   # Check CPU and memory
   top -bn1 | head -20
   
   # Check disk I/O
   iostat -x 1 3
   ```

3. **Review Error Logs**
   ```bash
   tail -100 /var/log/nginx/error.log
   tail -100 /var/log/mysql/error.log
   ```

### Step 6: Documentation and Reporting
1. **Update Maintenance Log**
   ```bash
   echo "$(date): Monthly maintenance completed" >> /var/log/maintenance.log
   ```

2. **Generate Report**
   - Record any issues encountered
   - Document updates applied
   - Note services restarted
   - Record disk usage before/after cleanup

## Emergency Rollback Procedure
If issues occur during maintenance:

1. **Stop Further Changes**
   ```bash
   # Cancel any ongoing operations
   # Press Ctrl+C if in interactive mode
   ```

2. **Restore Services**
   ```bash
   # Restart all critical services
   sudo systemctl restart nginx mysql your-application-service
   ```

3. **Checkpoint Recovery**
   ```bash
   # If using LVM snapshots
   sudo lvconvert --merge /dev/vg_maintenance/snapshot_root
   ```

4. **Contact Support**
   - Escalate to senior sysadmin
   - Notify application team
   - Update stakeholders

## Safety Guidelines
- Always perform maintenance during scheduled windows
- Have rollback plan ready before starting
- Test changes in staging environment first when possible
- Keep maintenance sessions under 4 hours
- Document all changes made

## Success Criteria
- All services running normally
- No critical errors in logs
- System resources within normal limits
- Application functionality verified
- Stakeholders notified of completion

## Notes
- Update this runbook as procedures change
- Include server-specific configurations
- Review and adjust based on past incidents
- Keep runbook accessible to all team members

---
*Last Updated: $(date)*
*Maintenance Window: First Sunday of each month, 02:00-04:00 UTC*