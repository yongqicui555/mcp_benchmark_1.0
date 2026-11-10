# Emergency System Recovery Runbook

## Overview
This runbook provides procedures for recovering systems during emergency situations. It covers boot diagnostics, network checks, and service restoration for critical production systems. Use this guide when systems are unresponsive, experiencing boot failures, or critical services are down.

## Emergency Response Protocol

### Immediate Actions (First 5 Minutes)
1. **Assess Situation**
   - Determine system criticality (Production/Staging/Development)
   - Identify affected services and users
   - Check monitoring alerts and dashboards

2. **Notify Stakeholders**
   - Primary on-call engineer
   - Team lead
   - Affected business units
   - Update status page

3. **Gather Information**
   - Last known good state
   - Recent changes/deployments
   - Backup availability
   - Known issues/outages

## Section 1: Boot Diagnostics and Recovery

### 1.1 System Unresponsive (No SSH/RDP)
```bash
# If physical access is available:
1. Check power status (LED indicators)
2. Check network connectivity lights
3. Connect monitor/keyboard directly
4. Check for BIOS/POST errors
```

### 1.2 Boot Failure Diagnostics
```bash
# Access boot menu (usually F2, F12, DEL during boot)
# Check boot order and devices

# For Linux systems:
# Access GRUB menu (press Shift/Esc during boot)
# Select recovery mode or previous kernel
```

### 1.3 Single User Mode Recovery (Linux)
```bash
# From GRUB menu:
1. Edit kernel parameters
2. Append "single" or "init=/bin/bash"
3. Boot into single user mode
4. Mount filesystems: mount -o remount,rw /
5. Run diagnostics
```

### 1.4 Filesystem Checks
```bash
# Check and repair filesystems
fsck -y /dev/sda1
# OR for specific filesystem types
xfs_repair /dev/sda1
e2fsck -p /dev/sda1

# Check disk health
smartctl -a /dev/sda
badblocks -sv /dev/sda
```

### 1.5 Boot Loader Repair
```bash
# GRUB repair (Linux)
grub-install /dev/sda
update-grub

# Windows Boot Manager repair
bootrec /fixmbr
bootrec /fixboot
bootrec /rebuildbcd
```

## Section 2: Network Diagnostics and Recovery

### 2.1 Basic Network Checks
```bash
# Check network interfaces
ip addr show
ifconfig -a

# Check interface status
ethtool eth0

# Check routing
ip route show
route -n

# Check DNS resolution
nslookup google.com
dig google.com
```

### 2.2 Network Service Diagnostics
```bash
# Check network manager
systemctl status NetworkManager
systemctl status network

# Restart network services
systemctl restart NetworkManager
systemctl restart network

# For systemd-networkd
systemctl restart systemd-networkd
```

### 2.3 Firewall and Security Checks
```bash
# Check firewall status
systemctl status firewalld
systemctl status iptables
systemctl status ufw

# Temporarily disable firewall (emergency only)
systemctl stop firewalld
# OR
ufw disable

# Check SELinux/AppArmor
getenforce
sestatus
aa-status
```

### 2.4 Network Configuration Recovery
```bash
# Restore network configuration from backup
cp /etc/network/interfaces.backup /etc/network/interfaces
cp /etc/sysconfig/network-scripts/ifcfg-eth0.backup /etc/sysconfig/network-scripts/ifcfg-eth0

# Apply changes
systemctl restart network
# OR
ifdown eth0 && ifup eth0
```

### 2.5 VPN and Remote Access Recovery
```bash
# Check VPN services
systemctl status openvpn
systemctl status wireguard

# Restart VPN
systemctl restart openvpn@server

# Check SSH access
systemctl status sshd
ss -tlnp | grep :22
```

## Section 3: Service Restoration Procedures

### 3.1 Critical Service Identification
```bash
# List all failed services
systemctl list-units --state=failed

# Check critical services
systemctl status nginx
systemctl status mysql
systemctl status postgresql
systemctl status redis
systemctl status docker
```

### 3.2 Service Dependency Mapping
```bash
# Check service dependencies
systemctl list-dependencies nginx
systemctl list-dependencies mysql

# Start services in correct order
systemctl start docker
systemctl start mysql
systemctl start nginx
```

### 3.3 Database Recovery Procedures
```bash
# Check database status
mysqladmin -u root -p status
pg_isready

# Start database services
systemctl start mysql
systemctl start postgresql

# Check database integrity
mysqlcheck -u root -p --all-databases
```

### 3.4 Web Server Recovery
```bash
# Test configuration
nginx -t
apachectl configtest

# Start web servers
systemctl start nginx
systemctl start apache2

# Check listening ports
netstat -tulpn | grep -E ':80|:443'
```

### 3.5 Application Service Recovery
```bash
# Node.js/PM2
pm2 status
pm2 resurrect
pm2 restart all

# Python/Gunicorn
systemctl start gunicorn
systemctl status gunicorn

# Java/Tomcat
systemctl start tomcat
tail -f /var/log/tomcat/catalina.out
```

## Section 4: Data Recovery and Backup Restoration

### 4.1 Backup Verification
```bash
# List available backups
ls -la /backups/
ls -la /var/backups/

# Verify backup integrity
tar -tzf /backups/full_backup_$(date +%Y%m%d).tar.gz
```

### 4.2 Critical Data Restoration
```bash
# Restore configuration files
tar -xzf /backups/config_backup.tar.gz -C /

# Restore database
mysql -u root -p < /backups/database_backup.sql
# OR for PostgreSQL
pg_restore -U postgres -d database /backups/database_backup.dump
```

### 4.3 Full System Restoration
```bash
# For complete system recovery
# Boot from recovery media
# Mount root filesystem
mount /dev/sda1 /mnt

# Restore from backup
rsync -av /backups/full_system/ /mnt/

# Reinstall bootloader
chroot /mnt
grub-install /dev/sda
update-grub
exit
```

## Section 5: Hardware Diagnostics

### 5.1 Memory Diagnostics
```bash
# Check memory usage
free -h

# Run memory test
memtester 256M 1

# Check for memory errors
dmesg | grep -i memory
dmesg | grep -i error
```

### 5.2 CPU and Temperature Checks
```bash
# Check CPU usage
top
htop

# Check temperature
sensors
# OR for specific hardware
ipmitool sensor list

# Check CPU frequency
cpufreq-info
```

### 5.3 Disk Health and RAID Status
```bash
# Check disk SMART status
smartctl -H /dev/sda

# Check RAID status
cat /proc/mdstat
mdadm --detail /dev/md0

# Check disk space
df -h
du -sh /* 2>/dev/null | sort -rh | head -10
```

### 5.4 Power Supply Diagnostics
```bash
# Check power supply (if supported)
ipmitool dcmi power reading

# Check UPS status
upsc ups@localhost

# Check battery health (laptops)
upower -i /org/freedesktop/UPower/devices/battery_BAT0
```

## Section 6: Security Incident Response

### 6.1 Suspected Compromise
```bash
# Isolate system from network
ifdown eth0

# Preserve evidence
mkdir /root/evidence
cp /var/log/* /root/evidence/
cp /etc/passwd /root/evidence/
cp /etc/shadow /root/evidence/

# Check for unauthorized processes
ps aux | grep -E '(miner|backdoor|shell)'
netstat -tulpn | grep -v ESTABLISHED
```

### 6.2 Malware Detection and Removal
```bash
# Scan for malware
clamscan -r /
rkhunter --check

# Check for rootkits
chkrootkit

# Check file integrity
aide --check
```

### 6.3 Account Security
```bash
# Check for unauthorized users
cat /etc/passwd
cat /etc/shadow

# Check sudoers file
cat /etc/sudoers
visudo -c

# Check SSH authorized keys
cat ~/.ssh/authorized_keys
cat /etc/ssh/sshd_config
```

## Section 7: Communication and Escalation

### 7.1 Communication Protocol
- **First 15 minutes**: Technical team only
- **15-30 minutes**: Update team lead and manager
- **30-60 minutes**: Notify affected business units
- **60+ minutes**: Executive briefing if critical

### 7.2 Status Updates
```bash
# Update status page
curl -X POST https://status.example.com/api/incidents \
  -d '{"status":"investigating","message":"System recovery in progress"}'

# Send team notification
./scripts/notify_team.sh "Emergency recovery in progress"
```

### 7.3 Documentation Requirements
- Log all commands executed
- Document system state before/after recovery
- Note any data loss or corruption
- Create post-mortem timeline

## Section 8: Post-Recovery Validation

### 8.1 System Health Verification
```bash
# Comprehensive health check
./scripts/health_check.sh

# Service verification
systemctl is-active nginx
systemctl is-active mysql
systemctl is-active sshd

# Performance baseline
./scripts/performance_baseline.sh
```

### 8.2 Data Integrity Checks
```bash
# Verify critical data
./scripts/verify_data_integrity.sh

# Check application functionality
curl -f http://localhost/health
mysql -e "SELECT 1"
redis-cli ping
```

### 8.3 Security Posture Verification
```bash
# Verify security controls
systemctl is-active firewalld
getenforce

# Check for open vulnerabilities
./scripts/security_scan.sh
```

### 8.4 Monitoring Re-establishment
```bash
# Re-enable monitoring
systemctl restart prometheus
systemctl restart grafana-server

# Verify alerting
./scripts/test_alerts.sh
```

## Section 9: Rollback and Alternative Recovery Paths

### 9.1 When to Consider Rollback
- Recovery taking > 2 hours
- Data corruption detected
- Security compromise confirmed
- Multiple systems affected

### 9.2 Alternative Recovery Options
1. **Failover to standby system**
2. **Restore from offsite backup**
3. **Rebuild from golden image**
4. **Cloud instance restoration**

### 9.3 Decision Matrix
```
Severity Level | Recovery Time | Action
---------------|---------------|--------
Critical       | > 1 hour      | Failover
High           | > 2 hours     | Restore backup
Medium         | > 4 hours     | Rebuild system
Low            | > 8 hours     | Schedule maintenance
```

## Section 10: Emergency Contacts

### 10.1 Primary Contacts (24/7)
- **On-call Engineer**: [Name] - [Phone] - [Pager]
- **Systems Lead**: [Name] - [Phone]
- **Security Officer**: [Name] - [Phone]
- **Network Engineer**: [Name] - [Phone]

### 10.2 Vendor Contacts
- **Hosting Provider**: [Company] - [Phone] - [Support Ticket]
- **Hardware Vendor**: [Company] - [Phone] - [Contract #]
- **Software Support**: [Company] - [Phone] - [License #]

### 10.3 Business Continuity
- **Business Unit Lead**: [Name] - [Phone]
- **Customer Support**: [Phone] - [Email]
- **Public Relations**: [Name] - [Phone]

## Appendix

### A. Quick Reference Commands
```bash
# System status
systemctl list-units --state=failed
journalctl -xe
dmesg | tail -50

# Network troubleshooting
traceroute 8.8.8.8
mtr 8.8.8.8
tcptraceroute example.com 443

# Disk recovery
testdisk /dev/sda
photorec /dev/sda1
```

### B. Recovery Time Objectives (RTO)
- **Critical systems**: 1 hour
- **Important systems**: 4 hours
- **Standard systems**: 8 hours
- **Development systems**: 24 hours

### C. Backup Verification Schedule
- Daily: Incremental backup verification
- Weekly: Full backup restoration test
- Monthly: Disaster recovery drill

### D. Common Failure Scenarios
1. **Boot failure**: Corrupted GRUB, failed disk
2. **Network outage**: Misconfiguration, hardware failure
3. **Service crash**: Memory leak, dependency failure
4. **Data corruption**: Disk failure, software bug

---

**Document Version**: 4.0
**Last Updated**: 2024-12-29
**Review Cycle**: Quarterly
**Approved By**: [CTO], [Security Director]

**Next Review Date**: 2025-03-29
**Emergency Drill Schedule**: Monthly

**Important**: This document contains sensitive recovery procedures. Access should be restricted to authorized personnel only.