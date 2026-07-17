import re
import string
from typing import Dict, List, Tuple, Optional, Union
from collections import Counter
import json

def count_word_frequency_file(
    file_path: str,
    case_sensitive: bool = False,
    include_numbers: bool = False,
    min_word_length: int = 1,
    stop_words: Optional[List[str]] = None,
    custom_delimiters: Optional[str] = None,
    output_limit: Optional[int] = None,
    sort_by: str = "frequency",  # "frequency", "alphabetical", "length"
    sort_order: str = "descending"  # "ascending", "descending"
) -> Dict[str, Union[Dict, List, int, bool, str]]:
    """
    Counts word frequencies in a text file with comprehensive processing options.
    
    Args:
        file_path: Path to the text file to analyze
        case_sensitive: If False, converts all words to lowercase (default: False)
        include_numbers: If True, includes words containing numbers (default: False)
        min_word_length: Minimum word length to include (default: 1)
        stop_words: List of words to exclude from counting
        custom_delimiters: Custom delimiter characters (default: standard word boundaries)
        output_limit: Maximum number of words to return in results (None for all)
        sort_by: How to sort results - "frequency", "alphabetical", or "length"
        sort_order: Sort order - "ascending" or "descending"
        
    Returns:
        Dictionary containing word frequencies and file statistics
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If parameters are invalid
    """
    
    # Default stop words (common English words)
    default_stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
        'should', 'may', 'might', 'must', 'can', 'could', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my',
        'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers',
        'ours', 'theirs', 'this', 'that', 'these', 'those', 'am', 'is',
        'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'will', 'would', 'shall', 'should',
        'may', 'might', 'must', 'can', 'could', 'cannot', 'couldnt'
    }
    
    # Validate parameters
    if min_word_length < 1:
        min_word_length = 1
    
    if sort_by not in ["frequency", "alphabetical", "length"]:
        sort_by = "frequency"
    
    if sort_order not in ["ascending", "descending"]:
        sort_order = "descending"
    
    # Use default stop words if none provided
    if stop_words is None:
        stop_words_set = default_stop_words
    else:
        stop_words_set = set(word.lower() for word in stop_words)
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Get file statistics
        file_stats = {
            "file_path": file_path,
            "total_characters": len(text),
            "total_lines": text.count('\n') + 1,
            "file_size_bytes": len(text.encode('utf-8'))
        }
        
        # If file is empty, return early
        if not text.strip():
            return {
                "success": True,
                "file_stats": file_stats,
                "word_frequencies": {},
                "summary": {
                    "total_words": 0,
                    "unique_words": 0,
                    "most_common_word": None,
                    "most_common_count": 0
                },
                "processing_options": {
                    "case_sensitive": case_sensitive,
                    "include_numbers": include_numbers,
                    "min_word_length": min_word_length,
                    "stop_words_used": len(stop_words_set) > 0,
                    "custom_delimiters": custom_delimiters is not None
                }
            }
        
        # Define word delimiters
        if custom_delimiters:
            # Use custom delimiters
            delimiters_pattern = f"[{re.escape(custom_delimiters)}]+"
        else:
            # Standard word boundaries: punctuation, whitespace, etc.
            delimiters_pattern = r'[\s\W_]+'
        
        # Split text into words
        words = re.split(delimiters_pattern, text)
        
        # Process each word
        processed_words = []
        for word in words:
            # Skip empty strings
            if not word:
                continue
            
            # Apply case sensitivity
            if not case_sensitive:
                word = word.lower()
            
            # Check if we should include numbers
            if not include_numbers and any(char.isdigit() for char in word):
                continue
            
            # Check minimum word length
            if len(word) < min_word_length:
                continue
            
            # Check against stop words
            if word in stop_words_set:
                continue
            
            # Add to processed words
            processed_words.append(word)
        
        # Count word frequencies
        word_counter = Counter(processed_words)
        
        # Get total word count
        total_words = len(processed_words)
        unique_words = len(word_counter)
        
        # Find most common word
        most_common_info = word_counter.most_common(1)
        most_common_word = most_common_info[0][0] if most_common_info else None
        most_common_count = most_common_info[0][1] if most_common_info else 0
        
        # Prepare word frequencies dictionary
        word_frequencies = dict(word_counter)
        
        # Sort the results based on user preference
        sorted_items = []
        
        if sort_by == "frequency":
            # Sort by frequency
            sorted_items = sorted(
                word_frequencies.items(),
                key=lambda x: x[1],
                reverse=(sort_order == "descending")
            )
        elif sort_by == "alphabetical":
            # Sort alphabetically
            sorted_items = sorted(
                word_frequencies.items(),
                key=lambda x: x[0],
                reverse=(sort_order == "descending")
            )
        elif sort_by == "length":
            # Sort by word length
            sorted_items = sorted(
                word_frequencies.items(),
                key=lambda x: len(x[0]),
                reverse=(sort_order == "descending")
            )
        
        # Apply output limit if specified
        if output_limit is not None and output_limit > 0:
            sorted_items = sorted_items[:output_limit]
        
        # Create sorted dictionary
        sorted_word_frequencies = dict(sorted_items)
        
        # Calculate additional statistics
        if total_words > 0:
            # Average word length
            avg_word_length = sum(len(word) for word in processed_words) / total_words
            
            # Word length distribution
            word_length_dist = {}
            for word in processed_words:
                length = len(word)
                word_length_dist[length] = word_length_dist.get(length, 0) + 1
            
            # Frequency distribution (how many words appear X times)
            freq_dist = {}
            for count in word_counter.values():
                freq_dist[count] = freq_dist.get(count, 0) + 1
            
            # Top 10 most frequent words
            top_10_words = word_counter.most_common(10)
            
            # Words that appear only once (hapax legomena)
            hapax_legomena = [word for word, count in word_counter.items() if count == 1]
            
            summary_stats = {
                "total_words": total_words,
                "unique_words": unique_words,
                "most_common_word": most_common_word,
                "most_common_count": most_common_count,
                "average_word_length": round(avg_word_length, 2),
                "lexical_diversity": round(unique_words / total_words, 4) if total_words > 0 else 0,
                "top_10_words": dict(top_10_words),
                "words_appearing_once": len(hapax_legomena),
                "word_length_distribution": dict(sorted(word_length_dist.items())),
                "frequency_distribution": dict(sorted(freq_dist.items()))
            }
        else:
            summary_stats = {
                "total_words": 0,
                "unique_words": 0,
                "most_common_word": None,
                "most_common_count": 0,
                "average_word_length": 0,
                "lexical_diversity": 0,
                "top_10_words": {},
                "words_appearing_once": 0,
                "word_length_distribution": {},
                "frequency_distribution": {}
            }
        
        # Prepare processing options info
        processing_options = {
            "case_sensitive": case_sensitive,
            "include_numbers": include_numbers,
            "min_word_length": min_word_length,
            "stop_words_used": len(stop_words_set) > 0,
            "stop_words_count": len(stop_words_set),
            "custom_delimiters": custom_delimiters,
            "output_limit": output_limit,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Return comprehensive results
        return {
            "success": True,
            "file_stats": file_stats,
            "word_frequencies": sorted_word_frequencies,
            "summary": summary_stats,
            "processing_options": processing_options,
            "metadata": {
                "tool": "count_word_frequency_file",
                "version": "1.0.0",
                "timestamp": "2024-01-01"  # In production, use datetime.now().isoformat()
            }
        }
        
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "file_path": file_path
        }
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read()
            # If we get here, we can process with latin-1
            # But for simplicity, we'll return an error suggesting utf-8
            return {
                "success": False,
                "error": f"File encoding issue. Try converting file to UTF-8: {file_path}",
                "file_path": file_path,
                "suggestion": "Convert file to UTF-8 encoding"
            }
        except:
            return {
                "success": False,
                "error": f"Cannot read file due to encoding issues: {file_path}",
                "file_path": file_path
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "file_path": file_path
        }