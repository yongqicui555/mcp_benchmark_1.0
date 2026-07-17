import re
import socket
from typing import Dict, List, Tuple, Optional

def email_regex_validator(email: str, check_format: bool = True, check_dns: bool = False, 
                         check_mx: bool = False, detailed_report: bool = True) -> Dict:
    """
    Validates email addresses using regular expressions with optional DNS and MX record checks.
    
    Args:
        email (str): The email address to validate
        check_format (bool): Check email format using regex (default: True)
        check_dns (bool): Check if domain has valid DNS records (default: False)
        check_mx (bool): Check if domain has MX records (default: False)
        detailed_report (bool): Return detailed validation report (default: True)
    
    Returns:
        dict: Validation results with detailed information
    """
    
    result = {
        'email': email,
        'is_valid': False,
        'validation_steps': {},
        'errors': [],
        'warnings': [],
        'suggestions': []
    }
    
    # Step 1: Basic format validation
    if check_format:
        format_valid, format_details = _validate_email_format(email)
        result['validation_steps']['format_validation'] = format_details
        
        if not format_valid:
            result['errors'].extend(format_details.get('errors', []))
            result['warnings'].extend(format_details.get('warnings', []))
            
            if detailed_report:
                return _format_detailed_result(result)
            else:
                result['is_valid'] = False
                return result
    
    # Step 2: Extract domain for further checks
    domain = email.split('@')[-1] if '@' in email else ''
    
    # Step 3: DNS validation (if requested)
    if check_dns:
        dns_valid, dns_details = _validate_dns(domain)
        result['validation_steps']['dns_validation'] = dns_details
        
        if not dns_valid:
            result['errors'].extend(dns_details.get('errors', []))
            result['warnings'].extend(dns_details.get('warnings', []))
    
    # Step 4: MX record validation (if requested)
    if check_mx:
        mx_valid, mx_details = _validate_mx_records(domain)
        result['validation_steps']['mx_validation'] = mx_details
        
        if not mx_valid:
            result['warnings'].extend(mx_details.get('warnings', []))
            # MX records are warning, not error (some domains use A records)
    
    # Determine overall validity
    format_ok = result['validation_steps'].get('format_validation', {}).get('is_valid', False)
    dns_ok = not check_dns or result['validation_steps'].get('dns_validation', {}).get('is_valid', False)
    
    result['is_valid'] = format_ok and dns_ok
    
    # Add suggestions for common issues
    _add_suggestions(result, email)
    
    if detailed_report:
        return _format_detailed_result(result)
    else:
        return {
            'email': email,
            'is_valid': result['is_valid'],
            'has_errors': len(result['errors']) > 0,
            'has_warnings': len(result['warnings']) > 0
        }

def _validate_email_format(email: str) -> Tuple[bool, Dict]:
    """Validate email format using comprehensive regex patterns."""
    
    details = {
        'is_valid': False,
        'checks': {},
        'errors': [],
        'warnings': []
    }
    
    # Comprehensive email regex pattern (RFC 5322 compliant)
    # This pattern is more comprehensive than simple validation
    email_pattern = r"""
        ^                       # Start of string
        [a-zA-Z0-9]             # Must start with alphanumeric
        (                       # Local part
          [a-zA-Z0-9._%+-]*     # Alphanumeric, dots, underscores, etc.
          [a-zA-Z0-9]           # Must end with alphanumeric
        )?                      # Optional (for very short emails)
        @                       # @ symbol
        [a-zA-Z0-9.-]+          # Domain part
        \.                      # Dot
        [a-zA-Z]{2,}            # TLD (2+ characters)
        $                       # End of string
    """
    
    # Simplified pattern for quick validation
    simple_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Check 1: Basic structure
    if not email or not isinstance(email, str):
        details['errors'].append("Email is empty or not a string")
        return False, details
    
    # Check 2: Contains @ symbol
    if '@' not in email:
        details['errors'].append("Email must contain @ symbol")
        details['checks']['has_at_symbol'] = False
        return False, details
    details['checks']['has_at_symbol'] = True
    
    # Check 3: Split into local and domain parts
    parts = email.split('@')
    if len(parts) != 2:
        details['errors'].append("Email must contain exactly one @ symbol")
        return False, details
    
    local_part, domain_part = parts
    details['local_part'] = local_part
    details['domain_part'] = domain_part
    
    # Check 4: Local part validation
    if not local_part:
        details['errors'].append("Local part (before @) cannot be empty")
    elif len(local_part) > 64:
        details['errors'].append("Local part exceeds maximum length of 64 characters")
    elif local_part.startswith('.') or local_part.endswith('.'):
        details['errors'].append("Local part cannot start or end with a dot")
    elif '..' in local_part:
        details['errors'].append("Local part cannot contain consecutive dots")
    
    # Check 5: Domain part validation
    if not domain_part:
        details['errors'].append("Domain part (after @) cannot be empty")
    elif len(domain_part) > 255:
        details['errors'].append("Domain part exceeds maximum length of 255 characters")
    elif '.' not in domain_part:
        details['errors'].append("Domain must contain at least one dot")
    elif domain_part.startswith('.') or domain_part.endswith('.'):
        details['errors'].append("Domain cannot start or end with a dot")
    elif '..' in domain_part:
        details['errors'].append("Domain cannot contain consecutive dots")
    
    # Check 6: Regex validation
    if not re.match(simple_pattern, email, re.IGNORECASE):
        details['errors'].append("Email format is invalid")
        details['checks']['regex_validation'] = False
    else:
        details['checks']['regex_validation'] = True
    
    # Check 7: Common issues (warnings)
    if local_part and local_part[0].isdigit():
        details['warnings'].append("Local part starts with a number (may be rejected by some systems)")
    
    if '_' in local_part:
        details['warnings'].append("Underscore in local part (may cause issues with some systems)")
    
    # Check for disposable email domains (common pattern)
    disposable_domains = ['tempmail', '10minutemail', 'throwaway', 'guerrillamail', 'mailinator']
    if any(disposable in domain_part.lower() for disposable in disposable_domains):
        details['warnings'].append("Email domain appears to be disposable/temporary")
    
    # Determine overall format validity
    details['is_valid'] = len(details['errors']) == 0
    
    return details['is_valid'], details

def _validate_dns(domain: str) -> Tuple[bool, Dict]:
    """Check if domain has valid DNS records."""
    
    details = {
        'is_valid': False,
        'domain': domain,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Try to resolve the domain
        ip_address = socket.gethostbyname(domain)
        details['ip_address'] = ip_address
        details['is_valid'] = True
        details['checks'] = {'dns_resolution': 'success'}
        
    except socket.gaierror:
        details['errors'].append(f"Domain '{domain}' does not have valid DNS records")
        details['checks'] = {'dns_resolution': 'failed'}
    
    except Exception as e:
        details['errors'].append(f"DNS check failed: {str(e)}")
        details['checks'] = {'dns_resolution': 'error'}
    
    return details['is_valid'], details

def _validate_mx_records(domain: str) -> Tuple[bool, Dict]:
    """Check if domain has MX records for email delivery."""
    
    details = {
        'has_mx': False,
        'domain': domain,
        'mx_records': [],
        'warnings': []
    }
    
    try:
        import dns.resolver
        mx_records = dns.resolver.resolve(domain, 'MX')
        
        if mx_records:
            details['has_mx'] = True
            for mx in mx_records:
                details['mx_records'].append({
                    'preference': mx.preference,
                    'exchange': str(mx.exchange)
                })
        else:
            details['warnings'].append(f"Domain '{domain}' has no MX records (may use A records instead)")
    
    except dns.resolver.NoAnswer:
        details['warnings'].append(f"Domain '{domain}' has no MX records")
    
    except dns.resolver.NXDOMAIN:
        details['warnings'].append(f"Domain '{domain}' does not exist")
    
    except Exception as e:
        details['warnings'].append(f"MX record check failed: {str(e)}")
    
    return details['has_mx'], details

def _add_suggestions(result: Dict, email: str) -> None:
    """Add helpful suggestions based on validation results."""
    
    if not result['is_valid']:
        # Check for common typos
        if 'gmail' in email.lower() and 'gmial' in email.lower():
            result['suggestions'].append("Did you mean 'gmail.com' instead of 'gmial.com'?")
        
        if 'hotmail' in email.lower() and 'hotmal' in email.lower():
            result['suggestions'].append("Did you mean 'hotmail.com' instead of 'hotmal.com'?")
        
        if 'yahoo' in email.lower() and 'yaho' in email.lower():
            result['suggestions'].append("Did you mean 'yahoo.com' instead of 'yaho.com'?")
        
        # Suggest fixing case issues
        if email != email.lower():
            result['suggestions'].append("Email addresses are case-insensitive. Consider using lowercase.")
    
    # Suggest using common providers if domain looks suspicious
    domain = email.split('@')[-1] if '@' in email else ''
    suspicious_tlds = ['.xyz', '.top', '.club', '.online', '.site']
    if any(domain.endswith(tld) for tld in suspicious_tlds):
        result['suggestions'].append("Consider using a well-known email provider for better deliverability.")

def _format_detailed_result(result: Dict) -> Dict:
    """Format the result for detailed reporting."""
    
    formatted = {
        'email': result['email'],
        'overall_validity': result['is_valid'],
        'summary': {
            'has_errors': len(result['errors']) > 0,
            'has_warnings': len(result['warnings']) > 0,
            'error_count': len(result['errors']),
            'warning_count': len(result['warnings']),
            'suggestion_count': len(result['suggestions'])
        }
    }
    
    if result['errors']:
        formatted['errors'] = result['errors']
    
    if result['warnings']:
        formatted['warnings'] = result['warnings']
    
    if result['suggestions']:
        formatted['suggestions'] = result['suggestions']
    
    # Add validation steps if available
    if result['validation_steps']:
        formatted['validation_details'] = result['validation_steps']
    
    return formatted

def test_email_validator():
    """Test the email validator with various examples."""
    
    test_emails = [
        # Valid emails
        ("user@example.com", "Standard valid email"),
        ("first.last@company.co.uk", "Valid with subdomain and country TLD"),
        ("user123@domain.org", "Valid with numbers"),
        ("user.name+tag@domain.com", "Valid with plus addressing"),
        
        # Invalid emails
        ("invalid-email", "Missing @ symbol"),
        ("user@.com", "Domain starts with dot"),
        ("user@com.", "Domain ends with dot"),
        ("@domain.com", "Missing local part"),
        ("user@domain", "Missing TLD"),
        ("user@domain.c", "TLD too short"),
        ("user name@domain.com", "Space in email"),
        ("user@-domain.com", "Domain starts with hyphen"),
        
        # Edge cases
        ("USER@DOMAIN.COM", "Uppercase (valid but warning)"),
        ("123@domain.com", "Local part starts with number (warning)"),
        ("user_name@domain.com", "Underscore in local part (warning)"),
    ]
    
    print("Email Regex Validator - Test Results")
    print("=" * 60)
    
    for email, description in test_emails:
        print(f"\nTest: {description}")
        print(f"Email: {email}")
        
        # Basic validation
        result = email_regex_validator(email, detailed_report=False)
        status = "✓ VALID" if result['is_valid'] else "✗ INVALID"
        print(f"Status: {status}")
        
        # Detailed validation for interesting cases
        if not result['is_valid'] or 'warning' in description.lower():
            detailed = email_regex_validator(email, detailed_report=True)
            
            if detailed.get('errors'):
                print("Errors:", ', '.join(detailed['errors']))
            
            if detailed.get('warnings'):
                print("Warnings:", ', '.join(detailed['warnings']))
    
    print("\n" + "=" * 60)
    print("Validation complete!")

# If run directly, execute tests
if __name__ == "__main__":
    test_email_validator()