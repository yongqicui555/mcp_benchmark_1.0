def calculate_factorial(n: int) -> dict:
    """
    Calculate the factorial of a non-negative integer.
    
    Args:
        n: Non-negative integer to calculate factorial for
        
    Returns:
        dict: Contains the factorial result and input information
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is only defined for non-negative integers")
    
    if n == 0:
        result = 1
    else:
        result = 1
        for i in range(1, n + 1):
            result *= i
    
    return {
        "input": n,
        "factorial": result,
        "explanation": f"{n}! = {result}"
    }