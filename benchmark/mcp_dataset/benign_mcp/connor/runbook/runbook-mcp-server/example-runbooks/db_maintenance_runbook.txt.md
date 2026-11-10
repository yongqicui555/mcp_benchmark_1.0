# Database Maintenance Runbook

## Overview
This runbook outlines standard procedures for maintaining database health, performance, and reliability. It covers weekly backups, index optimization, and log rotation procedures.

## Prerequisites
- Database administrator credentials
- Sufficient disk space for backups
- Maintenance window schedule
- Monitoring tools access
- Backup storage location configured

## Weekly Backups Procedure

### Full Backup Schedule
- **Frequency**: Every Sunday at 02:00 AM
- **Retention**: 4 weeks (monthly), plus quarterly archives

### Backup Steps
1. **Pre-backup Checks**
   - [ ] Verify available disk space (minimum 2x database size)
   - [ ] Check database connectivity
   - [ ] Review error logs for recent issues
   - [ ] Confirm backup destination is accessible

2. **Full Database Backup**
   - [ ] Execute full database backup command
   - [ ] Monitor backup progress and completion
   - [ ] Verify backup file integrity (checksums)
   - [ ] Record backup size and duration

3. **Post-backup Validation**
   - [ ] Test backup restoration on staging environment
   - [ ] Verify data consistency
   - [ ] Update backup log with timestamp and status
   - [ ] Clean up temporary files

### Backup Commands (Examples)
```bash
# PostgreSQL
pg_dump -U postgres -Fc database_name > /backup/db_backup_$(date +%Y%m%d).dump

# MySQL/MariaDB
mysqldump -u root -p database_name > /backup/db_backup_$(date +%Y%m%d).sql

# MongoDB
mongodump --host localhost --port 27017 --out /backup/db_backup_$(date +%Y%m%d)
```

## Index Optimization Procedure

### Optimization Schedule
- **Frequency**: Every Wednesday at 03:00 AM
- **Scope**: All production databases

### Optimization Steps
1. **Pre-optimization Analysis**
   - [ ] Identify fragmented indexes (over 30% fragmentation)
   - [ ] Check index usage statistics
   - [ ] Review query performance metrics
   - [ ] Identify unused indexes

2. **Index Maintenance**
   - [ ] Rebuild heavily fragmented indexes
   - [ ] Reorganize moderately fragmented indexes
   - [ ] Drop unused indexes (after validation)
   - [ ] Create missing indexes based on query analysis

3. **Post-optimization Validation**
   - [ ] Verify index integrity
   - [ ] Test critical queries performance
   - [ ] Monitor system resource usage
   - [ ] Document optimization results

### Optimization Commands (Examples)
```sql
-- PostgreSQL REINDEX
REINDEX INDEX index_name;
REINDEX TABLE table_name;
REINDEX DATABASE database_name;

-- MySQL OPTIMIZE TABLE
OPTIMIZE TABLE table_name;

-- SQL Server
ALTER INDEX index_name ON table_name REBUILD;
ALTER INDEX ALL ON table_name REORGANIZE;
```

## Log Rotation Procedure

### Rotation Schedule
- **Frequency**: Daily at 04:00 AM
- **Retention**: 30 days of logs, compressed archives for 90 days

### Rotation Steps
1. **Pre-rotation Checks**
   - [ ] Check current log file sizes
   - [ ] Verify log directory permissions
   - [ ] Confirm archive storage availability
   - [ ] Review log retention policies

2. **Log Rotation Execution**
   - [ ] Rotate current log files
   - [ ] Compress rotated logs
   - [ ] Move compressed logs to archive storage
   - [ ] Create new empty log files
   - [ ] Update log configuration if needed

3. **Post-rotation Validation**
   - [ ] Verify new logs are being written
   - [ ] Check compression integrity
   - [ ] Update rotation log with details
   - [ ] Monitor disk space after rotation

### Log Rotation Commands (Examples)
```bash
# PostgreSQL log rotation
pg_ctl -D /var/lib/postgresql/data logrotate

# MySQL log rotation
mysqladmin flush-logs
mv mysql.log mysql.log.old

# General log rotation with logrotate
logrotate -f /etc/logrotate.d/database
```

## Monitoring and Alerting

### Key Metrics to Monitor
- **Backup Status**: Success/failure, duration, size
- **Index Health**: Fragmentation percentage, usage statistics
- **Log Management**: File sizes, rotation success, disk usage
- **Performance**: Query response times, connection counts, cache hit ratio

### Alert Thresholds
- Backup failure or duration > 4 hours
- Index fragmentation > 50%
- Log directory > 80% disk usage
- Database response time > 5 seconds (95th percentile)

## Emergency Procedures

### Backup Failure
1. Check error logs for specific failure reason
2. Verify disk space and permissions
3. Attempt manual backup
4. If manual backup fails, escalate immediately
5. Document failure and resolution

### Optimization Issues
1. Stop optimization if causing performance degradation
2. Restore from recent backup if data corruption suspected
3. Review optimization parameters
4. Test on staging before retrying

### Log Rotation Failure
1. Check disk space and permissions
2. Manually rotate logs if automated process fails
3. Archive logs manually if needed
4. Update configuration and retest

## Maintenance Log Template
```
Date: [YYYY-MM-DD]
Maintenance Type: [Backup/Optimization/Log Rotation]
Start Time: [HH:MM]
End Time: [HH:MM]
Status: [Success/Partial/Failure]
Details: [Specific actions performed]
Issues Encountered: [Any problems]
Resolution: [How issues were resolved]
Performed By: [Name/Team]
Next Scheduled: [Next maintenance date]
```

## Contact Information
- Database Administrator: [Name/Contact]
- Primary On-call: [Name/Contact]
- Secondary On-call: [Name/Contact]
- Escalation Path: [Manager/Team Lead]

## Notes
- Always perform maintenance during off-peak hours
- Test procedures in staging environment first
- Keep runbook updated with new procedures
- Review and adjust schedules based on system growth