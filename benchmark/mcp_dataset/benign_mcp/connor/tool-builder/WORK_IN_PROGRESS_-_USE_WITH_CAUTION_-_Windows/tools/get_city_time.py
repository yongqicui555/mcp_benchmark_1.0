import pytz
from datetime import datetime
from typing import Dict, List, Optional, Union
import re

def get_city_time(
    city_name: str,
    include_details: bool = True,
    format_24h: bool = False,
    include_date: bool = True,
    include_timezone_info: bool = True
) -> Dict[str, Union[str, Dict, List, bool]]:
    """
    Fetches current local time for a city with comprehensive time zone support.
    
    Args:
        city_name: Name of the city (e.g., 'Tokyo', 'London', 'New York')
        include_details: Include additional city and timezone details
        format_24h: Use 24-hour format (default: 12-hour format with AM/PM)
        include_date: Include date information
        include_timezone_info: Include timezone offset and abbreviation
        
    Returns:
        Dictionary containing time information and city details
        
    Examples:
        get_city_time("Tokyo")
        get_city_time("New York", format_24h=True)
        get_city_time("London", include_details=False)
    """
    
    # Comprehensive city to timezone mapping
    # Includes major cities and common aliases
    city_timezone_map = {
        # North America
        "new york": "America/New_York",
        "nyc": "America/New_York",
        "new york city": "America/New_York",
        "los angeles": "America/Los_Angeles",
        "la": "America/Los_Angeles",
        "chicago": "America/Chicago",
        "toronto": "America/Toronto",
        "vancouver": "America/Vancouver",
        "mexico city": "America/Mexico_City",
        "miami": "America/New_York",  # Same as NY
        "houston": "America/Chicago",
        "dallas": "America/Chicago",
        "phoenix": "America/Phoenix",
        "denver": "America/Denver",
        "seattle": "America/Los_Angeles",
        "san francisco": "America/Los_Angeles",
        "boston": "America/New_York",
        "washington dc": "America/New_York",
        "washington": "America/New_York",
        "atlanta": "America/New_York",
        "detroit": "America/Detroit",
        "montreal": "America/Toronto",
        "calgary": "America/Edmonton",
        "edmonton": "America/Edmonton",
        
        # South America
        "sao paulo": "America/Sao_Paulo",
        "rio de janeiro": "America/Sao_Paulo",
        "buenos aires": "America/Argentina/Buenos_Aires",
        "lima": "America/Lima",
        "bogota": "America/Bogota",
        "santiago": "America/Santiago",
        "caracas": "America/Caracas",
        
        # Europe
        "london": "Europe/London",
        "paris": "Europe/Paris",
        "berlin": "Europe/Berlin",
        "madrid": "Europe/Madrid",
        "rome": "Europe/Rome",
        "amsterdam": "Europe/Amsterdam",
        "brussels": "Europe/Brussels",
        "vienna": "Europe/Vienna",
        "prague": "Europe/Prague",
        "warsaw": "Europe/Warsaw",
        "moscow": "Europe/Moscow",
        "istanbul": "Europe/Istanbul",
        "athens": "Europe/Athens",
        "dublin": "Europe/Dublin",
        "lisbon": "Europe/Lisbon",
        "stockholm": "Europe/Stockholm",
        "oslo": "Europe/Oslo",
        "helsinki": "Europe/Helsinki",
        "copenhagen": "Europe/Copenhagen",
        "zurich": "Europe/Zurich",
        "geneva": "Europe/Zurich",
        
        # Asia
        "tokyo": "Asia/Tokyo",
        "beijing": "Asia/Shanghai",
        "shanghai": "Asia/Shanghai",
        "hong kong": "Asia/Hong_Kong",
        "singapore": "Asia/Singapore",
        "seoul": "Asia/Seoul",
        "bangkok": "Asia/Bangkok",
        "jakarta": "Asia/Jakarta",
        "manila": "Asia/Manila",
        "kuala lumpur": "Asia/Kuala_Lumpur",
        "taipei": "Asia/Taipei",
        "mumbai": "Asia/Kolkata",
        "delhi": "Asia/Kolkata",
        "bangalore": "Asia/Kolkata",
        "chennai": "Asia/Kolkata",
        "kolkata": "Asia/Kolkata",
        "dhaka": "Asia/Dhaka",
        "karachi": "Asia/Karachi",
        "islamabad": "Asia/Karachi",
        "dubai": "Asia/Dubai",
        "abu dhabi": "Asia/Dubai",
        "riyadh": "Asia/Riyadh",
        "doha": "Asia/Qatar",
        "tehran": "Asia/Tehran",
        "baghdad": "Asia/Baghdad",
        
        # Australia/Oceania
        "sydney": "Australia/Sydney",
        "melbourne": "Australia/Melbourne",
        "brisbane": "Australia/Brisbane",
        "perth": "Australia/Perth",
        "adelaide": "Australia/Adelaide",
        "auckland": "Pacific/Auckland",
        "wellington": "Pacific/Auckland",
        "fiji": "Pacific/Fiji",
        "honolulu": "Pacific/Honolulu",
        
        # Africa
        "cairo": "Africa/Cairo",
        "johannesburg": "Africa/Johannesburg",
        "cape town": "Africa/Johannesburg",
        "nairobi": "Africa/Nairobi",
        "lagos": "Africa/Lagos",
        "accra": "Africa/Accra",
        "casablanca": "Africa/Casablanca",
        "tunis": "Africa/Tunis",
        "algiers": "Africa/Algiers",
    }
    
    # City information for additional details
    city_info = {
        "new york": {"country": "USA", "region": "North America", "population": "8.4M"},
        "london": {"country": "UK", "region": "Europe", "population": "8.9M"},
        "tokyo": {"country": "Japan", "region": "Asia", "population": "13.9M"},
        "paris": {"country": "France", "region": "Europe", "population": "2.1M"},
        "sydney": {"country": "Australia", "region": "Oceania", "population": "5.3M"},
        "beijing": {"country": "China", "region": "Asia", "population": "21.5M"},
        "mumbai": {"country": "India", "region": "Asia", "population": "20.7M"},
        "cairo": {"country": "Egypt", "region": "Africa", "population": "9.5M"},
        "sao paulo": {"country": "Brazil", "region": "South America", "population": "12.3M"},
        "moscow": {"country": "Russia", "region": "Europe", "population": "12.5M"},
    }
    
    try:
        # Normalize city name
        normalized_city = city_name.strip().lower()
        
        # Check if city is in our mapping
        if normalized_city not in city_timezone_map:
            # Try to find similar cities
            similar_cities = []
            for city in city_timezone_map.keys():
                if normalized_city in city or city in normalized_city:
                    similar_cities.append(city.title())
            
            # Also check for partial matches
            if not similar_cities:
                for city in city_timezone_map.keys():
                    if normalized_city.split()[0] in city or any(word in city for word in normalized_city.split()):
                        similar_cities.append(city.title())
            
            # Remove duplicates and sort
            similar_cities = sorted(list(set(similar_cities)))
            
            return {
                "success": False,
                "error": f"City '{city_name}' not found in database.",
                "suggestions": similar_cities[:10] if similar_cities else [],
                "available_regions": ["North America", "South America", "Europe", "Asia", "Africa", "Australia/Oceania"],
                "total_cities_available": len(city_timezone_map)
            }
        
        # Get timezone for the city
        timezone_str = city_timezone_map[normalized_city]
        
        try:
            timezone = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            return {
                "success": False,
                "error": f"Timezone '{timezone_str}' not found in pytz database.",
                "city": city_name,
                "timezone_string": timezone_str
            }
        
        # Get current time in that timezone
        now_utc = datetime.now(pytz.UTC)
        local_time = now_utc.astimezone(timezone)
        
        # Format the time based on user preferences
        if format_24h:
            time_format = "%H:%M:%S"
            formatted_time = local_time.strftime(time_format)
        else:
            time_format = "%I:%M:%S %p"
            formatted_time = local_time.strftime(time_format).lstrip('0')
        
        # Format date if requested
        formatted_date = ""
        if include_date:
            date_format = "%A, %B %d, %Y"
            formatted_date = local_time.strftime(date_format)
        
        # Get timezone info if requested
        timezone_info = {}
        if include_timezone_info:
            # Get timezone abbreviation
            tz_abbr = local_time.strftime('%Z')
            
            # Get UTC offset
            utc_offset = local_time.strftime('%z')
            if utc_offset:
                # Format offset as ±HH:MM
                offset_hours = int(utc_offset[:3])
                offset_minutes = utc_offset[3:]
                formatted_offset = f"{offset_hours:+03d}:{offset_minutes}"
            else:
                formatted_offset = "Unknown"
            
            # Check if DST is active
            is_dst = local_time.dst().seconds > 0 if local_time.dst() else False
            
            timezone_info = {
                "timezone": timezone_str,
                "abbreviation": tz_abbr,
                "utc_offset": formatted_offset,
                "is_dst": is_dst,
                "dst_active": "Yes" if is_dst else "No"
            }
        
        # Prepare basic result
        result = {
            "success": True,
            "city": city_name.title(),
            "local_time": formatted_time,
            "timestamp": local_time.isoformat(),
            "unix_timestamp": int(local_time.timestamp())
        }
        
        # Add date if requested
        if include_date:
            result["date"] = formatted_date
            result["date_components"] = {
                "year": local_time.year,
                "month": local_time.month,
                "day": local_time.day,
                "weekday": local_time.strftime('%A'),
                "day_of_year": local_time.timetuple().tm_yday
            }
        
        # Add timezone info if requested
        if include_timezone_info:
            result["timezone_info"] = timezone_info
        
        # Add additional details if requested
        if include_details:
            # Get city information
            city_details = city_info.get(normalized_city, {})
            
            # Calculate time in other major cities for comparison
            comparison_cities = ["London", "New York", "Tokyo", "Sydney", "Dubai"]
            comparison_times = []
            
            for comp_city in comparison_cities:
                if comp_city.lower() != normalized_city:
                    try:
                        comp_tz = pytz.timezone(city_timezone_map[comp_city.lower()])
                        comp_time = now_utc.astimezone(comp_tz)
                        comp_formatted = comp_time.strftime("%I:%M %p").lstrip('0')
                        comparison_times.append({
                            "city": comp_city,
                            "time": comp_formatted,
                            "timezone": city_timezone_map[comp_city.lower()].split('/')[-1]
                        })
                    except:
                        pass
            
            # Calculate time differences with UTC
            utc_time = now_utc.strftime("%H:%M")
            local_utc_diff = local_time.strftime('%z')
            if local_utc_diff:
                diff_hours = int(local_utc_diff[:3])
                diff_direction = "ahead of" if diff_hours > 0 else "behind" if diff_hours < 0 else "same as"
                diff_abs = abs(diff_hours)
            
            # Add all details
            result["details"] = {
                "normalized_name": normalized_city,
                "timezone_region": timezone_str.split('/')[0],
                "country": city_details.get("country", "Unknown"),
                "region": city_details.get("region", "Unknown"),
                "population": city_details.get("population", "Unknown"),
                "coordinates": "Available via geocoding API",  # Placeholder
                "current_season": get_season(local_time.month, normalized_city),
                "daylight_hours": estimate_daylight_hours(local_time, normalized_city),
                "comparison_with_other_cities": comparison_times[:3],
                "utc_reference": {
                    "utc_time": utc_time,
                    "difference_from_utc": f"{diff_abs} hours {diff_direction} UTC" if local_utc_diff else "Unknown"
                }
            }
            
            # Add fun facts for certain cities
            fun_facts = get_city_fun_facts(normalized_city)
            if fun_facts:
                result["details"]["fun_facts"] = fun_facts
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "city": city_name
        }


def get_season(month: int, city: str) -> str:
    """Determine the season based on month and hemisphere."""
    # Northern hemisphere cities
    northern_cities = ["new york", "london", "paris", "tokyo", "beijing", "moscow"]
    
    if city in northern_cities:
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"
    else:
        # Southern hemisphere or equatorial
        if month in [12, 1, 2]:
            return "Summer"
        elif month in [3, 4, 5]:
            return "Autumn"
        elif month in [6, 7, 8]:
            return "Winter"
        else:
            return "Spring"


def estimate_daylight_hours(local_time: datetime, city: str) -> str:
    """Estimate daylight hours based on season and location."""
    month = local_time.month
    
    # Very rough estimation
    if city in ["stockholm", "helsinki", "oslo"] and month in [5, 6, 7]:
        return "18-20 hours (Summer in Scandinavia)"
    elif city in ["new york", "london", "paris"]:
        if month in [12, 1]:
            return "9-10 hours"
        elif month in [6, 7]:
            return "14-15 hours"
        else:
            return "11-13 hours"
    elif city in ["singapore", "nairobi", "quito"]:
        return "12 hours year-round (near equator)"
    else:
        return "11-13 hours (typical)"


def get_city_fun_facts(city: str) -> List[str]:
    """Return fun facts about specific cities."""
    facts = {
        "london": [
            "Big Ben is actually the name of the bell, not the clock tower",
            "London has over 170 museums",
            "The London Underground is the oldest underground railway network in the world"
        ],
        "tokyo": [
            "Tokyo is the most populous metropolitan area in the world",
            "The city has the most Michelin-starred restaurants of any city",
            "Tokyo was originally named Edo"
        ],
        "new york": [
            "More than 800 languages are spoken in New York City",
            "The New York Public Library has over 50 million items",
            "Times Square is named after the New York Times"
        ],
        "paris": [
            "The Eiffel Tower was originally intended to be a temporary structure",
            "Paris has only one stop sign in the entire city",
            "The city is known as the 'City of Light' because of its early adoption of street lighting"
        ],
        "sydney": [
            "Sydney Opera House roof weighs over 161,000 tons",
            "Sydney has over 100 beaches",
            "The Sydney Harbour Bridge is nicknamed 'The Coathanger'"
        ]
    }
    
    return facts.get(city, [])


# Helper function to list all available cities
def list_available_cities() -> Dict[str, List[str]]:
    """List all cities available in the database grouped by region."""
    # This would be called separately if needed
    pass