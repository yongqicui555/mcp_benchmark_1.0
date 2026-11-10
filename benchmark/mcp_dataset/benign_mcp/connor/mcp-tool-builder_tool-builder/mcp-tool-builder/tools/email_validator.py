import re
from typing import List, Optional

def email_validator(email: str, check_dns: bool = False) -> dict:
    """
    Validate email addresses against standard format rules.
    
    Args:
        email: Email address to validate
        check_dns: If True, also checks if domain has valid MX records (requires internet connection)
        
    Returns:
        dict: Contains validation results and detailed analysis
    """
    # RFC 5322 compliant email regex pattern (simplified version)
    # This pattern covers most common email formats
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Common disposable/temporary email domains
    disposable_domains = [
        'tempmail.com', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'sharklasers.com', 'yopmail.com',
        'throwawaymail.com', 'fakeinbox.com', 'temp-mail.org',
        'trashmail.com', 'mohmal.com', 'dispostable.com'
    ]
    
    results = {
        "email": email,
        "is_valid_format": False,
        "is_valid_dns": None,
        "is_disposable": False,
        "domain": None,
        "username": None,
        "tld": None,
        "validation_checks": {},
        "suggestions": []
    }
    
    # Check basic format
    if not email or not isinstance(email, str):
        results["validation_checks"]["non_empty_string"] = False
        results["suggestions"].append("Email must be a non-empty string")
        return results
    
    results["validation_checks"]["non_empty_string"] = True
    
    # Check length constraints
    if len(email) > 254:  # RFC 5321 specifies maximum 254 characters
        results["validation_checks"]["max_length"] = False
        results["suggestions"].append("Email address too long (max 254 characters)")
        return results
    results["validation_checks"]["max_length"] = True
    
    # Check for @ symbol
    if '@' not in email:
        results["validation_checks"]["has_at_symbol"] = False
        results["suggestions"].append("Email must contain '@' symbol")
        return results
    
    results["validation_checks"]["has_at_symbol"] = True
    
    # Split email into username and domain
    parts = email.split('@')
    if len(parts) != 2:
        results["validation_checks"]["single_at_symbol"] = False
        results["suggestions"].append("Email must contain exactly one '@' symbol")
        return results
    
    username, domain = parts
    results["username"] = username
    results["domain"] = domain
    
    # Validate username
    if not username:
        results["validation_checks"]["username_non_empty"] = False
        results["suggestions"].append("Username part cannot be empty")
        return results
    results["validation_checks"]["username_non_empty"] = True
    
    if len(username) > 64:  # RFC 5321 specifies maximum 64 characters for local part
        results["validation_checks"]["username_max_length"] = False
        results["suggestions"].append("Username too long (max 64 characters)")
        return results
    results["validation_checks"]["username_max_length"] = True
    
    # Validate domain
    if not domain:
        results["validation_checks"]["domain_non_empty"] = False
        results["suggestions"].append("Domain part cannot be empty")
        return results
    results["validation_checks"]["domain_non_empty"] = True
    
    # Check for dot in domain
    if '.' not in domain:
        results["validation_checks"]["domain_has_dot"] = False
        results["suggestions"].append("Domain must contain at least one '.'")
        return results
    results["validation_checks"]["domain_has_dot"] = True
    
    # Extract TLD
    domain_parts = domain.split('.')
    if len(domain_parts) < 2:
        results["validation_checks"]["valid_tld_structure"] = False
        results["suggestions"].append("Domain must have at least one subdomain and TLD")
        return results
    
    tld = domain_parts[-1]
    results["tld"] = tld
    
    # Check TLD length
    if len(tld) < 2:
        results["validation_checks"]["tld_min_length"] = False
        results["suggestions"].append("TLD must be at least 2 characters")
        return results
    results["validation_checks"]["tld_min_length"] = True
    
    # Apply regex pattern
    if not re.match(email_pattern, email):
        results["validation_checks"]["regex_pattern"] = False
        results["suggestions"].append("Email format is invalid")
        return results
    
    results["validation_checks"]["regex_pattern"] = True
    results["is_valid_format"] = True
    
    # Check for disposable email domains
    domain_lower = domain.lower()
    for disposable_domain in disposable_domains:
        if domain_lower.endswith(disposable_domain):
            results["is_disposable"] = True
            results["suggestions"].append("Email uses a disposable/temporary domain")
            break
    
    # Optional DNS check for MX records
    if check_dns:
        try:
            import socket
            import dns.resolver
            
            # Try to resolve MX records for the domain
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                results["is_valid_dns"] = len(mx_records) > 0
                if not results["is_valid_dns"]:
                    results["suggestions"].append("Domain does not have MX records configured")
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
                results["is_valid_dns"] = False
                results["suggestions"].append("Domain does not exist or has no MX records")
        except ImportError:
            results["is_valid_dns"] = None
            results["suggestions"].append("DNS check requires dnspython library (pip install dnspython)")
        except Exception as e:
            results["is_valid_dns"] = None
            results["suggestions"].append(f"DNS check failed: {str(e)}")
    
    return results