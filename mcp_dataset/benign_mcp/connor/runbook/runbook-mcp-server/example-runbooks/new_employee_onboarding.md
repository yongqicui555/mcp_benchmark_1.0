# New Employee Onboarding Runbook

## Overview
This runbook outlines the standard procedures for onboarding new employees. It covers account creation, software installation, access permissions, and orientation activities. The process should be completed within 3 business days before the employee's start date.

## Prerequisites
- HR notification with employee details (name, department, start date, manager)
- Approved hardware request (laptop, accessories)
- Assigned workspace/desk number
- Security clearance level determined

## Section 1: Pre-Onboarding Preparation (Day -5)

### 1.1 Gather Employee Information
```
Employee Name: [Full Name]
Start Date: [YYYY-MM-DD]
Department: [Department Name]
Manager: [Manager Name]
Job Title: [Job Title]
Location: [Office Location]
Employee ID: [To be assigned]
```

### 1.2 Hardware Preparation
- [ ] Order laptop (standard configuration for department)
- [ ] Order peripherals (monitor, keyboard, mouse, dock)
- [ ] Prepare access badge
- [ ] Assign desk/workspace
- [ ] Prepare welcome package (company swag, notebook, pen)

### 1.3 Documentation Preparation
- [ ] Prepare employment contract
- [ ] Prepare confidentiality agreement
- [ ] Prepare IT acceptable use policy
- [ ] Prepare benefits enrollment forms

## Section 2: Account Creation (Day -3)

### 2.1 Create Directory Accounts
```bash
# Active Directory/LDAP account creation
# Use company's standard username format (e.g., first.last)
Username: [username]
Temporary Password: [Generate secure temporary password]
```

### 2.2 Email Account Setup
```bash
# Microsoft 365/Google Workspace setup
Email Address: [username@company.com]
Aliases: [firstname.lastname@company.com] (if different)
Mailbox Size: 50GB standard
```

### 2.3 Collaboration Tools
- [ ] Slack/Teams account: [username]
- [ ] Zoom/Meeting account: [username]
- [ ] Calendar access configured
- [ ] Shared drives/department folders access

### 2.4 Internal Systems
- [ ] HRIS system access (Workday/BambooHR)
- [ ] Time tracking system
- [ ] Expense reporting system
- [ ] Project management tool (Jira/Asana)

## Section 3: Software Installation (Day -2)

### 3.1 Standard Software Package
**Operating System**: Windows 11 Pro / macOS [version]
**Security Software**:
- [ ] Endpoint protection (CrowdStrike/SentinelOne)
- [ ] VPN client (GlobalProtect/Cisco AnyConnect)
- [ ] Password manager (1Password/LastPass)
- [ ] Disk encryption (BitLocker/FileVault)

**Productivity Suite**:
- [ ] Microsoft Office 365 / Google Workspace
- [ ] Adobe Acrobat Reader
- [ ] Web browsers (Chrome, Firefox, Edge)
- [ ] PDF editor (if required)

**Development Tools** (for engineering roles):
- [ ] IDE (VS Code/IntelliJ)
- [ ] Git client
- [ ] Docker
- [ ] Node.js/Python/Java runtime
- [ ] Database clients

### 3.2 Department-Specific Software
**Sales/Marketing**:
- [ ] CRM (Salesforce/HubSpot)
- [ ] Marketing automation
- [ ] Analytics tools

**Engineering**:
- [ ] AWS/Azure/GCP CLI
- [ ] Kubernetes tools
- [ ] Monitoring tools

**Finance**:
- [ ] Accounting software
- [ ] Financial reporting tools

### 3.3 Configuration Steps
```bash
# Standard configuration checklist
1. Join computer to domain: COMPANYDOMAIN
2. Configure network printers
3. Set up backup solution
4. Configure email client
5. Install department-specific certificates
6. Configure development environment (if applicable)
```

## Section 4: Access Permissions (Day -2)

### 4.1 Network Access
- [ ] VPN access configured
- [ ] Wi-Fi credentials provided
- [ ] Network drive mappings:
  - H: drive (personal)
  - S: drive (shared department)
  - P: drive (projects)

### 4.2 Application Access
**Required for all employees**:
- [ ] Intranet portal
- [ ] Document management system
- [ ] Help desk ticketing system
- [ ] Knowledge base

**Department-specific**:
- [ ] Code repositories (GitHub/GitLab/Bitbucket)
- [ ] CI/CD pipelines
- [ ] Monitoring dashboards (Grafana/New Relic)
- [ ] Database access (read/write as needed)
- [ ] API keys/service accounts

### 4.3 Physical Access
- [ ] Office building access
- [ ] Department floor access
- [ ] Server room access (if required)
- [ ] Conference room booking system

### 4.4 Security Groups
```powershell
# Example Active Directory groups
Add-ADGroupMember -Identity "All Employees"
Add-ADGroupMember -Identity "[Department] Employees"
Add-ADGroupMember -Identity "[Project] Team"
Add-ADGroupMember -Identity "[Location] Office"
```

## Section 5: First Day Setup (Day 0)

### 5.1 Morning Preparation
- [ ] Computer delivered to desk and powered on
- [ ] Welcome email sent with first-day schedule
- [ ] Manager notified of employee arrival
- [ ] IT support notified for first-day assistance

### 5.2 Welcome and Orientation
**9:00 AM - Welcome Meeting** (30 mins)
- HR representative
- IT representative
- Manager

**9:30 AM - Account Activation** (30 mins)
- Guide through first login
- Password change
- Multi-factor authentication setup
- Email access verification

**10:00 AM - Software Walkthrough** (60 mins)
- Essential applications
- Communication tools
- File storage structure
- Security protocols

### 5.3 Afternoon Activities
**1:00 PM - Department Introduction** (60 mins)
- Meet team members
- Department overview
- Current projects

**2:00 PM - Security Training** (60 mins)
- Security policies
- Data handling procedures
- Incident reporting

**3:00 PM - System Access Verification** (30 mins)
- Verify all accounts are working
- Test application access
- Confirm permissions

## Section 6: First Week Activities (Days 1-5)

### 6.1 Daily Check-ins
- **Day 1**: Manager check-in (end of day)
- **Day 2**: IT support check-in
- **Day 3**: HR check-in
- **Day 4**: Team lead check-in
- **Day 5**: Week 1 review with manager

### 6.2 Training Schedule
- Company culture and values
- Product training
- Development processes (if applicable)
- Compliance requirements

### 6.3 Account Fine-tuning
- [ ] Adjust permissions based on role needs
- [ ] Add to additional distribution lists
- [ ] Configure specialized software
- [ ] Set up development environments

## Section 7: Documentation and Compliance

### 7.1 Required Documentation
- [ ] Employee information form completed
- [ ] IT acceptable use policy signed
- [ ] Security training completion certificate
- [ ] Equipment checkout form signed
- [ ] Emergency contact information

### 7.2 Compliance Tasks
- [ ] Background check completed
- [ ] Right-to-work verification
- [ ] Benefits enrollment submitted
- [ ] Tax forms completed

### 7.3 Record Keeping
```
File: /HR/Employees/[Employee ID]/Onboarding/
├── Contracts/
├── IT_Setup/
├── Training/
└── Compliance/
```

## Section 8: Troubleshooting Common Issues

### 8.1 Account Issues
**Problem**: Cannot log in to domain
**Solution**: 
1. Verify account is enabled in AD
2. Check password expiration
3. Verify network connectivity

**Problem**: Email not working
**Solution**:
1. Check mailbox provisioning status
2. Verify license assignment
3. Check forwarding rules

### 8.2 Access Issues
**Problem**: Cannot access shared drives
**Solution**:
1. Verify group membership
2. Check share permissions
3. Confirm network mapping

**Problem**: Application access denied
**Solution**:
1. Verify license assignment
2. Check role-based access control
3. Confirm department approval

### 8.3 Hardware Issues
**Problem**: Laptop not connecting to VPN
**Solution**:
1. Reinstall VPN client
2. Check certificate installation
3. Verify network settings

## Section 9: Offboarding Considerations

### 9.1 Account Decommissioning Timeline
- **Day 0**: Disable remote access
- **Day +1**: Forward email, disable accounts
- **Day +7**: Full account deletion (except legal hold)

### 9.2 Access Revocation Order
1. VPN and remote access
2. Production systems
3. Internal applications
4. Email and collaboration tools
5. Directory accounts

## Section 10: Contacts and Escalation

### 10.1 Primary Contacts
- **HR Coordinator**: [Name] - [Phone] - [Email]
- **IT Onboarding Specialist**: [Name] - [Phone] - [Email]
- **Department Manager**: [Name] - [Phone] - [Email]
- **Security Officer**: [Name] - [Phone] - [Email]

### 10.2 Escalation Path
1. IT Help Desk (tier 1 support)
2. IT Onboarding Specialist
3. IT Manager
4. HR Director

### 10.3 Emergency Contacts
- **After-hours IT Support**: [Phone]
- **Security Incident**: [Phone]
- **Facilities Emergency**: [Phone]

## Appendix

### A. Checklists
**Pre-Onboarding Checklist**: [Attached as separate file]
**First Day Checklist**: [Attached as separate file]
**First Week Checklist**: [Attached as separate file]

### B. Templates
- Welcome email template
- Account creation request form
- Equipment checkout form
- Training completion certificate

### C. Department-Specific Requirements
**Engineering**: Development environment setup guide
**Sales**: CRM access and training guide
**Finance**: Financial system access procedures

---

**Document Version**: 2.1
**Last Updated**: 2024-12-29
**Review Cycle**: Quarterly
**Approved By**: [HR Director], [IT Director]

**Next Review Date**: 2025-03-29