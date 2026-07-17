def convert_temperature(temperature, from_unit):
    """
    Converts temperatures between Celsius and Fahrenheit.
    
    Args:
        temperature (float): The temperature value to convert
        from_unit (str): The unit to convert from - 'C' for Celsius or 'F' for Fahrenheit
        
    Returns:
        float: The converted temperature value, or an error message if input is invalid
        
    Examples:
        >>> convert_temperature(100, 'C')
        212.0  # 100°C to Fahrenheit
        >>> convert_temperature(32, 'F')
        0.0    # 32°F to Celsius
        >>> convert_temperature(-40, 'C')
        -40.0  # -40°C to Fahrenheit (same value)
        >>> convert_temperature(-40, 'F')
        -40.0  # -40°F to Celsius (same value)
    """
    try:
        # Validate temperature is numeric
        if not isinstance(temperature, (int, float)):
            return "Error: Temperature must be a numeric value (int or float)."
        
        # Validate and normalize unit
        if not isinstance(from_unit, str):
            return "Error: Unit must be a string ('C' or 'F')."
        
        from_unit = from_unit.upper().strip()
        
        # Perform conversion
        if from_unit == 'C' or from_unit == 'CELSIUS':
            # Celsius to Fahrenheit: (C × 9/5) + 32
            converted = (temperature * 9/5) + 32
            return float(converted)
        
        elif from_unit == 'F' or from_unit == 'FAHRENHEIT':
            # Fahrenheit to Celsius: (F - 32) × 5/9
            converted = (temperature - 32) * 5/9
            return float(converted)
        
        else:
            return "Error: Unit must be 'C' (Celsius) or 'F' (Fahrenheit)."
    
    except Exception as e:
        return f"Error converting temperature: {str(e)}"