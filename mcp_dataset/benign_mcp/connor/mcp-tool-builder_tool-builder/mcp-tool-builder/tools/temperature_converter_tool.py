def temperature_converter_tool(value, from_unit, to_unit):
    """
    Convert temperatures between Celsius, Fahrenheit, and Kelvin.
    
    Args:
        value: Temperature value to convert (string or numeric)
        from_unit: Original unit ('C', 'F', or 'K')
        to_unit: Target unit ('C', 'F', or 'K')
    
    Returns:
        Dictionary with conversion results and details
    """
    try:
        # Convert input value to float
        temp_value = float(value)
        
        # Validate units
        valid_units = ['C', 'F', 'K']
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        
        if from_unit not in valid_units:
            return {
                'error': f"Invalid source unit: {from_unit}. Must be one of: {', '.join(valid_units)}"
            }
        
        if to_unit not in valid_units:
            return {
                'error': f"Invalid target unit: {to_unit}. Must be one of: {', '.join(valid_units)}"
            }
        
        # Convert to Kelvin first (as intermediate unit)
        if from_unit == 'C':
            kelvin = temp_value + 273.15
        elif from_unit == 'F':
            kelvin = (temp_value - 32) * 5/9 + 273.15
        else:  # from_unit == 'K'
            kelvin = temp_value
        
        # Convert from Kelvin to target unit
        if to_unit == 'C':
            result = kelvin - 273.15
        elif to_unit == 'F':
            result = (kelvin - 273.15) * 9/5 + 32
        else:  # to_unit == 'K'
            result = kelvin
        
        # Format the result
        result = round(result, 2)
        
        # Determine temperature context
        if to_unit == 'C':
            if result < 0:
                context = "Freezing"
            elif result < 10:
                context = "Cold"
            elif result < 20:
                context = "Cool"
            elif result < 30:
                context = "Warm"
            elif result < 40:
                context = "Hot"
            else:
                context = "Extremely Hot"
        elif to_unit == 'F':
            if result < 32:
                context = "Freezing"
            elif result < 50:
                context = "Cold"
            elif result < 68:
                context = "Cool"
            elif result < 86:
                context = "Warm"
            elif result < 104:
                context = "Hot"
            else:
                context = "Extremely Hot"
        else:  # Kelvin
            if result < 273.15:
                context = "Below freezing"
            elif result < 283.15:
                context = "Cold"
            elif result < 293.15:
                context = "Cool"
            elif result < 303.15:
                context = "Warm"
            elif result < 313.15:
                context = "Hot"
            else:
                context = "Extremely Hot"
        
        # Create formulas dictionary
        formulas = {
            'C_to_F': 'F = (C × 9/5) + 32',
            'F_to_C': 'C = (F - 32) × 5/9',
            'C_to_K': 'K = C + 273.15',
            'K_to_C': 'C = K - 273.15',
            'F_to_K': 'K = (F - 32) × 5/9 + 273.15',
            'K_to_F': 'F = (K - 273.15) × 9/5 + 32'
        }
        
        formula_key = f"{from_unit}_to_{to_unit}"
        formula_used = formulas.get(formula_key, "Direct conversion (same unit)")
        
        return {
            'original_value': temp_value,
            'original_unit': from_unit,
            'converted_value': result,
            'converted_unit': to_unit,
            'formula_used': formula_used,
            'context': context,
            'error': None
        }
        
    except ValueError:
        return {
            'error': f"Invalid temperature value: {value}. Must be a number."
        }
    except Exception as e:
        return {
            'error': f"Conversion error: {str(e)}"
        }