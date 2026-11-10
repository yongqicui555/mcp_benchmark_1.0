# Server Monitoring Runbook

## Overview
This runbook provides comprehensive procedures for monitoring server health across CPU usage, memory utilization, disk space, and network connectivity. It includes alert thresholds, investigation steps, and remediation procedures for common issues.

## Monitoring Architecture

### Monitoring Stack Components
- **Metrics Collection**: Prometheus, Telegraf, collectd
- **Alert Management**: Alertmanager, PagerDuty, OpsGenie
- **Visualization**: Grafana, Kibana
- **Log Management**: ELK Stack, Loki
- **Infrastructure**: Nagios, Zabbix (legacy)

### Data Collection Frequency
- **High-frequency metrics**: 15-second intervals (CPU, memory, network)
- **Standard metrics**: 60-second intervals (disk, processes, services)
- **Long-term metrics**: 5-minute intervals (trend analysis, capacity planning)

## CPU Usage Monitoring

### Alert Thresholds
- **Warning**: CPU utilization > 80% for 5 minutes
- **Critical**: CPU utilization > 90% for 2 minutes
- **Emergency**: CPU utilization > 95% for 1 minute

### Investigation Procedures

#### Step 1: Initial Assessment
- [ ] Check which CPU cores are affected
- [ ] Identify time pattern (spike vs sustained)
- [ ] Review recent deployment/configuration changes
- [ ] Check system load average (1m, 5m, 15m)

#### Step 2: Process Analysis
```bash
# Top CPU-consuming processes
top -b -n 1 | head -20
ps aux --sort=-%cpu | head -10

# Per-process CPU usage
pidstat -u 1 5

# CPU usage by container (if applicable)
docker stats --no-stream
```

#### Step 3: System Context
- [ ] Check CPU steal time (virtualization issues)
- [ ] Review CPU frequency scaling
- [ ] Examine interrupt rates
- [ ] Check for thermal throttling

### Remediation Actions

#### High User CPU
1. **Identify process**: `top`, `htop`, `atop`
2. **Analyze process**:
   - Is it expected workload?
   - Check process priority (nice value)
   - Review process limits
3. **Take action**:
   - Adjust process priority if non-critical
   - Consider horizontal scaling
   - Optimize application code

#### High System CPU
1. **Check system calls**: `strace -c -p <PID>`
2. **Review kernel activities**:
   - Context switches: `vmstat 1`
   - Interrupts: `cat /proc/interrupts`
3. **Investigate**:
   - I/O wait issues
   - Network packet processing
   - System call bottlenecks

#### High I/O Wait
1. **Check disk I/O**: `iostat -x 1`
2. **Identify disk-bound processes**: `iotop`
3. **Solutions**:
   - Optimize disk I/O patterns
   - Consider SSD upgrade
   - Implement caching

### Escalation Matrix
- **Level 1**: On-call engineer (immediate)
- **Level 2**: Senior SRE (if unresolved in 30 minutes)
- **Level 3**: Infrastructure lead (if unresolved in 1 hour)

## Memory Threshold Monitoring

### Alert Thresholds
- **Warning**: Memory usage > 85% for 10 minutes
- **Critical**: Memory usage > 90% for 5 minutes
- **Emergency**: Memory usage > 95% for 2 minutes

### Investigation Procedures

#### Step 1: Memory Breakdown
```bash
# Overall memory usage
free -h

# Detailed memory info
cat /proc/meminfo

# Memory by process
ps aux --sort=-%mem | head -10

# Slab memory usage
slabtop -o
```

#### Step 2: Swap Analysis
- [ ] Check swap usage: `swapon -s`
- [ ] Monitor swap in/out: `vmstat 1`
- [ ] Identify processes using swap: `cat /proc/*/status | grep -i swap`

#### Step 3: Memory Pressure
- [ ] Check page faults: `sar -B 1`
- [ ] Monitor OOM killer: `dmesg | grep -i oom`
- [ ] Review memory cgroup limits (if applicable)

### Remediation Actions

#### High Application Memory
1. **Identify memory-hungry processes**
2. **Check for memory leaks**:
   - Monitor process RSS over time
   - Use `valgrind` or similar tools
3. **Actions**:
   - Restart problematic processes
   - Implement memory limits
   - Optimize application memory usage

#### High Kernel Memory
1. **Check slab memory**: `slabtop`
2. **Investigate kernel modules**
3. **Solutions**:
   - Tune kernel parameters
   - Update kernel/drivers
   - Reduce network buffer sizes if appropriate

#### Swap Thrashing
1. **Immediate actions**:
   - Identify and kill worst offenders
   - Add temporary swap if available
2. **Long-term solutions**:
   - Increase physical memory
   - Optimize memory usage patterns
   - Implement better caching

### Memory Optimization Checklist
```
[ ] Application memory profiling completed
[ ] Kernel parameters reviewed and tuned
[ ] Swap configuration optimized
[ ] Memory limits configured for containers
[ ] Monitoring for memory leaks implemented
```

## Disk Space Monitoring

### Alert Thresholds
- **Warning**: Disk usage > 80%
- **Critical**: Disk usage > 90%
- **Emergency**: Disk usage > 95%

### Filesystem-Specific Thresholds
- **/ (root)**: 80% warning, 90% critical
- **/var/log**: 85% warning, 95% critical
- **/home**: 75% warning, 85% critical
- **Database volumes**: 70% warning, 80% critical

### Investigation Procedures

#### Step 1: Disk Usage Analysis
```bash
# Overall disk usage
df -h

# Detailed filesystem info
df -i  # inode usage

# Find large files
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -20

# Directory size analysis
du -sh /* 2>/dev/null | sort -hr | head -20
```

#### Step 2: Growth Rate Analysis
- [ ] Check historical growth patterns
- [ ] Identify fastest-growing directories
- [ ] Review log rotation policies
- [ ] Check for orphaned temporary files

#### Step 3: Special Considerations
- [ ] Database tablespace usage
- [ ] Docker/container storage
- [ ] Backup file retention
- [ ] Cache directory sizes

### Remediation Actions

#### Immediate Cleanup
1. **Identify cleanup candidates**:
   - Old log files: `find /var/log -type f -mtime +30`
   - Temporary files: `find /tmp -type f -mtime +7`
   - Cache directories: `/var/cache`, `~/.cache`
2. **Safe deletions**:
   - Rotate logs: `logrotate -f /etc/logrotate.conf`
   - Clear package manager cache
   - Remove old kernel versions

#### Application-Level Solutions
1. **Implement retention policies**
2. **Archive old data** (cold storage)
3. **Compress historical data**
4. **Review data ingestion rates**

#### Infrastructure Solutions
1. **Increase disk capacity** (LVM expansion)
2. **Implement storage tiering**
3. **Add monitoring for specific directories**
4. **Set up automated cleanup scripts**

### Disk Space Management Scripts
```bash
#!/bin/bash
# Daily disk cleanup script
LOG_DIR="/var/log"
TEMP_DIR="/tmp"
CACHE_DIR="/var/cache"

# Clean old logs
find $LOG_DIR -name "*.log" -mtime +30 -delete

# Clean temporary files older than 7 days
find $TEMP_DIR -type f -mtime +7 -delete

# Clean package manager cache
apt-get clean 2>/dev/null || yum clean all 2>/dev/null

# Report disk usage
df -h > /var/log/disk_usage_$(date +%Y%m%d).log
```

## Network Connectivity Checks

### Alert Thresholds
- **Warning**: Packet loss > 1% for 5 minutes
- **Critical**: Packet loss > 5% for 2 minutes
- **Emergency**: Complete network outage

### Connectivity Tests

#### Internal Network Checks
```bash
# Basic connectivity
ping -c 5 <internal_host>

# Port connectivity
nc -zv <host> <port>
telnet <host> <port>

# DNS resolution
dig <hostname>
nslookup <hostname>

# Route tracing
traceroute <destination>
mtr <destination>
```

#### External Connectivity Checks
- [ ] Internet connectivity: `ping 8.8.8.8`
- [ ] DNS resolution: `dig google.com`
- [ ] HTTPS connectivity: `curl -I https://example.com`
- [ ] NTP synchronization: `ntpdate -q pool.ntp.org`

### Investigation Procedures

#### Step 1: Local Network Stack
```bash
# Network interfaces
ip addr show
ifconfig -a

# Routing table
ip route show
netstat -rn

# Network statistics
ss -tulpn
netstat -s

# Connection states
ss -s
```

#### Step 2: Performance Analysis
- [ ] Bandwidth usage: `iftop`, `nethogs`
- [ ] Packet capture: `tcpdump -i eth0 -c 100`
- [ ] Latency measurement: `ping -c 10 <host>`
- [ ] Jitter analysis: `ping -c 100 -i 0.1 <host>`

#### Step 3: Service Dependencies
- [ ] Load balancer health
- [ ] Firewall rules verification
- [ ] VPN connectivity (if applicable)
- [ ] Cloud provider network status

### Remediation Actions

#### DNS Issues
1. **Check local resolver**: `cat /etc/resolv.conf`
2. **Test different DNS servers**
3. **Clear DNS cache**: `systemctl restart systemd-resolved`
4. **Check DNS server health**

#### Routing Problems
1. **Verify default gateway**
2. **Check routing table consistency**
3. **Test different network paths**
4. **Review BGP/OSPF status (if applicable)**

#### Firewall Issues
1. **Check iptables/nftables rules**
2. **Verify security group settings (cloud)**
3. **Test with temporary rule relaxation**
4. **Review recent firewall changes**

#### Bandwidth Saturation
1. **Identify bandwidth-heavy processes**
2. **Implement QoS/traffic shaping**
3. **Consider bandwidth upgrade**
4. **Optimize data transfer patterns**

### Network Health Dashboard Metrics
- **Latency**: < 50ms (internal), < 100ms (external)
- **Packet loss**: < 0.1% (internal), < 0.5% (external)
- **Bandwidth utilization**: < 70% sustained
- **TCP retransmission rate**: < 1%
- **DNS resolution time**: < 100ms

## Alert Response Workflow

### Alert Triage Process
1. **Acknowledge alert** within 5 minutes
2. **Classify severity** using defined thresholds
3. **Initial investigation** using this runbook
4. **Escalate** if unable to resolve within timeframe

### Communication Protocol
- **SEV-1**: Immediate team notification, executive alert within 15 minutes
- **SEV-2**: Team notification within 30 minutes
- **SEV-3**: Daily status report
- **SEV-4**: Weekly review

### Post-Incident Actions
1. **Document** root cause and resolution
2. **Update** monitoring thresholds if needed
3. **Create** preventive measures
4. **Schedule** follow-up review

## Monitoring Configuration

### Prometheus Alert Rules Example
```yaml
groups:
  - name: cpu_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 80% for 5 minutes"

  - name: memory_alerts
    rules:
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 85% for 10 minutes"
```

### Grafana Dashboard Configuration
- **CPU Dashboard**: Real-time usage, historical trends, top processes
- **Memory Dashboard**: Usage breakdown, swap activity, pressure stalls
- **Disk Dashboard**: Usage by mount, growth rates, inode usage
- **Network Dashboard**: Bandwidth, latency, packet loss, connection states

## Maintenance Schedule

### Daily Checks
- [ ] Review critical alerts from past 24 hours
- [ ] Check dashboard for anomalies
- [ ] Verify backup completion
- [ ] Review capacity trends

### Weekly Tasks
- [ ] Analyze alert frequency and patterns
- [ ] Review and tune alert thresholds
- [ ] Clean up old monitoring data
- [ ] Update runbook with new learnings

### Monthly Activities
- [ ] Capacity planning review
- [ ] Monitoring stack updates
- [ ] Disaster recovery testing
- [ ] Team training on new features

## Tools and Resources

### Command Reference
- **CPU**: `top`, `htop`, `mpstat`, `pidstat`, `perf`
- **Memory**: `free`, `vmstat`, `slabtop`, `pmap`
- **Disk**: `df`, `du`, `iostat`, `iotop`, `lsof`
- **Network**: `ping`, `traceroute`, `mtr`, `ss`, `netstat`, `tcpdump`

### Documentation Links
- [Monitoring Stack Documentation]
- [Alert Management Procedures]
- [Capacity Planning Guidelines]
- [Disaster Recovery Plans]

## Contact Information
- **Primary On-call**: [Name/Contact]
- **Secondary On-call**: [Name/Contact]
- **Infrastructure Team**: [Team Contact]
- **Escalation Path**: [Manager/Director]

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Name] | Initial version |

---

**Note**: This runbook should be reviewed and updated quarterly to reflect changes in infrastructure, applications, and monitoring tools.