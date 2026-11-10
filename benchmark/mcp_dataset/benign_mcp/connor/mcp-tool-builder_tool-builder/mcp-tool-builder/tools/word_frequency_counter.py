import os
import re
from collections import Counter
from typing import Dict, List

def word_frequency_counter(file_path: str) -> dict:
    """
    Read a text file and count how many times each word appears.
    
    Args:
        file_path: Path to the text file to analyze
        
    Returns:
        dict: Contains word frequencies and file information
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If there's an error reading the file
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")
    
    # Clean and tokenize text
    # Convert to lowercase and remove punctuation
    text_clean = text.lower()
    # Remove punctuation (keep apostrophes for contractions like "don't")
    text_clean = re.sub(r'[^\w\s\']', ' ', text_clean)
    
    # Split into words
    words = text_clean.split()
    
    # Count word frequencies
    word_counts = Counter(words)
    
    # Get most common words
    most_common = word_counts.most_common()
    
    # Prepare results
    total_words = len(words)
    unique_words = len(word_counts)
    
    return {
        "file_path": file_path,
        "total_words": total_words,
        "unique_words": unique_words,
        "word_frequencies": dict(most_common),
        "most_common_words": most_common[:10],  # Top 10 most frequent words
        "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
    }