def advanced_word_frequency_counter(file_path, ignore_stopwords=True, case_sensitive=False, min_word_length=2, top_n=20):
    """
    Advanced word frequency counter with text cleaning and analysis features.
    
    Args:
        file_path: Path to the text file to analyze
        ignore_stopwords: Whether to ignore common stop words (default: True)
        case_sensitive: Whether to treat words as case sensitive (default: False)
        min_word_length: Minimum word length to include (default: 2)
        top_n: Number of top words to return in results (default: 20)
    
    Returns:
        Dictionary with word frequency analysis and statistics
    """
    import re
    import os
    from collections import Counter
    
    # Common English stop words
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'can', 'could', 'may', 'might', 'must', 'shall', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my',
        'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers',
        'ours', 'theirs', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'will', 'would', 'shall', 'should',
        'can', 'could', 'may', 'might', 'must', 'ought', 'from', 'up', 'down',
        'out', 'so', 'then', 'than', 'too', 'very', 'just', 'now', 'also'
    }
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                'error': f"File not found: {file_path}",
                'file_path': file_path,
                'success': False
            }
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        if not text.strip():
            return {
                'error': "File is empty",
                'file_path': file_path,
                'success': False
            }
        
        # Basic file statistics
        file_size = os.path.getsize(file_path)
        lines = text.count('\n') + 1
        characters = len(text)
        words_rough = len(text.split())
        
        # Clean and process the text
        # Remove punctuation and special characters, keep apostrophes for contractions
        text_clean = re.sub(r'[^\w\s\'-]', ' ', text)
        
        # Split into words
        if case_sensitive:
            words = text_clean.split()
        else:
            words = text_clean.lower().split()
        
        # Filter words by minimum length
        words = [word for word in words if len(word) >= min_word_length]
        
        # Remove stop words if requested
        if ignore_stopwords:
            words = [word for word in words if word not in stop_words]
        
        # Count word frequencies
        word_counts = Counter(words)
        total_words = len(words)
        unique_words = len(word_counts)
        
        # Calculate word frequencies as percentages
        word_frequencies = {}
        for word, count in word_counts.items():
            percentage = (count / total_words) * 100
            word_frequencies[word] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        # Get top N words
        top_words = word_counts.most_common(top_n)
        top_words_dict = {}
        for word, count in top_words:
            percentage = (count / total_words) * 100
            top_words_dict[word] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        # Calculate additional statistics
        if total_words > 0:
            avg_word_length = sum(len(word) for word in words) / total_words
            most_common_word, most_common_count = word_counts.most_common(1)[0]
            lexical_density = (unique_words / total_words) * 100
        else:
            avg_word_length = 0
            most_common_word = None
            most_common_count = 0
            lexical_density = 0
        
        # Prepare results
        results = {
            'file_path': file_path,
            'file_size_bytes': file_size,
            'success': True,
            'statistics': {
                'total_lines': lines,
                'total_characters': characters,
                'rough_word_count': words_rough,
                'processed_word_count': total_words,
                'unique_words': unique_words,
                'lexical_density_percent': round(lexical_density, 2),
                'average_word_length': round(avg_word_length, 2),
                'most_common_word': most_common_word,
                'most_common_count': most_common_count
            },
            'processing_options': {
                'ignore_stopwords': ignore_stopwords,
                'case_sensitive': case_sensitive,
                'min_word_length': min_word_length,
                'top_n': top_n
            },
            'top_words': top_words_dict,
            'all_word_counts': dict(word_counts),
            'sample_text_preview': text[:200] + '...' if len(text) > 200 else text
        }
        
        return results
        
    except Exception as e:
        return {
            'error': f"Error processing file: {str(e)}",
            'file_path': file_path,
            'success': False
        }