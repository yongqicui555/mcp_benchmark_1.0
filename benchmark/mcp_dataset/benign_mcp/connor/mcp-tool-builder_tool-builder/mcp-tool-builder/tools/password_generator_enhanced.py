def password_generator_enhanced(length=16, include_uppercase=True, include_lowercase=True, 
                               include_digits=True, include_symbols=True, exclude_similar=True, 
                               exclude_ambiguous=True, custom_symbols=None, num_passwords=1,
                               strength_analysis=True):
    """
    Enhanced password generator with multiple character sets, strength analysis, and security features.
    
    Args:
        length: Password length (default: 16, min: 8, max: 128)
        include_uppercase: Include uppercase letters A-Z (default: True)
        include_lowercase: Include lowercase letters a-z (default: True)
        include_digits: Include digits 0-9 (default: True)
        include_symbols: Include symbols !@#$%^&* etc. (default: True)
        exclude_similar: Exclude similar characters like i, l, 1, o, 0 (default: True)
        exclude_ambiguous: Exclude ambiguous symbols like {}[]()\/'"`~,;:.<> (default: True)
        custom_symbols: Custom symbol string to use instead of default symbols (optional)
        num_passwords: Number of passwords to generate (default: 1, max: 20)
        strength_analysis: Include password strength analysis (default: True)
        
    Returns:
        A dictionary containing:
        - passwords: List of generated passwords
        - parameters: The parameters used for generation
        - strength_analysis: Dictionary with strength metrics for each password
        - entropy_bits: Estimated entropy in bits for each password
        - generation_time: Time taken to generate passwords
        - error: Error message if any (None if successful)
    """
    
    import random
    import string
    import time
    import re
    import math
    
    result = {
        "passwords": [],
        "parameters": {},
        "strength_analysis": {},
        "entropy_bits": [],
        "generation_time": 0,
        "error": None
    }
    
    try:
        start_time = time.time()
        
        # Validate parameters
        if length < 8:
            raise ValueError("Password length must be at least 8 characters")
        if length > 128:
            raise ValueError("Password length cannot exceed 128 characters")
        if num_passwords < 1:
            raise ValueError("Number of passwords must be at least 1")
        if num_passwords > 20:
            raise ValueError("Number of passwords cannot exceed 20")
        
        # Check that at least one character set is selected
        if not any([include_uppercase, include_lowercase, include_digits, include_symbols]):
            raise ValueError("At least one character set must be selected")
        
        # Store parameters
        result["parameters"] = {
            "length": length,
            "include_uppercase": include_uppercase,
            "include_lowercase": include_lowercase,
            "include_digits": include_digits,
            "include_symbols": include_symbols,
            "exclude_similar": exclude_similar,
            "exclude_ambiguous": exclude_ambiguous,
            "custom_symbols": custom_symbols,
            "num_passwords": num_passwords
        }
        
        # Define character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        
        # Default symbols (common password symbols)
        default_symbols = "!@#$%^&*"
        
        # Symbols to exclude if exclude_ambiguous is True
        ambiguous_symbols = "{}[]()\/'\"`~,;:.<>"
        
        # Characters to exclude if exclude_similar is True
        similar_chars = {
            'uppercase': 'IO',
            'lowercase': 'il',
            'digits': '01'
        }
        
        # Filter character sets based on options
        if exclude_similar:
            uppercase = ''.join(c for c in uppercase if c not in similar_chars['uppercase'])
            lowercase = ''.join(c for c in lowercase if c not in similar_chars['lowercase'])
            digits = ''.join(c for c in digits if c not in similar_chars['digits'])
        
        # Prepare symbol set
        if custom_symbols:
            symbols = custom_symbols
        else:
            symbols = default_symbols
        
        if exclude_ambiguous:
            symbols = ''.join(c for c in symbols if c not in ambiguous_symbols)
        
        # Build the character pool
        char_pool = ""
        char_sets = []
        
        if include_uppercase and uppercase:
            char_pool += uppercase
            char_sets.append(("uppercase", uppercase))
        
        if include_lowercase and lowercase:
            char_pool += lowercase
            char_sets.append(("lowercase", lowercase))
        
        if include_digits and digits:
            char_pool += digits
            char_sets.append(("digits", digits))
        
        if include_symbols and symbols:
            char_pool += symbols
            char_sets.append(("symbols", symbols))
        
        if not char_pool:
            raise ValueError("Character pool is empty after applying filters")
        
        # Generate passwords
        passwords = []
        entropy_list = []
        strength_dict = {}
        
        for i in range(num_passwords):
            # Ensure at least one character from each selected set
            password_chars = []
            
            # Add one character from each selected character set
            for set_name, chars in char_sets:
                password_chars.append(random.choice(chars))
            
            # Fill the rest with random characters from the pool
            remaining_length = length - len(password_chars)
            if remaining_length > 0:
                password_chars.extend(random.choices(char_pool, k=remaining_length))
            
            # Shuffle the characters
            random.shuffle(password_chars)
            password = ''.join(password_chars)
            passwords.append(password)
            
            # Calculate entropy
            pool_size = len(char_pool)
            entropy = length * math.log2(pool_size)
            entropy_list.append(round(entropy, 2))
            
            # Strength analysis
            if strength_analysis:
                strength = analyze_password_strength(password)
                strength_dict[f"password_{i+1}"] = strength
        
        # Store results
        result["passwords"] = passwords
        result["entropy_bits"] = entropy_list
        
        if strength_analysis:
            result["strength_analysis"] = strength_dict
        
        result["generation_time"] = round(time.time() - start_time, 4)
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def analyze_password_strength(password):
    """
    Analyze password strength based on multiple criteria.
    
    Args:
        password: The password to analyze
        
    Returns:
        Dictionary with strength metrics and score
    """
    
    analysis = {
        "length": len(password),
        "has_uppercase": bool(re.search(r'[A-Z]', password)),
        "has_lowercase": bool(re.search(r'[a-z]', password)),
        "has_digits": bool(re.search(r'\d', password)),
        "has_symbols": bool(re.search(r'[^A-Za-z0-9]', password)),
        "unique_chars": len(set(password)),
        "score": 0,
        "strength": "Very Weak",
        "recommendations": []
    }
    
    # Calculate score (0-100)
    score = 0
    
    # Length score (max 30 points)
    length = len(password)
    if length >= 8:
        score += 10
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10
    
    # Character variety score (max 40 points)
    if analysis["has_uppercase"]:
        score += 10
    if analysis["has_lowercase"]:
        score += 10
    if analysis["has_digits"]:
        score += 10
    if analysis["has_symbols"]:
        score += 10
    
    # Uniqueness score (max 30 points)
    uniqueness = analysis["unique_chars"] / length
    if uniqueness >= 0.5:
        score += 10
    if uniqueness >= 0.75:
        score += 10
    if uniqueness >= 0.9:
        score += 10
    
    # Adjust score based on patterns
    # Check for common patterns
    if re.search(r'(.)\1{2,}', password):  # Repeated characters
        score -= 10
    
    if re.search(r'(012|123|234|345|456|567|678|789|890)', password):  # Sequential numbers
        score -= 10
    
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password, re.IGNORECASE):  # Sequential letters
        score -= 10
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    # Determine strength level
    if score >= 80:
        strength = "Very Strong"
    elif score >= 60:
        strength = "Strong"
    elif score >= 40:
        strength = "Good"
    elif score >= 20:
        strength = "Weak"
    else:
        strength = "Very Weak"
    
    analysis["score"] = score
    analysis["strength"] = strength
    
    # Generate recommendations
    if length < 12:
        analysis["recommendations"].append("Use longer passwords (at least 12 characters)")
    
    if not analysis["has_uppercase"]:
        analysis["recommendations"].append("Include uppercase letters")
    
    if not analysis["has_lowercase"]:
        analysis["recommendations"].append("Include lowercase letters")
    
    if not analysis["has_digits"]:
        analysis["recommendations"].append("Include numbers")
    
    if not analysis["has_symbols"]:
        analysis["recommendations"].append("Include symbols")
    
    if analysis["unique_chars"] / length < 0.7:
        analysis["recommendations"].append("Use more diverse characters")
    
    return analysis