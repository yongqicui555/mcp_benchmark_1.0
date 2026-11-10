import secrets
import string
from typing import Optional, Dict

def password_generator(
    length: int = 12,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
    exclude_similar: bool = True,
    exclude_ambiguous: bool = False
) -> dict:
    """
    Generate a secure random password with specified characteristics.
    
    Args:
        length: Length of password to generate (default: 12)
        include_uppercase: Include uppercase letters A-Z (default: True)
        include_lowercase: Include lowercase letters a-z (default: True)
        include_digits: Include digits 0-9 (default: True)
        include_symbols: Include symbols !@#$%^&* etc. (default: True)
        exclude_similar: Exclude similar characters like i, l, 1, I, o, 0, O (default: True)
        exclude_ambiguous: Exclude ambiguous symbols like {}[]()\/'"`~,;:.<> (default: False)
        
    Returns:
        dict: Contains generated password and generation details
        
    Raises:
        ValueError: If no character sets are selected or length is invalid
    """
    # Validate length
    if length < 4:
        raise ValueError("Password length must be at least 4 characters")
    if length > 128:
        raise ValueError("Password length cannot exceed 128 characters")
    
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    symbols = string.punctuation
    
    # Characters to exclude if requested
    similar_chars = "il1ILo0O"
    ambiguous_symbols = "{}[]()\/'\"`~,;:.<>"
    
    # Apply exclusions
    if exclude_similar:
        uppercase = ''.join(c for c in uppercase if c not in similar_chars)
        lowercase = ''.join(c for c in lowercase if c not in similar_chars)
        digits = ''.join(c for c in digits if c not in similar_chars)
    
    if exclude_ambiguous:
        symbols = ''.join(c for c in symbols if c not in ambiguous_symbols)
    
    # Build character pool based on selections
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
    
    # Validate character pool
    if not char_pool:
        raise ValueError("At least one character set must be selected")
    
    # Ensure we have enough characters for the requested length
    if len(char_pool) < length:
        raise ValueError(f"Character pool size ({len(char_pool)}) is smaller than requested length ({length})")
    
    # Generate password ensuring at least one character from each selected set
    password_chars = []
    
    # First, ensure at least one character from each selected set
    for set_name, chars in char_sets:
        password_chars.append(secrets.choice(chars))
    
    # Fill remaining characters randomly from the full pool
    remaining_length = length - len(password_chars)
    if remaining_length > 0:
        password_chars.extend(secrets.choice(char_pool) for _ in range(remaining_length))
    
    # Shuffle the password to randomize position of required characters
    secrets.SystemRandom().shuffle(password_chars)
    
    password = ''.join(password_chars)
    
    # Calculate password strength metrics
    pool_size = len(char_pool)
    possible_combinations = pool_size ** length
    entropy_bits = length * (pool_size.bit_length() - 1)  # Approximate entropy in bits
    
    # Strength classification
    if entropy_bits < 40:
        strength = "Very Weak"
    elif entropy_bits < 60:
        strength = "Weak"
    elif entropy_bits < 80:
        strength = "Moderate"
    elif entropy_bits < 100:
        strength = "Strong"
    else:
        strength = "Very Strong"
    
    # Character count breakdown
    char_counts = {
        "uppercase": sum(1 for c in password if c in uppercase) if include_uppercase else 0,
        "lowercase": sum(1 for c in password if c in lowercase) if include_lowercase else 0,
        "digits": sum(1 for c in password if c in digits) if include_digits else 0,
        "symbols": sum(1 for c in password if c in symbols) if include_symbols else 0,
        "total": length
    }
    
    return {
        "password": password,
        "length": length,
        "character_pool_size": pool_size,
        "possible_combinations": possible_combinations,
        "entropy_bits": entropy_bits,
        "strength": strength,
        "character_counts": char_counts,
        "settings": {
            "include_uppercase": include_uppercase,
            "include_lowercase": include_lowercase,
            "include_digits": include_digits,
            "include_symbols": include_symbols,
            "exclude_similar": exclude_similar,
            "exclude_ambiguous": exclude_ambiguous
        }
    }