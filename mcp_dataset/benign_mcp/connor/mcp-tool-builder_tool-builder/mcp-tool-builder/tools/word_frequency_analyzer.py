def word_frequency_analyzer(file_path, ignore_stopwords=False, case_sensitive=False, min_word_length=1):
    """
    Enhanced word frequency analyzer with text cleaning, stop word filtering, and detailed statistics.
    
    Args:
        file_path: Path to the text file to analyze
        ignore_stopwords: If True, common stop words will be ignored (default: False)
        case_sensitive: If True, words are case-sensitive (default: False)
        min_word_length: Minimum word length to include (default: 1)
        
    Returns:
        A dictionary containing:
        - total_words: Total number of words in the file
        - unique_words: Number of unique words
        - word_frequencies: Dictionary of word frequencies
        - most_common: List of most common words with counts
        - longest_words: List of longest words found
        - average_word_length: Average length of words
        - statistics: Various text statistics
        - error: Error message if any (None if successful)
    """
    
    import re
    import os
    from collections import Counter
    
    result = {
        "total_words": 0,
        "unique_words": 0,
        "word_frequencies": {},
        "most_common": [],
        "longest_words": [],
        "average_word_length": 0,
        "statistics": {},
        "error": None
    }
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        if not text.strip():
            raise ValueError("File is empty or contains only whitespace")
        
        # Common English stop words
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'down', 'out', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
            'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
            'should', 'now', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
            'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would',
            'should', 'could', 'ought', 'i\'m', 'you\'re', 'he\'s', 'she\'s',
            'it\'s', 'we\'re', 'they\'re', 'i\'ve', 'you\'ve', 'we\'ve', 'they\'ve',
            'i\'d', 'you\'d', 'he\'d', 'she\'d', 'we\'d', 'they\'d', 'i\'ll',
            'you\'ll', 'he\'ll', 'she\'ll', 'we\'ll', 'they\'ll', 'isn\'t',
            'aren\'t', 'wasn\'t', 'weren\'t', 'hasn\'t', 'haven\'t', 'hadn\'t',
            'doesn\'t', 'don\'t', 'didn\'t', 'won\'t', 'wouldn\'t', 'shan\'t',
            'shouldn\'t', 'can\'t', 'cannot', 'couldn\'t', 'mustn\'t', 'let\'s',
            'that\'s', 'who\'s', 'what\'s', 'here\'s', 'there\'s', 'when\'s',
            'where\'s', 'why\'s', 'how\'s'
        }
        
        # Clean and tokenize text
        # Remove punctuation and special characters, keep apostrophes for contractions
        cleaned_text = re.sub(r'[^\w\s\']', ' ', text)
        
        # Split into words
        if case_sensitive:
            words = cleaned_text.split()
        else:
            words = cleaned_text.lower().split()
        
        # Filter words based on criteria
        filtered_words = []
        for word in words:
            # Remove apostrophes from start/end for better matching
            clean_word = word.strip("'")
            
            # Check minimum length
            if len(clean_word) < min_word_length:
                continue
            
            # Check stop words
            if ignore_stopwords and clean_word in stop_words:
                continue
            
            filtered_words.append(clean_word)
        
        if not filtered_words:
            raise ValueError("No words found after applying filters")
        
        # Count word frequencies
        word_counter = Counter(filtered_words)
        
        # Calculate statistics
        total_words = len(filtered_words)
        unique_words = len(word_counter)
        
        # Calculate average word length
        total_characters = sum(len(word) for word in filtered_words)
        average_word_length = total_characters / total_words if total_words > 0 else 0
        
        # Find most common words (top 20)
        most_common = word_counter.most_common(20)
        
        # Find longest words (top 10)
        longest_words = sorted(word_counter.keys(), key=len, reverse=True)[:10]
        
        # Calculate word length distribution
        word_length_dist = {}
        for word in word_counter:
            length = len(word)
            word_length_dist[length] = word_length_dist.get(length, 0) + 1
        
        # Prepare result
        result["total_words"] = total_words
        result["unique_words"] = unique_words
        result["word_frequencies"] = dict(word_counter)
        result["most_common"] = most_common
        result["longest_words"] = longest_words
        result["average_word_length"] = round(average_word_length, 2)
        
        # Additional statistics
        result["statistics"] = {
            "word_length_distribution": dict(sorted(word_length_dist.items())),
            "vocabulary_richness": round(unique_words / total_words * 100, 2) if total_words > 0 else 0,
            "most_common_word": most_common[0] if most_common else None,
            "longest_word": longest_words[0] if longest_words else None,
            "file_size_bytes": os.path.getsize(file_path),
            "character_count": len(text),
            "line_count": len(text.splitlines()),
            "sentence_count": len(re.split(r'[.!?]+', text)) - 1
        }
        
    except Exception as e:
        result["error"] = str(e)
    
    return result