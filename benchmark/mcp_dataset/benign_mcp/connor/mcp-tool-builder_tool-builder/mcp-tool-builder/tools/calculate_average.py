def calculate_average(numbers):
    """
    Calculate the average (mean) of a list of numbers.
    
    Args:
        numbers: A list of numbers (integers or floats) as a string in various formats:
                - "1,2,3,4,5" (comma-separated)
                - "1 2 3 4 5" (space-separated)
                - "[1, 2, 3, 4, 5]" (Python list format)
                - "1.5,2.7,3.2" (floats)
                
    Returns:
        A dictionary containing:
        - average: The calculated average (float)
        - count: Number of elements in the list
        - sum: Total sum of all numbers
        - numbers: The parsed list of numbers
        - error: Error message if any (None if successful)
    """
    import re
    import json
    
    result = {
        "average": None,
        "count": 0,
        "sum": 0,
        "numbers": [],
        "error": None
    }
    
    try:
        # If input is already a list (from JSON), use it directly
        if isinstance(numbers, list):
            num_list = numbers
        else:
            # Try to parse as JSON first (for Python list format)
            try:
                num_list = json.loads(numbers)
                if not isinstance(num_list, list):
                    raise ValueError("Input is not a list")
            except (json.JSONDecodeError, ValueError):
                # If not JSON, try to parse as comma-separated or space-separated values
                # Remove brackets if present
                cleaned = numbers.strip()
                if cleaned.startswith('[') and cleaned.endswith(']'):
                    cleaned = cleaned[1:-1]
                
                # Split by commas or spaces
                if ',' in cleaned:
                    parts = cleaned.split(',')
                else:
                    # Split by whitespace
                    parts = re.split(r'\s+', cleaned)
                
                num_list = []
                for part in parts:
                    part = part.strip()
                    if part:  # Skip empty strings
                        num_list.append(part)
        
        # Convert all elements to float
        parsed_numbers = []
        for num in num_list:
            try:
                parsed_numbers.append(float(num))
            except ValueError:
                raise ValueError(f"Invalid number: '{num}'")
        
        if not parsed_numbers:
            raise ValueError("No valid numbers found in input")
        
        # Calculate statistics
        total_sum = sum(parsed_numbers)
        count = len(parsed_numbers)
        average = total_sum / count
        
        # Prepare result
        result["numbers"] = parsed_numbers
        result["count"] = count
        result["sum"] = total_sum
        result["average"] = average
        
    except Exception as e:
        result["error"] = str(e)
    
    return result