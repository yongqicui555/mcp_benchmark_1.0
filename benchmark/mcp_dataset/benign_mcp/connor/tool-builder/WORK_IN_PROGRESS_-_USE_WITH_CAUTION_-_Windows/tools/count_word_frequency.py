def count_word_frequency(text):
    """
    Counts word frequency in a given text.
    
    Args:
        text (str): The input text to analyze
        
    Returns:
        dict: A dictionary with words as keys and frequency counts as values,
              or an error message if input is invalid
        
    Examples:
        >>> count_word_frequency("hello world hello")
        {'hello': 2, 'world': 1}
        >>> count_word_frequency("The quick brown fox jumps over the lazy dog")
        {'the': 2, 'quick': 1, 'brown': 1, 'fox': 1, 'jumps': 1, 'over': 1, 'lazy': 1, 'dog': 1}
    """
    try:
        # Validate input is a string
        if not isinstance(text, str):
            return "Error: Input must be a string."
        
        # If empty string, return empty dict
        if not text.strip():
            return {}
        
        # Convert to lowercase and split into words
        # Remove punctuation and split by whitespace
        import re
        
        # Remove punctuation and special characters, keep letters, numbers, and apostrophes
        cleaned_text = re.sub(r'[^\w\s\']', ' ', text.lower())
        
        # Split by whitespace
        words = cleaned_text.split()
        
        # Remove empty strings and single quotes
        words = [word for word in words if word and word != "'"]
        
        # Count frequency
        frequency = {}
        for word in words:
            # Remove leading/trailing apostrophes
            word = word.strip("'")
            if word:  # Check if word is not empty after stripping
                frequency[word] = frequency.get(word, 0) + 1
        
        return frequency
    
    except Exception as e:
        return f"Error counting word frequency: {str(e)}"