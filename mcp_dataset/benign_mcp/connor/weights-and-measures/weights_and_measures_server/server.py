"""Weights and Measures MCP Server.

Provides tools and resources for unit conversions and measurement reference tables.
"""

import json
from mcp.server.fastmcp import FastMCP

from .data import (
    ALL_CONVERSIONS,
    UNIT_TO_CATEGORY,
    UNIT_CATEGORIES,
    WEIGHT_TABLES,
    LENGTH_TABLES,
    VOLUME_TABLES,
)

# Create the FastMCP server
mcp = FastMCP("weights-and-measures")


# Tools

@mcp.tool()
def convert_unit(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a value from one unit of measurement to another.

    Supports weight (avoirdupois, troy, apothecaries', metric),
    length (imperial/US, metric), and volume (US fluid, imperial fluid, metric) conversions.

    Args:
        value: The numeric value to convert
        from_unit: The unit to convert from (e.g., 'pound', 'kilogram', 'mile', 'gallon')
        to_unit: The unit to convert to (e.g., 'gram', 'pound', 'kilometer', 'liter')

    Returns:
        JSON string with conversion result and formula
    """
    from_unit = from_unit.lower().replace(" ", "_")
    to_unit = to_unit.lower().replace(" ", "_")

    # Validate units exist
    if from_unit not in ALL_CONVERSIONS:
        available_units = ", ".join(sorted(ALL_CONVERSIONS.keys()))
        return json.dumps({
            "error": f"Unknown unit '{from_unit}'. Available units: {available_units}"
        }, indent=2)

    if to_unit not in ALL_CONVERSIONS:
        available_units = ", ".join(sorted(ALL_CONVERSIONS.keys()))
        return json.dumps({
            "error": f"Unknown unit '{to_unit}'. Available units: {available_units}"
        }, indent=2)

    # Check if units are in the same category
    from_category = UNIT_TO_CATEGORY[from_unit]
    to_category = UNIT_TO_CATEGORY[to_unit]

    if from_category != to_category:
        return json.dumps({
            "error": f"Cannot convert between different categories. "
                    f"'{from_unit}' is a {from_category} unit, "
                    f"'{to_unit}' is a {to_category} unit."
        }, indent=2)

    # Perform conversion (convert to base unit, then to target unit)
    base_value = value * ALL_CONVERSIONS[from_unit]
    result = base_value / ALL_CONVERSIONS[to_unit]

    return json.dumps({
        "input": {
            "value": value,
            "unit": from_unit
        },
        "output": {
            "value": result,
            "unit": to_unit
        },
        "formula": f"{value} {from_unit} × {ALL_CONVERSIONS[from_unit]} ÷ {ALL_CONVERSIONS[to_unit]} = {result} {to_unit}"
    }, indent=2)


@mcp.tool()
def get_conversion_factor(from_unit: str, to_unit: str) -> str:
    """Get the conversion factor between two units of measurement.

    Returns the multiplier needed to convert from one unit to another.

    Args:
        from_unit: The unit to convert from
        to_unit: The unit to convert to

    Returns:
        JSON string with conversion factor and usage example
    """
    from_unit = from_unit.lower().replace(" ", "_")
    to_unit = to_unit.lower().replace(" ", "_")

    # Validate units exist
    if from_unit not in ALL_CONVERSIONS:
        available_units = ", ".join(sorted(ALL_CONVERSIONS.keys()))
        return json.dumps({
            "error": f"Unknown unit '{from_unit}'. Available units: {available_units}"
        }, indent=2)

    if to_unit not in ALL_CONVERSIONS:
        available_units = ", ".join(sorted(ALL_CONVERSIONS.keys()))
        return json.dumps({
            "error": f"Unknown unit '{to_unit}'. Available units: {available_units}"
        }, indent=2)

    # Check if units are in the same category
    from_category = UNIT_TO_CATEGORY[from_unit]
    to_category = UNIT_TO_CATEGORY[to_unit]

    if from_category != to_category:
        return json.dumps({
            "error": f"Cannot get conversion factor between different categories. "
                    f"'{from_unit}' is a {from_category} unit, "
                    f"'{to_unit}' is a {to_category} unit."
        }, indent=2)

    # Calculate conversion factor
    factor = ALL_CONVERSIONS[from_unit] / ALL_CONVERSIONS[to_unit]

    return json.dumps({
        "from_unit": from_unit,
        "to_unit": to_unit,
        "conversion_factor": factor,
        "usage": f"To convert from {from_unit} to {to_unit}, multiply by {factor}",
        "example": f"1 {from_unit} = {factor} {to_unit}"
    }, indent=2)


@mcp.tool()
def list_units(category: str = None) -> str:
    """List all available units for conversion, optionally filtered by category.

    Args:
        category: Optional category to filter by: 'weight', 'length', or 'volume'

    Returns:
        JSON string with list of units
    """
    if category:
        category = category.lower()
        if category not in UNIT_CATEGORIES:
            return json.dumps({
                "error": f"Unknown category '{category}'. Available categories: weight, length, volume"
            }, indent=2)

        units = UNIT_CATEGORIES[category]
        return json.dumps({
            "category": category,
            "units": sorted(units),
            "count": len(units)
        }, indent=2)
    else:
        return json.dumps({
            "categories": {
                cat: sorted(units)
                for cat, units in UNIT_CATEGORIES.items()
            },
            "total_units": len(ALL_CONVERSIONS)
        }, indent=2)


# Resources

@mcp.resource("weights://tables/avoirdupois")
def get_avoirdupois_table() -> str:
    """Avoirdupois (Commercial) Weight Table - pounds, ounces, grains"""
    return json.dumps(WEIGHT_TABLES["avoirdupois"], indent=2)


@mcp.resource("weights://tables/troy")
def get_troy_table() -> str:
    """Troy Weight Table - precious metals weight (troy ounces, pennyweights)"""
    return json.dumps(WEIGHT_TABLES["troy"], indent=2)


@mcp.resource("weights://tables/apothecaries")
def get_apothecaries_table() -> str:
    """Apothecaries' Weight Table - pharmacy weight (drams, scruples)"""
    return json.dumps(WEIGHT_TABLES["apothecaries"], indent=2)


@mcp.resource("weights://tables/metric-weight")
def get_metric_weight_table() -> str:
    """Metric Weight Table - kilograms, grams"""
    return json.dumps(WEIGHT_TABLES["metric"], indent=2)


@mcp.resource("weights://tables/cross-system-weight")
def get_cross_system_weight_table() -> str:
    """Cross-System Weight Conversions - conversions between different weight systems"""
    return json.dumps(WEIGHT_TABLES["cross_system"], indent=2)


@mcp.resource("length://tables/imperial-us")
def get_imperial_us_table() -> str:
    """Imperial/US Length Table - miles, yards, feet, inches"""
    return json.dumps(LENGTH_TABLES["imperial_us"], indent=2)


@mcp.resource("length://tables/metric")
def get_metric_length_table() -> str:
    """Metric Length Table - kilometers, meters, centimeters"""
    return json.dumps(LENGTH_TABLES["metric"], indent=2)


@mcp.resource("length://tables/cross-system")
def get_cross_system_length_table() -> str:
    """Cross-System Length Conversions - imperial/metric conversions"""
    return json.dumps(LENGTH_TABLES["cross_system"], indent=2)


@mcp.resource("volume://tables/us-fluid")
def get_us_fluid_table() -> str:
    """US Fluid Measurements Table - gallons, quarts, pints, cups"""
    return json.dumps(VOLUME_TABLES["us_fluid"], indent=2)


@mcp.resource("volume://tables/imperial-fluid")
def get_imperial_fluid_table() -> str:
    """Imperial Fluid Measurements Table"""
    return json.dumps(VOLUME_TABLES["imperial_fluid"], indent=2)


@mcp.resource("volume://tables/metric-volume")
def get_metric_volume_table() -> str:
    """Metric Volume Table - liters, milliliters"""
    return json.dumps(VOLUME_TABLES["metric"], indent=2)


@mcp.resource("volume://tables/cross-system-volume")
def get_cross_system_volume_table() -> str:
    """Cross-System Volume Conversions - conversions between different volume systems"""
    return json.dumps(VOLUME_TABLES["cross_system"], indent=2)


@mcp.resource("units://all")
def get_all_units() -> str:
    """Complete list of all supported units organized by category"""
    return json.dumps({
        "categories": UNIT_CATEGORIES,
        "total_units": len(ALL_CONVERSIONS),
        "description": "All supported units for weight, length, and volume conversions"
    }, indent=2)
