def temperature_converter_enhanced(value, from_unit, to_unit):
    """
    Enhanced temperature converter with support for multiple units and better error handling.
    
    Args:
        value: Temperature value as a string or number
        from_unit: Source temperature unit. Options: "C", "F", "K", "celsius", "fahrenheit", "kelvin"
        to_unit: Target temperature unit. Options: "C", "F", "K", "celsius", "fahrenheit", "kelvin"
        
    Returns:
        A dictionary containing:
        - original_value: The input value
        - original_unit: The input unit
        - converted_value: The converted temperature
        - converted_unit: The target unit
        - formula_used: The conversion formula applied
        - error: Error message if any (None if successful)
    """
    
    result = {
        "original_value": None,
        "original_unit": None,
        "converted_value": None,
        "converted_unit": None,
        "formula_used": None,
        "error": None
    }
    
    try:
        # Normalize unit names
        unit_map = {
            "c": "C", "celsius": "C",
            "f": "F", "fahrenheit": "F",
            "k": "K", "kelvin": "K"
        }
        
        # Convert input to lowercase for matching
        from_unit_lower = from_unit.lower()
        to_unit_lower = to_unit.lower()
        
        # Validate and normalize units
        if from_unit_lower not in unit_map:
            raise ValueError(f"Invalid source unit: '{from_unit}'. Valid options: C, F, K, celsius, fahrenheit, kelvin")
        
        if to_unit_lower not in unit_map:
            raise ValueError(f"Invalid target unit: '{to_unit}'. Valid options: C, F, K, celsius, fahrenheit, kelvin")
        
        from_unit_norm = unit_map[from_unit_lower]
        to_unit_norm = unit_map[to_unit_lower]
        
        # Parse the value
        try:
            temp_value = float(value)
        except ValueError:
            raise ValueError(f"Invalid temperature value: '{value}'. Must be a number.")
        
        # Store original values
        result["original_value"] = temp_value
        result["original_unit"] = from_unit_norm
        
        # Conversion formulas
        formulas = {
            ("C", "F"): lambda c: (c * 9/5) + 32,
            ("F", "C"): lambda f: (f - 32) * 5/9,
            ("C", "K"): lambda c: c + 273.15,
            ("K", "C"): lambda k: k - 273.15,
            ("F", "K"): lambda f: (f - 32) * 5/9 + 273.15,
            ("K", "F"): lambda k: (k - 273.15) * 9/5 + 32,
        }
        
        # Check if conversion is needed
        if from_unit_norm == to_unit_norm:
            converted_value = temp_value
            formula = "No conversion needed (same units)"
        else:
            # Get the conversion function
            conversion_key = (from_unit_norm, to_unit_norm)
            if conversion_key in formulas:
                conversion_func = formulas[conversion_key]
                converted_value = conversion_func(temp_value)
                
                # Generate formula description
                formula_descriptions = {
                    ("C", "F"): "F = (C × 9/5) + 32",
                    ("F", "C"): "C = (F - 32) × 5/9",
                    ("C", "K"): "K = C + 273.15",
                    ("K", "C"): "C = K - 273.15",
                    ("F", "K"): "K = (F - 32) × 5/9 + 273.15",
                    ("K", "F"): "F = (K - 273.15) × 9/5 + 32",
                }
                formula = formula_descriptions[conversion_key]
            else:
                # This shouldn't happen with our validation, but just in case
                raise ValueError(f"Conversion from {from_unit_norm} to {to_unit_norm} not supported")
        
        # Round to 2 decimal places for readability
        converted_value = round(converted_value, 2)
        
        # Store results
        result["converted_value"] = converted_value
        result["converted_unit"] = to_unit_norm
        result["formula_used"] = formula
        
        # Add some useful temperature context
        if to_unit_norm == "C":
            if converted_value < 0:
                result["context"] = "Below freezing"
            elif converted_value < 10:
                result["context"] = "Cold"
            elif converted_value < 20:
                result["context"] = "Cool"
            elif converted_value < 30:
                result["context"] = "Warm"
            else:
                result["context"] = "Hot"
        elif to_unit_norm == "F":
            if converted_value < 32:
                result["context"] = "Below freezing"
            elif converted_value < 50:
                result["context"] = "Cold"
            elif converted_value < 70:
                result["context"] = "Cool"
            elif converted_value < 90:
                result["context"] = "Warm"
            else:
                result["context"] = "Hot"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result