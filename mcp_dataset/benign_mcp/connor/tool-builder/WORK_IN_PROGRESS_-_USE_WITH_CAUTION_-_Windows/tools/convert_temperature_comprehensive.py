import re
from typing import Dict, Union, Optional

def convert_temperature_comprehensive(
    temperature: Union[str, int, float], 
    from_unit: str,
    to_unit: Optional[str] = None,
    precision: int = 2
) -> Dict[str, Union[str, float, bool]]:
    """
    Converts temperatures between Celsius and Fahrenheit with comprehensive error checking.
    
    Args:
        temperature: Temperature value to convert (can be string, int, or float)
        from_unit: Original unit - 'C' for Celsius, 'F' for Fahrenheit
        to_unit: Target unit - 'C' for Celsius, 'F' for Fahrenheit. 
                 If None, automatically converts to the opposite unit.
        precision: Number of decimal places for the result (default: 2)
        
    Returns:
        Dictionary containing conversion results or error information
        
    Examples:
        convert_temperature_comprehensive("25", "C", "F")  # 25°C to °F
        convert_temperature_comprehensive("98.6", "F", "C")  # 98.6°F to °C
        convert_temperature_comprehensive(0, "C")  # 0°C to °F (auto-detect opposite)
    """
    
    # Define valid units
    valid_units = ['C', 'F', 'celsius', 'fahrenheit', '°C', '°F']
    
    # Normalize unit names
    unit_mapping = {
        'C': 'C', 'celsius': 'C', '°C': 'C',
        'F': 'F', 'fahrenheit': 'F', '°F': 'F'
    }
    
    try:
        # Validate and normalize from_unit
        from_unit_lower = str(from_unit).strip().lower()
        if from_unit_lower in ['c', 'celsius', '°c']:
            normalized_from = 'C'
        elif from_unit_lower in ['f', 'fahrenheit', '°f']:
            normalized_from = 'F'
        else:
            return {
                "success": False,
                "error": f"Invalid source unit: '{from_unit}'. Valid units: C, F, celsius, fahrenheit, °C, °F",
                "input_temperature": str(temperature),
                "input_unit": from_unit
            }
        
        # Determine target unit
        if to_unit is None:
            # Auto-convert to opposite unit
            normalized_to = 'F' if normalized_from == 'C' else 'C'
        else:
            # Validate and normalize to_unit
            to_unit_lower = str(to_unit).strip().lower()
            if to_unit_lower in ['c', 'celsius', '°c']:
                normalized_to = 'C'
            elif to_unit_lower in ['f', 'fahrenheit', '°f']:
                normalized_to = 'F'
            else:
                return {
                    "success": False,
                    "error": f"Invalid target unit: '{to_unit}'. Valid units: C, F, celsius, fahrenheit, °C, °F",
                    "input_temperature": str(temperature),
                    "input_unit": from_unit,
                    "target_unit": to_unit
                }
        
        # Check if conversion is needed
        if normalized_from == normalized_to:
            return {
                "success": False,
                "error": f"Source and target units are the same ({normalized_from}). No conversion needed.",
                "input_temperature": str(temperature),
                "input_unit": from_unit,
                "target_unit": to_unit
            }
        
        # Parse temperature value
        temp_str = str(temperature).strip()
        
        # Remove any degree symbols or extra whitespace
        temp_str = temp_str.replace('°', '').replace('º', '')
        
        # Check for empty input
        if not temp_str:
            return {
                "success": False,
                "error": "Temperature value cannot be empty",
                "input_temperature": str(temperature),
                "input_unit": from_unit,
                "target_unit": to_unit
            }
        
        # Validate temperature format using regex
        # Allows: integers, decimals, negative numbers, scientific notation
        temp_pattern = r'^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$'
        
        if not re.match(temp_pattern, temp_str):
            return {
                "success": False,
                "error": f"Invalid temperature format: '{temperature}'. Must be a valid number.",
                "input_temperature": str(temperature),
                "input_unit": from_unit,
                "target_unit": to_unit
            }
        
        # Convert to float
        try:
            temp_value = float(temp_str)
        except ValueError:
            return {
                "success": False,
                "error": f"Could not convert '{temperature}' to a number",
                "input_temperature": str(temperature),
                "input_unit": from_unit,
                "target_unit": to_unit
            }
        
        # Validate precision
        if not isinstance(precision, int) or precision < 0 or precision > 10:
            precision = 2  # Default to 2 if invalid
        
        # Perform conversion
        if normalized_from == 'C' and normalized_to == 'F':
            # Celsius to Fahrenheit: (C × 9/5) + 32
            converted_value = (temp_value * 9/5) + 32
            formula = f"({temp_value} × 9/5) + 32"
        elif normalized_from == 'F' and normalized_to == 'C':
            # Fahrenheit to Celsius: (F - 32) × 5/9
            converted_value = (temp_value - 32) * 5/9
            formula = f"({temp_value} - 32) × 5/9"
        else:
            # This should not happen with our validation, but just in case
            return {
                "success": False,
                "error": f"Unsupported conversion: {normalized_from} to {normalized_to}",
                "input_temperature": str(temperature),
                "input_unit": from_unit,
                "target_unit": to_unit
            }
        
        # Round to specified precision
        converted_value = round(converted_value, precision)
        
        # Format the result
        from_symbol = '°C' if normalized_from == 'C' else '°F'
        to_symbol = '°C' if normalized_to == 'C' else '°F'
        
        # Determine temperature category for both input and output
        def get_temperature_category(temp: float, unit: str) -> str:
            if unit == 'C':
                if temp < -273.15:
                    return "Below Absolute Zero (Invalid)"
                elif temp < 0:
                    return "Freezing"
                elif temp < 10:
                    return "Cold"
                elif temp < 20:
                    return "Cool"
                elif temp < 30:
                    return "Comfortable"
                elif temp < 40:
                    return "Warm"
                else:
                    return "Hot"
            else:  # Fahrenheit
                if temp < -459.67:
                    return "Below Absolute Zero (Invalid)"
                elif temp < 32:
                    return "Freezing"
                elif temp < 50:
                    return "Cold"
                elif temp < 68:
                    return "Cool"
                elif temp < 86:
                    return "Comfortable"
                elif temp < 104:
                    return "Warm"
                else:
                    return "Hot"
        
        input_category = get_temperature_category(temp_value, normalized_from)
        output_category = get_temperature_category(converted_value, normalized_to)
        
        # Check for extreme temperatures
        warnings = []
        if normalized_from == 'C' and temp_value < -273.15:
            warnings.append("Input temperature is below absolute zero (-273.15°C)")
        elif normalized_from == 'F' and temp_value < -459.67:
            warnings.append("Input temperature is below absolute zero (-459.67°F)")
        
        # Prepare result
        result = {
            "success": True,
            "original": {
                "value": temp_value,
                "unit": normalized_from,
                "formatted": f"{temp_value}{from_symbol}",
                "category": input_category
            },
            "converted": {
                "value": converted_value,
                "unit": normalized_to,
                "formatted": f"{converted_value}{to_symbol}",
                "category": output_category
            },
            "conversion": {
                "from": normalized_from,
                "to": normalized_to,
                "formula": formula,
                "precision": precision
            }
        }
        
        # Add warnings if any
        if warnings:
            result["warnings"] = warnings
        
        # Add common reference points
        reference_points = {
            "water_freezes": "0°C = 32°F",
            "water_boils": "100°C = 212°F",
            "absolute_zero": "-273.15°C = -459.67°F",
            "room_temperature": "20°C = 68°F",
            "body_temperature": "37°C = 98.6°F"
        }
        result["reference_points"] = reference_points
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "input_temperature": str(temperature),
            "input_unit": from_unit,
            "target_unit": to_unit
        }