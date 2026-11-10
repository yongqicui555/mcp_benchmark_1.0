import math
import sys
from typing import Dict, List, Union, Optional
from decimal import Decimal, getcontext
import time

def factorial_calculator(n: Union[int, str], method: str = 'iterative', 
                         include_details: bool = True, 
                         calculate_time: bool = False,
                         precision: int = 50) -> Dict:
    """
    Calculate factorial of a number with various methods and detailed information.
    
    Args:
        n: The number to calculate factorial for (non-negative integer)
        method: Calculation method - 'iterative', 'recursive', or 'math_lib'
        include_details: Whether to include mathematical details and properties
        calculate_time: Whether to measure and report calculation time
        precision: Decimal precision for large number calculations (default: 50)
    
    Returns:
        dict: Factorial result with optional details and properties
    
    Raises:
        ValueError: If n is negative or not an integer
    """
    
    # Set up timing
    start_time = time.time() if calculate_time else None
    
    # Validate input
    try:
        n = int(n)
    except (ValueError, TypeError):
        return {
            'error': 'Input must be an integer or string representing an integer',
            'input_received': str(n)
        }
    
    if n < 0:
        return {
            'error': 'Factorial is not defined for negative numbers',
            'input': n,
            'suggestion': 'Use gamma function for non-integer or negative values'
        }
    
    result = {
        'input': n,
        'factorial': None,
        'method_used': method,
        'success': False
    }
    
    # Calculate factorial based on chosen method
    try:
        if method == 'math_lib':
            # Use Python's math.factorial (fastest for standard integers)
            factorial_result = math.factorial(n)
            
        elif method == 'iterative':
            # Iterative calculation
            factorial_result = 1
            for i in range(2, n + 1):
                factorial_result *= i
                
        elif method == 'recursive':
            # Recursive calculation (with memoization for efficiency)
            memo = {}
            def recursive_fact(k):
                if k in memo:
                    return memo[k]
                if k == 0 or k == 1:
                    return 1
                result = k * recursive_fact(k - 1)
                memo[k] = result
                return result
            
            factorial_result = recursive_fact(n)
            
        else:
            return {
                'error': f"Unknown method '{method}'. Use 'iterative', 'recursive', or 'math_lib'",
                'available_methods': ['iterative', 'recursive', 'math_lib']
            }
        
        result['factorial'] = factorial_result
        result['success'] = True
        
        # Calculate time if requested
        if calculate_time and start_time:
            elapsed = time.time() - start_time
            result['calculation_time_ms'] = round(elapsed * 1000, 3)
        
        # Add details if requested
        if include_details:
            details = _get_factorial_details(n, factorial_result, precision)
            result.update(details)
        
        # Add warnings for large numbers
        if n > 20:
            result['warning'] = f'Factorial of {n} is a very large number ({len(str(factorial_result))} digits)'
        
        if n > 1000 and method != 'math_lib':
            result['suggestion'] = 'For n > 1000, consider using math_lib method for better performance'
        
    except RecursionError:
        return {
            'error': f'Recursion depth exceeded for n={n}. Use iterative or math_lib method for large numbers.',
            'input': n,
            'max_recursion_depth': sys.getrecursionlimit()
        }
    except OverflowError:
        return {
            'error': f'Factorial of {n} causes integer overflow',
            'input': n,
            'suggestion': 'Use approximation methods or specialized libraries for very large factorials'
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}',
            'input': n
        }
    
    return result

def _get_factorial_details(n: int, factorial_result: int, precision: int) -> Dict:
    """Generate detailed mathematical information about the factorial."""
    
    details = {
        'mathematical_properties': {},
        'approximations': {},
        'related_sequences': {}
    }
    
    # Basic properties
    details['digit_count'] = len(str(factorial_result))
    details['is_even'] = factorial_result % 2 == 0
    details['trailing_zeros'] = _count_trailing_zeros(factorial_result)
    
    # Mathematical properties
    details['mathematical_properties']['definition'] = f'{n}! = {n} × {n-1} × ... × 2 × 1' if n > 0 else '0! = 1'
    
    if n > 0:
        details['mathematical_properties']['prime_factors'] = _get_prime_factors(factorial_result)
    
    # Approximations (for large n)
    if n >= 10:
        # Stirling's approximation
        stirling = math.sqrt(2 * math.pi * n) * (n / math.e) ** n
        details['approximations']['stirling'] = {
            'value': stirling,
            'relative_error': abs(stirling - factorial_result) / factorial_result
        }
        
        # More accurate Stirling approximation
        stirling_accurate = math.sqrt(2 * math.pi * n) * (n / math.e) ** n * (1 + 1/(12*n))
        details['approximations']['stirling_accurate'] = {
            'value': stirling_accurate,
            'relative_error': abs(stirling_accurate - factorial_result) / factorial_result
        }
    
    # Related sequences
    if n <= 20:  # Keep it reasonable
        details['related_sequences']['factorial_sequence'] = [math.factorial(i) for i in range(min(n+1, 11))]
    
    # Double factorial (n!!)
    if n <= 30:
        double_fact = 1
        for i in range(n, 0, -2):
            double_fact *= i
        details['related_sequences']['double_factorial'] = double_fact
    
    # Subfactorial (derangements) for small n
    if n <= 10:
        subfactorial = _calculate_subfactorial(n)
        details['related_sequences']['subfactorial'] = subfactorial
    
    # Gamma function relationship
    details['mathematical_properties']['gamma_relationship'] = f'Γ({n+1}) = {n}!'
    
    return details

def _count_trailing_zeros(n: int) -> int:
    """Count trailing zeros in factorial result."""
    count = 0
    while n % 10 == 0 and n != 0:
        count += 1
        n //= 10
    return count

def _get_prime_factors(n: int) -> Dict[int, int]:
    """Get prime factorization of a number."""
    factors = {}
    d = 2
    temp = n
    
    while d * d <= temp:
        while temp % d == 0:
            factors[d] = factors.get(d, 0) + 1
            temp //= d
        d += 1 if d == 2 else 2
    
    if temp > 1:
        factors[temp] = factors.get(temp, 0) + 1
    
    return factors

def _calculate_subfactorial(n: int) -> int:
    """Calculate !n (subfactorial/derangements)."""
    if n == 0:
        return 1
    if n == 1:
        return 0
    
    # Using recurrence: !n = (n-1) * (!(n-1) + !(n-2))
    a, b = 1, 0  # !0, !1
    for i in range(2, n + 1):
        a, b = b, (i - 1) * (a + b)
    return b

def factorial_approximation(n: int, method: str = 'stirling') -> Dict:
    """
    Approximate factorial for very large numbers.
    
    Args:
        n: The number
        method: 'stirling' or 'ramanujan'
    
    Returns:
        dict: Approximation result
    """
    if n <= 0:
        return {'error': 'n must be positive'}
    
    if method == 'stirling':
        # Stirling's approximation
        approx = math.sqrt(2 * math.pi * n) * (n / math.e) ** n
        correction = 1 + 1/(12*n) + 1/(288*n**2) - 139/(51840*n**3)
        approx *= correction
        
    elif method == 'ramanujan':
        # Ramanujan's approximation
        approx = math.sqrt(math.pi) * (n/math.e) ** n * ((8*n + 4*n + 1)**(1/6))
        
    else:
        return {'error': f"Unknown method '{method}'"}
    
    return {
        'n': n,
        'approximation_method': method,
        'approximate_value': approx,
        'log10_approximation': math.log10(approx) if approx > 0 else float('-inf')
    }

def batch_factorial_calculator(numbers: List[int], method: str = 'math_lib') -> Dict:
    """
    Calculate factorials for multiple numbers in batch.
    
    Args:
        numbers: List of numbers
        method: Calculation method
    
    Returns:
        dict: Batch results
    """
    results = []
    errors = []
    
    for n in numbers:
        try:
            n_int = int(n)
            if n_int < 0:
                errors.append({'input': n, 'error': 'Negative number'})
                continue
                
            result = factorial_calculator(n_int, method=method, include_details=False, calculate_time=False)
            results.append(result)
            
        except Exception as e:
            errors.append({'input': n, 'error': str(e)})
    
    return {
        'batch_size': len(numbers),
        'successful_calculations': len(results),
        'failed_calculations': len(errors),
        'results': results,
        'errors': errors if errors else None
    }

def test_factorial_calculator():
    """Test the factorial calculator with various examples."""
    
    print("Factorial Calculator - Test Suite")
    print("=" * 60)
    
    test_cases = [
        (0, "0! = 1 (by definition)"),
        (1, "1! = 1"),
        (5, "5! = 120"),
        (10, "10! = 3,628,800"),
        (20, "20! (large but manageable)"),
        (50, "50! (very large number)"),
    ]
    
    # Test different methods
    methods = ['iterative', 'recursive', 'math_lib']
    
    for n, description in test_cases:
        print(f"\nTest: {description}")
        print(f"n = {n}")
        
        for method in methods:
            if n > 15 and method == 'recursive':
                print(f"  {method}: Skipped (recursion depth for large n)")
                continue
                
            try:
                result = factorial_calculator(n, method=method, include_details=False, calculate_time=True)
                
                if result['success']:
                    fact_str = str(result['factorial'])
                    if len(fact_str) > 50:
                        fact_str = fact_str[:20] + "..." + fact_str[-20:] + f" ({len(fact_str)} digits)"
                    
                    time_str = f" in {result.get('calculation_time_ms', 'N/A')}ms"
                    print(f"  {method}: {fact_str}{time_str}")
                else:
                    print(f"  {method}: ERROR - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"  {method}: EXCEPTION - {str(e)}")
    
    # Test error cases
    print("\n" + "=" * 60)
    print("Error Case Tests:")
    
    error_cases = [-5, "invalid", 3.14, 10000]
    for case in error_cases:
        result = factorial_calculator(case, include_details=False)
        print(f"\nInput: {case}")
        print(f"Result: {result.get('error', 'No error')}")
    
    # Test batch calculation
    print("\n" + "=" * 60)
    print("Batch Calculation Test:")
    
    batch_numbers = [0, 1, 5, 10, -3, "abc", 7]
    batch_result = batch_factorial_calculator(batch_numbers)
    
    print(f"Batch size: {batch_result['batch_size']}")
    print(f"Successful: {batch_result['successful_calculations']}")
    print(f"Failed: {batch_result['failed_calculations']}")
    
    if batch_result['errors']:
        print("Errors:", batch_result['errors'])
    
    print("\n" + "=" * 60)
    print("Test complete!")

# If run directly, execute tests
if __name__ == "__main__":
    test_factorial_calculator()