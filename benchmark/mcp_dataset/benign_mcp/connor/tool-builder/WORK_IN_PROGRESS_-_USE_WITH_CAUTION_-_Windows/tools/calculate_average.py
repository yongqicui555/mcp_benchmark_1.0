def calculate_average(numbers):
    """
    Calculates the average (mean) of a list of numbers.
    
    Args:
        numbers (list): List of integers or floats to calculate average for
        
    Returns:
        float: The mean value of the numbers, or an error message if input is invalid
        
    Examples:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
        >>> calculate_average([1.5, 2.5, 3.5])
        2.5
        >>> calculate_average([10, 20, 30, 40])
        25.0
    """
    try:
        # Check if input is a list
        if not isinstance(numbers, list):
            return "Error: Input must be a list of numbers."
        
        # Check if list is empty
        if len(numbers) == 0:
            return "Error: Cannot calculate average of an empty list."
        
        # Check if all elements are numbers
        for num in numbers:
            if not isinstance(num, (int, float)):
                return f"Error: All elements must be numbers. Found non-numeric value: {num}"
        
        # Calculate average
        total = sum(numbers)
        average = total / len(numbers)
        
        return float(average)
    
    except ZeroDivisionError:
        # This shouldn't happen since we check for empty list, but just in case
        return "Error: Division by zero - cannot calculate average."
    except Exception as e:
        return f"Error calculating average: {str(e)}"