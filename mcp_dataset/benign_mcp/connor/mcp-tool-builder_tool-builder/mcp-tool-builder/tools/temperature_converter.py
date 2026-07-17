def temperature_converter(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert temperature between Celsius and Fahrenheit.
    
    Args:
        value: Temperature value to convert
        from_unit: Source unit ('c' for Celsius, 'f' for Fahrenheit)
        to_unit: Target unit ('c' for Celsius, 'f' for Fahrenheit)
    
    Returns:
        dict: Contains converted value and unit
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit not in ['c', 'f']:
        raise ValueError("from_unit must be 'c' for Celsius or 'f' for Fahrenheit")
    if to_unit not in ['c', 'f']:
        raise ValueError("to_unit must be 'c' for Celsius or 'f' for Fahrenheit")
    
    if from_unit == to_unit:
        result = value
    elif from_unit == 'c' and to_unit == 'f':
        # Celsius to Fahrenheit: (C × 9/5) + 32
        result = (value * 9/5) + 32
    elif from_unit == 'f' and to_unit == 'c':
        # Fahrenheit to Celsius: (F - 32) × 5/9
        result = (value - 32) * 5/9
    else:
        raise ValueError(f"Unsupported conversion: {from_unit} to {to_unit}")
    
    # Round to 2 decimal places for readability
    result = round(result, 2)
    
    return {
        "value": result,
        "unit": to_unit.upper(),
        "original_value": value,
        "original_unit": from_unit.upper()
    }