def temperature_converter_plus(temperature, from_unit, to_unit, include_context=False):
    """
    Convert temperatures between Celsius and Fahrenheit with additional context.
    
    Args:
        temperature (float): The temperature value to convert
        from_unit (str): Source unit - 'C' for Celsius or 'F' for Fahrenheit
        to_unit (str): Target unit - 'C' for Celsius or 'F' for Fahrenheit
        include_context (bool): Whether to include weather context information
    
    Returns:
        dict: Contains converted temperature and optional context
    """
    try:
        # Validate inputs
        temperature = float(temperature)
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        
        if from_unit not in ['C', 'F'] or to_unit not in ['C', 'F']:
            return {
                'error': 'Invalid unit. Use "C" for Celsius or "F" for Fahrenheit'
            }
        
        if from_unit == to_unit:
            converted_temp = temperature
            formula = "No conversion needed (same units)"
        elif from_unit == 'C' and to_unit == 'F':
            # Celsius to Fahrenheit: (C × 9/5) + 32
            converted_temp = (temperature * 9/5) + 32
            formula = f"({temperature} × 9/5) + 32 = {converted_temp:.2f}"
        else:  # from_unit == 'F' and to_unit == 'C'
            # Fahrenheit to Celsius: (F - 32) × 5/9
            converted_temp = (temperature - 32) * 5/9
            formula = f"({temperature} - 32) × 5/9 = {converted_temp:.2f}"
        
        result = {
            'original_temperature': temperature,
            'original_unit': from_unit,
            'converted_temperature': round(converted_temp, 2),
            'target_unit': to_unit,
            'conversion_formula': formula,
            'freezing_point': {
                'celsius': 0,
                'fahrenheit': 32,
                'description': 'Water freezes at this temperature'
            },
            'boiling_point': {
                'celsius': 100,
                'fahrenheit': 212,
                'description': 'Water boils at this temperature at sea level'
            }
        }
        
        # Add weather context if requested
        if include_context:
            # Determine weather context based on temperature
            if from_unit == 'C':
                temp_for_context = temperature
            else:
                temp_for_context = (temperature - 32) * 5/9
            
            if temp_for_context < -10:
                weather_context = "Extremely cold - Arctic conditions"
            elif temp_for_context < 0:
                weather_context = "Freezing - Winter conditions"
            elif temp_for_context < 10:
                weather_context = "Cold - Jacket weather"
            elif temp_for_context < 20:
                weather_context = "Cool - Pleasant weather"
            elif temp_for_context < 30:
                weather_context = "Warm - Comfortable weather"
            elif temp_for_context < 35:
                weather_context = "Hot - Summer weather"
            else:
                weather_context = "Very hot - Heatwave conditions"
            
            result['weather_context'] = weather_context
            
            # Add human body temperature reference
            result['human_body_temperature'] = {
                'celsius': 37.0,
                'fahrenheit': 98.6,
                'description': 'Normal human body temperature'
            }
        
        return result
        
    except ValueError:
        return {
            'error': 'Invalid temperature value. Please provide a numeric temperature.'
        }
    except Exception as e:
        return {
            'error': f'An error occurred: {str(e)}'
        }

# Example usage and test function
def test_temperature_converter():
    """Test the temperature converter with various examples"""
    test_cases = [
        (0, 'C', 'F', True),      # Freezing point
        (100, 'C', 'F', True),    # Boiling point
        (32, 'F', 'C', True),     # Freezing in Fahrenheit
        (212, 'F', 'C', True),    # Boiling in Fahrenheit
        (20, 'C', 'F', False),    # Room temperature
        (98.6, 'F', 'C', True),   # Body temperature
    ]
    
    print("Testing Temperature Converter Plus:")
    print("=" * 50)
    
    for temp, from_u, to_u, context in test_cases:
        result = temperature_converter_plus(temp, from_u, to_u, context)
        print(f"\n{temp}°{from_u} → {result['converted_temperature']}°{to_u}")
        print(f"Formula: {result['conversion_formula']}")
        
        if 'weather_context' in result:
            print(f"Weather context: {result['weather_context']}")
    
    print("\n" + "=" * 50)
    print("Reference points:")
    print("- Water freezes at 0°C / 32°F")
    print("- Water boils at 100°C / 212°F")
    print("- Human body temperature: 37°C / 98.6°F")

# If run directly, execute tests
if __name__ == "__main__":
    test_temperature_converter()