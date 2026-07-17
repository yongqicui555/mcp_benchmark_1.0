def sum_and_average_calculator(numbers_input, precision=2):
    """
    Calculate both sum and average of a list of numbers with detailed statistics.
    
    Args:
        numbers_input: List of numbers as a comma-separated string or Python list
                      Example: "10,20,30" or [10, 20, 30]
        precision: Number of decimal places for results (default: 2)
    
    Returns:
        Dictionary with sum, average, and detailed statistics
    """
    try:
        # Parse input - handle both string and list inputs
        if isinstance(numbers_input, str):
            # Remove brackets if present and split by commas
            numbers_str = numbers_input.strip()
            if numbers_str.startswith('[') and numbers_str.endswith(']'):
                numbers_str = numbers_str[1:-1]
            
            # Split by commas and convert to floats
            numbers_list = []
            for num_str in numbers_str.split(','):
                num_str_clean = num_str.strip()
                if num_str_clean:
                    numbers_list.append(float(num_str_clean))
        elif isinstance(numbers_input, list):
            # Convert list elements to floats
            numbers_list = [float(num) for num in numbers_input]
        else:
            return {
                'error': f"Invalid input type: {type(numbers_input)}. Expected string or list.",
                'success': False
            }
        
        # Check if we have any numbers
        if not numbers_list:
            return {
                'error': "No numbers provided in the input",
                'success': False,
                'input': numbers_input
            }
        
        # Calculate basic statistics
        count = len(numbers_list)
        total_sum = sum(numbers_list)
        
        # Calculate average
        if count > 0:
            average = total_sum / count
        else:
            average = 0
        
        # Calculate additional statistics
        if count > 0:
            # Sort for median calculation
            sorted_numbers = sorted(numbers_list)
            
            # Calculate median
            if count % 2 == 1:
                # Odd number of elements
                median = sorted_numbers[count // 2]
            else:
                # Even number of elements
                mid1 = sorted_numbers[count // 2 - 1]
                mid2 = sorted_numbers[count // 2]
                median = (mid1 + mid2) / 2
            
            # Calculate min and max
            minimum = min(numbers_list)
            maximum = max(numbers_list)
            
            # Calculate range
            value_range = maximum - minimum
            
            # Calculate variance and standard deviation
            if count > 1:
                mean = average
                variance = sum((x - mean) ** 2 for x in numbers_list) / (count - 1)
                std_dev = variance ** 0.5
            else:
                variance = 0
                std_dev = 0
        else:
            median = 0
            minimum = 0
            maximum = 0
            value_range = 0
            variance = 0
            std_dev = 0
        
        # Format results with specified precision
        def format_number(num):
            return round(num, precision) if precision >= 0 else num
        
        # Prepare results
        results = {
            'success': True,
            'input': numbers_input,
            'parsed_numbers': numbers_list,
            'basic_results': {
                'sum': format_number(total_sum),
                'average': format_number(average),
                'count': count
            },
            'detailed_statistics': {
                'minimum': format_number(minimum),
                'maximum': format_number(maximum),
                'range': format_number(value_range),
                'median': format_number(median),
                'variance': format_number(variance),
                'standard_deviation': format_number(std_dev)
            },
            'summary': f"Sum: {format_number(total_sum)}, Average: {format_number(average)} (from {count} numbers)",
            'calculation_precision': precision
        }
        
        return results
        
    except ValueError as e:
        return {
            'error': f"Invalid number format in input: {str(e)}",
            'success': False,
            'input': numbers_input
        }
    except Exception as e:
        return {
            'error': f"Calculation error: {str(e)}",
            'success': False,
            'input': numbers_input
        }