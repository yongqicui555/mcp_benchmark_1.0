import re
import socket
import dns.resolver
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
import ipaddress

def validate_email_comprehensive(
    email: str,
    check_dns: bool = False,
    check_mx_records: bool = False,
    allow_ip_domains: bool = False,
    allow_localhost: bool = False,
    max_length: int = 254,
    min_local_part_length: int = 1,
    max_local_part_length: int = 64,
    min_domain_part_length: int = 1,
    max_domain_part_length: int = 255,
    additional_checks: bool = True
) -> Dict[str, Union[bool, str, Dict, List]]:
    """
    Comprehensive email validation with multiple verification levels.
    
    Args:
        email: Email address to validate
        check_dns: Check if domain exists via DNS lookup
        check_mx_records: Check if domain has MX records (for email delivery)
        allow_ip_domains: Allow IP addresses as domains (e.g., user@[192.168.1.1])
        allow_localhost: Allow localhost as domain
        max_length: Maximum total email length (RFC 5321: 254 chars)
        min_local_part_length: Minimum local part length
        max_local_part_length: Maximum local part length (RFC 5321: 64 chars)
        min_domain_part_length: Minimum domain part length
        max_domain_part_length: Maximum domain part length (RFC 1035: 255 chars)
        additional_checks: Perform additional security and format checks
        
    Returns:
        Dictionary with validation results and detailed information
        
    Examples:
        validate_email_comprehensive("user@example.com")
        validate_email_comprehensive("test@domain.com", check_dns=True, check_mx_records=True)
    """
    
    # Initialize result structure
    result = {
        "success": False,
        "email": email,
        "is_valid": False,
        "validation_level": "basic",
        "errors": [],
        "warnings": [],
        "details": {
            "local_part": "",
            "domain_part": "",
            "domain_type": "unknown",
            "format_valid": False,
            "length_valid": False,
            "character_valid": False,
            "dns_check": None,
            "mx_records": None,
            "security_checks": {}
        }
    }
    
    # Helper function to add errors
    def add_error(message: str):
        result["errors"].append(message)
    
    def add_warning(message: str):
        result["warnings"].append(message)
    
    # 1. Basic null/empty check
    if not email or not isinstance(email, str):
        add_error("Email address is empty or not a string")
        return result
    
    email = email.strip()
    result["email"] = email
    
    # 2. Length check (RFC 5321)
    if len(email) > max_length:
        add_error(f"Email exceeds maximum length of {max_length} characters (RFC 5321)")
        return result
    
    result["details"]["length_valid"] = True
    
    # 3. Basic format check - must contain exactly one @
    if email.count('@') != 1:
        add_error("Email must contain exactly one @ symbol")
        return result
    
    # Split into local and domain parts
    try:
        local_part, domain_part = email.split('@')
    except ValueError:
        add_error("Invalid email format - cannot split local and domain parts")
        return result
    
    result["details"]["local_part"] = local_part
    result["details"]["domain_part"] = domain_part
    
    # 4. Local part validation
    # Check length
    if len(local_part) < min_local_part_length:
        add_error(f"Local part must be at least {min_local_part_length} character(s)")
    
    if len(local_part) > max_local_part_length:
        add_error(f"Local part exceeds maximum length of {max_local_part_length} characters (RFC 5321)")
    
    # Check for valid characters in local part
    # According to RFC 5322, local part can contain:
    # - Letters (a-z, A-Z)
    # - Digits (0-9)
    # - Special characters: ! # $ % & ' * + - / = ? ^ _ ` { | } ~
    # - Dot (.) but not at start/end or consecutive
    
    # Simplified regex for common email patterns
    local_part_regex = r'^[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*$'
    
    if not re.match(local_part_regex, local_part):
        add_error("Local part contains invalid characters or format")
    
    # Check for leading/trailing dots
    if local_part.startswith('.') or local_part.endswith('.'):
        add_error("Local part cannot start or end with a dot")
    
    # Check for consecutive dots
    if '..' in local_part:
        add_error("Local part cannot contain consecutive dots")
    
    # 5. Domain part validation
    # Check length
    if len(domain_part) < min_domain_part_length:
        add_error(f"Domain part must be at least {min_domain_part_length} character(s)")
    
    if len(domain_part) > max_domain_part_length:
        add_error(f"Domain part exceeds maximum length of {max_domain_part_length} characters")
    
    # Check if domain is an IP address (e.g., user@[192.168.1.1])
    is_ip_domain = False
    ip_match = re.match(r'^\[(.*)\]$', domain_part)
    if ip_match:
        ip_str = ip_match.group(1)
        try:
            # Validate IP address
            ipaddress.ip_address(ip_str)
            is_ip_domain = True
            result["details"]["domain_type"] = "ip_address"
            
            if not allow_ip_domains:
                add_error("IP address domains are not allowed")
            elif ip_str == "127.0.0.1" or ip_str == "::1":
                if not allow_localhost:
                    add_error("Localhost domains are not allowed")
                else:
                    result["details"]["domain_type"] = "localhost"
        except ValueError:
            add_error("Invalid IP address format in domain")
    else:
        # Regular domain validation
        # Domain regex (simplified but covers most cases)
        domain_regex = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63}(?<!-))*\.[A-Za-z]{2,}$'
        
        if not re.match(domain_regex, domain_part):
            add_error("Domain part has invalid format")
        else:
            result["details"]["domain_type"] = "regular_domain"
        
        # Check for valid TLD (at least 2 letters)
        tld = domain_part.split('.')[-1]
        if len(tld) < 2:
            add_error("Top-level domain must be at least 2 characters")
        
        # Check for consecutive dots
        if '..' in domain_part:
            add_error("Domain cannot contain consecutive dots")
        
        # Check for leading/trailing hyphens in domain labels
        labels = domain_part.split('.')
        for label in labels:
            if label.startswith('-') or label.endswith('-'):
                add_error("Domain labels cannot start or end with hyphens")
    
    # If we have errors at this point, return
    if result["errors"]:
        return result
    
    result["details"]["format_valid"] = True
    result["details"]["character_valid"] = True
    
    # 6. Additional security and format checks
    if additional_checks:
        security_checks = {}
        
        # Check for disposable email domains
        disposable_domains = [
            'tempmail.com', 'throwawaymail.com', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', '10minutemail.com',
            'trashmail.com', 'dispostable.com', 'fakeinbox.com'
        ]
        
        for disposable in disposable_domains:
            if domain_part.endswith(disposable):
                security_checks["disposable_email"] = True
                add_warning(f"Domain appears to be disposable: {disposable}")
                break
        else:
            security_checks["disposable_email"] = False
        
        # Check for common typos
        common_typos = {
            'gmial.com': 'gmail.com',
            'gmal.com': 'gmail.com',
            'gmail.cm': 'gmail.com',
            'gmail.con': 'gmail.com',
            'hotmal.com': 'hotmail.com',
            'hotmai.com': 'hotmail.com',
            'yaho.com': 'yahoo.com',
            'yahoov.com': 'yahoo.com',
            'outlok.com': 'outlook.com'
        }
        
        for typo, correction in common_typos.items():
            if domain_part == typo:
                security_checks["possible_typo"] = True
                add_warning(f"Possible typo: '{typo}' should be '{correction}'")
                break
        else:
            security_checks["possible_typo"] = False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            (r'.*\.exe$', "Domain ends with .exe - highly suspicious"),
            (r'.*\.js$', "Domain ends with .js - suspicious"),
            (r'.*\.php$', "Domain ends with .php - suspicious"),
            (r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$', "Domain looks like IP address without brackets"),
            (r'.*test.*', "Domain contains 'test' - might be testing domain"),
            (r'.*example.*', "Domain contains 'example' - example domain"),
        ]
        
        for pattern, message in suspicious_patterns:
            if re.match(pattern, domain_part, re.IGNORECASE):
                security_checks["suspicious_pattern"] = True
                add_warning(message)
                break
        else:
            security_checks["suspicious_pattern"] = False
        
        result["details"]["security_checks"] = security_checks
    
    # 7. DNS validation (if requested)
    if check_dns and not is_ip_domain:
        try:
            # Try to resolve the domain
            socket.gethostbyname(domain_part)
            result["details"]["dns_check"] = True
        except socket.gaierror:
            result["details"]["dns_check"] = False
            add_error(f"Domain '{domain_part}' does not exist or cannot be resolved")
    
    # 8. MX record validation (if requested)
    if check_mx_records and not is_ip_domain:
        try:
            answers = dns.resolver.resolve(domain_part, 'MX')
            mx_records = []
            for rdata in answers:
                mx_records.append({
                    "preference": rdata.preference,
                    "exchange": str(rdata.exchange)
                })
            
            if mx_records:
                result["details"]["mx_records"] = mx_records
            else:
                result["details"]["mx_records"] = False
                add_warning(f"Domain '{domain_part}' has no MX records (cannot receive email)")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
            result["details"]["mx_records"] = False
            add_warning(f"Domain '{domain_part}' has no MX records or cannot be resolved")
        except Exception as e:
            result["details"]["mx_records"] = None
            add_warning(f"Could not check MX records: {str(e)}")
    
    # 9. Final validation decision
    # If we have errors, email is invalid
    if not result["errors"]:
        result["is_valid"] = True
        result["success"] = True
        
        # Determine validation level
        if check_mx_records and result["details"]["mx_records"]:
            result["validation_level"] = "mx_verified"
        elif check_dns and result["details"]["dns_check"]:
            result["validation_level"] = "dns_verified"
        else:
            result["validation_level"] = "format_verified"
    
    # Add summary
    result["summary"] = {
        "total_checks": 9,
        "passed_checks": sum([
            result["details"]["length_valid"],
            result["details"]["format_valid"],
            result["details"]["character_valid"],
            result["details"]["dns_check"] or not check_dns,
            result["details"]["mx_records"] is not False or not check_mx_records
        ]),
        "error_count": len(result["errors"]),
        "warning_count": len(result["warnings"])
    }
    
    return result


# Additional helper functions
def validate_email_list(
    emails: List[str],
    **kwargs
) -> Dict[str, Union[List, Dict]]:
    """
    Validate a list of email addresses.
    
    Args:
        emails: List of email addresses to validate
        **kwargs: Additional arguments passed to validate_email_comprehensive
        
    Returns:
        Dictionary with validation results for each email
    """
    results = {
        "total_emails": len(emails),
        "valid_emails": [],
        "invalid_emails": [],
        "detailed_results": [],
        "summary": {
            "valid_count": 0,
            "invalid_count": 0,
            "unique_domains": set()
        }
    }
    
    for email in emails:
        validation_result = validate_email_comprehensive(email, **kwargs)
        results["detailed_results"].append(validation_result)
        
        if validation_result["is_valid"]:
            results["valid_emails"].append(email)
            results["summary"]["valid_count"] += 1
            if "domain_part" in validation_result["details"]:
                results["summary"]["unique_domains"].add(validation_result["details"]["domain_part"])
        else:
            results["invalid_emails"].append({
                "email": email,
                "errors": validation_result["errors"]
            })
            results["summary"]["invalid_count"] += 1
    
    results["summary"]["unique_domains"] = list(results["summary"]["unique_domains"])
    
    return results


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address
        
    Returns:
        Domain part or None if invalid
    """
    result = validate_email_comprehensive(email, additional_checks=False)
    if result["is_valid"]:
        return result["details"]["domain_part"]
    return None


def is_email_provider_known(email: str, known_providers: List[str] = None) -> bool:
    """
    Check if email is from a known provider.
    
    Args:
        email: Email address to check
        known_providers: List of known providers (default: common providers)
        
    Returns:
        True if email is from known provider
    """
    if known_providers is None:
        known_providers = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'icloud.com', 'aol.com', 'protonmail.com', 'zoho.com',
            'mail.com', 'yandex.com', 'gmx.com'
        ]
    
    domain = extract_domain_from_email(email)
    if domain:
        return domain.lower() in [p.lower() for p in known_providers]
    
    return False