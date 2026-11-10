def enhanced_email_validator(email, check_disposable=True, check_common_domains=True, suggest_corrections=True):
    """
    Enhanced email validator with comprehensive format checking and validation features.
    
    Args:
        email: Email address string to validate
        check_disposable: Check if email is from a disposable/temporary email service (default: True)
        check_common_domains: Check if domain is from common email providers (default: True)
        suggest_corrections: Suggest corrections for common typos (default: True)
    
    Returns:
        Dictionary with detailed validation results and suggestions
    """
    import re
    import socket
    
    # Common disposable/temporary email domains
    disposable_domains = {
        'mailinator.com', 'guerrillamail.com', 'sharklasers.com', 'grr.la',
        'guerrillamail.net', 'guerrillamail.org', 'guerrillamail.biz',
        'spam4.me', 'fakeinbox.com', 'yopmail.com', 'tempmail.com',
        'temp-mail.org', 'trashmail.com', 'getairmail.com', 'maildrop.cc',
        '10minutemail.com', 'dispostable.com', 'mailnesia.com',
        'throwawaymail.com', 'tempail.com', 'mailmetrash.com',
        'tmpmail.org', 'mail.tm', 'moakt.com', '33mail.com',
        'anonbox.net', 'jetable.org', 'mailcatch.com'
    }
    
    # Common legitimate email providers
    common_providers = {
        'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'aol.com',
        'icloud.com', 'protonmail.com', 'zoho.com', 'yandex.com', 'mail.com',
        'gmx.com', 'live.com', 'msn.com', 'me.com', 'mac.com', 'inbox.com'
    }
    
    # Common TLDs (Top Level Domains)
    common_tlds = {
        'com', 'org', 'net', 'edu', 'gov', 'mil', 'io', 'co', 'uk', 'de',
        'fr', 'jp', 'cn', 'ru', 'br', 'it', 'es', 'nl', 'se', 'no', 'dk',
        'fi', 'pl', 'au', 'ca', 'nz', 'ch', 'at', 'be', 'ie', 'pt', 'gr'
    }
    
    # Common typos and their corrections
    common_typos = {
        'gmial.com': 'gmail.com',
        'gmal.com': 'gmail.com',
        'gmaill.com': 'gmail.com',
        'gmai.com': 'gmail.com',
        'gmail.con': 'gmail.com',
        'gmail.cm': 'gmail.com',
        'gmail.co': 'gmail.com',
        'yahooo.com': 'yahoo.com',
        'yaho.com': 'yahoo.com',
        'yhaoo.com': 'yahoo.com',
        'outlook.cm': 'outlook.com',
        'outlook.con': 'outlook.com',
        'hotmail.cm': 'hotmail.com',
        'hotmail.con': 'hotmail.com'
    }
    
    def validate_format(email_str):
        """Validate email format using RFC 5322 compliant regex"""
        # RFC 5322 compliant regex (simplified version)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email_str))
    
    def parse_email(email_str):
        """Parse email into username and domain components"""
        if '@' in email_str:
            username, domain = email_str.split('@', 1)
            domain_parts = domain.split('.')
            tld = domain_parts[-1] if domain_parts else ''
            return username, domain, tld
        return '', '', ''
    
    def check_dns_mx(domain):
        """Check if domain has MX records (simplified check)"""
        try:
            # Try to get MX records
            mx_records = socket.getaddrinfo(domain, None)
            return True
        except (socket.gaierror, socket.herror):
            return False
    
    def suggest_email_correction(email_str):
        """Suggest corrections for common email typos"""
        username, domain, tld = parse_email(email_str)
        
        suggestions = []
        
        # Check for common domain typos
        if domain in common_typos:
            corrected_domain = common_typos[domain]
            suggestions.append(f"{username}@{corrected_domain}")
        
        # Check for missing @ symbol
        if '@' not in email_str and '.' in email_str:
            # Try to guess where @ should go
            parts = email_str.split('.')
            if len(parts) >= 2:
                # Common pattern: username.domain.tld
                possible_email = f"{parts[0]}@{'.'.join(parts[1:])}"
                if validate_format(possible_email):
                    suggestions.append(possible_email)
        
        # Check for double @
        if email_str.count('@') > 1:
            # Remove extra @ symbols
            parts = email_str.split('@')
            corrected = f"{parts[0]}@{parts[-1]}"
            if validate_format(corrected):
                suggestions.append(corrected)
        
        return suggestions
    
    # Initialize results
    results = {
        'email': email,
        'is_valid_format': False,
        'is_valid_dns': None,
        'is_disposable': False,
        'is_common_provider': False,
        'username': '',
        'domain': '',
        'tld': '',
        'tld_is_common': False,
        'validation_checks': {},
        'suggestions': [],
        'correction_suggestions': [],
        'warnings': [],
        'success': True
    }
    
    try:
        # Basic validation
        if not email or not isinstance(email, str):
            results['success'] = False
            results['error'] = "Email must be a non-empty string"
            return results
        
        email = email.strip()
        results['email'] = email
        
        # Check 1: Non-empty string
        results['validation_checks']['non_empty'] = bool(email)
        
        # Check 2: Maximum length (RFC 5321: 64 chars local part + 255 chars domain = 320 total)
        results['validation_checks']['max_length'] = len(email) <= 320
        
        # Check 3: Contains @ symbol
        has_at_symbol = '@' in email
        results['validation_checks']['has_at_symbol'] = has_at_symbol
        
        if not has_at_symbol:
            results['warnings'].append("Email missing @ symbol")
        
        # Parse email components
        username, domain, tld = parse_email(email)
        results['username'] = username
        results['domain'] = domain
        results['tld'] = tld
        
        # Check 4: Username validation
        results['validation_checks']['username_non_empty'] = bool(username)
        results['validation_checks']['username_max_length'] = len(username) <= 64
        
        # Check 5: Domain validation
        results['validation_checks']['domain_non_empty'] = bool(domain)
        results['validation_checks']['domain_has_dot'] = '.' in domain
        
        # Check 6: TLD validation
        results['validation_checks']['tld_min_length'] = len(tld) >= 2
        results['tld_is_common'] = tld.lower() in common_tlds
        
        # Check 7: Regex format validation
        is_valid_format = validate_format(email)
        results['is_valid_format'] = is_valid_format
        results['validation_checks']['regex_pattern'] = is_valid_format
        
        # Check disposable domains
        if check_disposable and domain:
            domain_lower = domain.lower()
            results['is_disposable'] = domain_lower in disposable_domains
            if results['is_disposable']:
                results['warnings'].append("Email appears to be from a disposable/temporary email service")
        
        # Check common providers
        if check_common_domains and domain:
            domain_lower = domain.lower()
            results['is_common_provider'] = domain_lower in common_providers
        
        # Check DNS MX records (simplified)
        if domain and is_valid_format:
            try:
                results['is_valid_dns'] = check_dns_mx(domain)
                if not results['is_valid_dns']:
                    results['warnings'].append("Domain may not have proper mail server configuration")
            except Exception:
                results['is_valid_dns'] = False
                results['warnings'].append("Could not verify domain DNS configuration")
        
        # Suggest corrections
        if suggest_corrections and not is_valid_format:
            corrections = suggest_email_correction(email)
            results['correction_suggestions'] = corrections
            if corrections:
                results['suggestions'].append(f"Try: {', '.join(corrections)}")
        
        # Overall validation summary
        all_checks_passed = all(results['validation_checks'].values())
        results['overall_valid'] = all_checks_passed and is_valid_format
        
        # Generate summary message
        if results['overall_valid']:
            results['summary'] = f"Email '{email}' is valid"
            if results['is_disposable']:
                results['summary'] += " (but from disposable service)"
            elif results['is_common_provider']:
                results['summary'] += " (common provider)"
        else:
            results['summary'] = f"Email '{email}' is invalid"
            failed_checks = [k for k, v in results['validation_checks'].items() if not v]
            if failed_checks:
                results['summary'] += f" - Failed checks: {', '.join(failed_checks)}"
        
        return results
        
    except Exception as e:
        return {
            'success': False,
            'email': email,
            'error': f"Validation error: {str(e)}"
        }