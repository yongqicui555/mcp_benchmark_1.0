"""Weights and Measures conversion data and tables."""

# Base conversion factors to standard units
# Weight: converting to grams
# Length: converting to meters
# Volume: converting to liters

WEIGHT_CONVERSIONS = {
    # Avoirdupois (Commercial) Weight
    "gross_ton": 2240 * 453.59237,  # to grams
    "net_ton": 2000 * 453.59237,  # to grams
    "pound": 453.59237,  # to grams
    "ounce": 28.349523125,  # to grams
    "grain": 0.06479891,  # to grams

    # Troy Weight
    "troy_pound": 373.2417216,  # to grams
    "troy_ounce": 31.1034768,  # to grams
    "pennyweight": 1.55517384,  # to grams
    "troy_grain": 0.06479891,  # to grams (same as avoirdupois grain)

    # Apothecaries' Weight
    "apothecaries_pound": 373.2417216,  # to grams (same as troy)
    "apothecaries_ounce": 31.1034768,  # to grams
    "dram": 3.8879346,  # to grams
    "scruple": 1.2959782,  # to grams
    "apothecaries_grain": 0.06479891,  # to grams

    # Metric Weight
    "metric_ton": 1000000,  # to grams
    "kilogram": 1000,  # to grams
    "gram": 1,  # base unit
    "decigram": 0.1,  # to grams
    "centigram": 0.01,  # to grams
    "milligram": 0.001,  # to grams
}

LENGTH_CONVERSIONS = {
    # Imperial/US Length
    "mile": 1609.344,  # to meters
    "yard": 0.9144,  # to meters
    "foot": 0.3048,  # to meters
    "inch": 0.0254,  # to meters

    # Metric Length
    "kilometer": 1000,  # to meters
    "meter": 1,  # base unit
    "decimeter": 0.1,  # to meters
    "centimeter": 0.01,  # to meters
    "millimeter": 0.001,  # to meters
}

VOLUME_CONVERSIONS = {
    # US Fluid Measurements
    "us_gallon": 3.785411784,  # to liters
    "gallon": 3.785411784,  # to liters (default to US)
    "quart": 0.946352946,  # to liters
    "pint": 0.473176473,  # to liters
    "fluid_ounce": 0.0295735295625,  # to liters
    "cup": 0.2365882365,  # to liters
    "tablespoon": 0.01478676478125,  # to liters
    "teaspoon": 0.00492892159375,  # to liters

    # Imperial Fluid Measurements
    "imperial_gallon": 4.54609,  # to liters
    "imperial_quart": 1.1365225,  # to liters
    "imperial_pint": 0.56826125,  # to liters
    "imperial_fluid_ounce": 0.0284130625,  # to liters

    # Metric Volume
    "cubic_meter": 1000,  # to liters
    "liter": 1,  # base unit
    "deciliter": 0.1,  # to liters
    "centiliter": 0.01,  # to liters
    "milliliter": 0.001,  # to liters

    # Cubic measurements
    "cubic_inch": 0.016387064,  # to liters
    "cubic_foot": 28.316846592,  # to liters
}

# Categories for organizing units
UNIT_CATEGORIES = {
    "weight": list(WEIGHT_CONVERSIONS.keys()),
    "length": list(LENGTH_CONVERSIONS.keys()),
    "volume": list(VOLUME_CONVERSIONS.keys()),
}

# Reverse lookup
UNIT_TO_CATEGORY = {}
for category, units in UNIT_CATEGORIES.items():
    for unit in units:
        UNIT_TO_CATEGORY[unit] = category

# All conversions combined
ALL_CONVERSIONS = {
    **WEIGHT_CONVERSIONS,
    **LENGTH_CONVERSIONS,
    **VOLUME_CONVERSIONS,
}

# Reference tables
WEIGHT_TABLES = {
    "avoirdupois": {
        "description": "Avoirdupois (Commercial) Weight",
        "conversions": [
            "1 gross ton = 2,240 pounds",
            "1 net ton = 2,000 pounds",
            "1 pound = 16 ounces or 7,000 grains",
            "1 ounce = 437.5 grains",
        ]
    },
    "troy": {
        "description": "Troy Weight (used for precious metals)",
        "conversions": [
            "1 pound = 12 ounces or 5,760 grains",
            "1 ounce = 20 pennyweights or 480 grains",
            "1 pennyweight = 24 grains",
            "1 troy ounce = 1.09714 ounces avoirdupois",
        ]
    },
    "apothecaries": {
        "description": "Apothecaries' Weight (used in pharmacy)",
        "conversions": [
            "1 pound = 12 ounces or 5,760 grains",
            "1 ounce = 8 drams or 480 grains",
            "1 dram = 3 scruples or 60 grains",
        ]
    },
    "metric": {
        "description": "Metric Weight",
        "conversions": [
            "1 metric ton = 1,000 kilograms",
            "1 kilogram = 1,000 grams",
            "1 gram = 10 decigrams = 100 centigrams = 1,000 milligrams",
        ]
    },
    "cross_system": {
        "description": "Cross-System Weight Conversions",
        "conversions": [
            "1 pound avoirdupois = 453.6 grams",
            "1 kilogram = 2.2046 pounds avoirdupois",
            "1 troy ounce = 31.1035 grams",
        ]
    }
}

LENGTH_TABLES = {
    "imperial_us": {
        "description": "Imperial/US Length Measurements",
        "conversions": [
            "1 mile = 1,760 yards or 5,280 feet",
            "1 yard = 3 feet or 36 inches",
            "1 foot = 12 inches",
        ]
    },
    "metric": {
        "description": "Metric Length",
        "conversions": [
            "1 kilometer = 1,000 meters",
            "1 meter = 10 decimeters = 100 centimeters = 1,000 millimeters",
        ]
    },
    "cross_system": {
        "description": "Cross-System Length Conversions",
        "conversions": [
            "1 mile = 1.609 kilometers",
            "1 yard = 0.9144 meters",
            "1 inch = 25.4 millimeters",
            "1 meter = 39.37 inches",
        ]
    }
}

VOLUME_TABLES = {
    "us_fluid": {
        "description": "US Fluid Measurements",
        "conversions": [
            "1 gallon = 4 quarts = 8 pints = 128 fluid ounces",
            "1 quart = 2 pints = 32 fluid ounces",
            "1 pint = 2 cups = 16 fluid ounces",
            "1 cup = 8 fluid ounces = 16 tablespoons",
            "1 tablespoon = 3 teaspoons",
            "1 US gallon = 231 cubic inches",
        ]
    },
    "imperial_fluid": {
        "description": "Imperial Fluid Measurements",
        "conversions": [
            "1 imperial gallon = 1.2 US gallons",
            "1 imperial gallon = 4 imperial quarts",
            "1 imperial quart = 2 imperial pints",
        ]
    },
    "metric": {
        "description": "Metric Volume",
        "conversions": [
            "1 cubic meter = 1,000 liters",
            "1 liter = 10 deciliters = 100 centiliters = 1,000 milliliters",
        ]
    },
    "cross_system": {
        "description": "Cross-System Volume Conversions",
        "conversions": [
            "1 US gallon = 3.785 liters",
            "1 imperial gallon = 4.546 liters",
            "1 liter = 0.264 US gallons",
            "1 cubic inch = 16.387 milliliters",
        ]
    }
}
