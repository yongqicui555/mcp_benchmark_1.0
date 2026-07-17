"""Solar elevation and geometry utilities.

Pure Python — no numpy required. Same algorithm as
ionis-training/versions/common/model.py:solar_elevation_deg.
"""

import math


def solar_elevation_deg(lat: float, lon: float, hour_utc: float, day_of_year: int) -> float:
    """Compute solar elevation angle in degrees.

    Positive = sun above horizon (daylight)
    Negative = sun below horizon (night)

    Physical thresholds:
        > 0 deg:        Daylight — D-layer absorbing, F-layer ionized
        0 to -6 deg:    Civil twilight — D-layer weakening
        -6 to -12 deg:  Nautical twilight — D-layer collapsed, F-layer residual
        -12 to -18 deg: Astronomical twilight — F-layer fading
        < -18 deg:      Night — F-layer decayed

    Accuracy: ~1 degree (simplified equations, sufficient for ionospheric modeling).
    """
    # Solar declination
    dec = -23.44 * math.cos(math.radians(360.0 / 365.0 * (day_of_year + 10)))
    dec_r = math.radians(dec)
    lat_r = math.radians(lat)

    # Hour angle: degrees from solar noon
    solar_hour = hour_utc + lon / 15.0
    hour_angle = (solar_hour - 12.0) * 15.0
    ha_r = math.radians(hour_angle)

    # Solar elevation formula
    sin_elev = (
        math.sin(lat_r) * math.sin(dec_r)
        + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha_r)
    )
    sin_elev = max(-1.0, min(1.0, sin_elev))
    return math.degrees(math.asin(sin_elev))


def classify_solar(elevation: float) -> str:
    """Classify solar elevation into propagation-relevant categories."""
    if elevation > 0:
        return "DAY"
    elif elevation > -6:
        return "CIVIL_TWILIGHT"
    elif elevation > -12:
        return "NAUTICAL_TWILIGHT"
    elif elevation > -18:
        return "ASTRONOMICAL_TWILIGHT"
    else:
        return "NIGHT"


def classify_path_solar(
    tx_lat: float, tx_lon: float,
    rx_lat: float, rx_lon: float,
    hour_utc: float, day_of_year: int,
) -> tuple[str, float, float]:
    """Classify a propagation path by solar geometry at both endpoints.

    Returns:
        (classification, tx_elevation, rx_elevation)
        Classification is one of: "both_day", "cross_terminator",
        "both_twilight", or "both_dark"
    """
    tx_elev = solar_elevation_deg(tx_lat, tx_lon, hour_utc, day_of_year)
    rx_elev = solar_elevation_deg(rx_lat, rx_lon, hour_utc, day_of_year)

    tx_day = tx_elev > 0
    rx_day = rx_elev > 0

    if tx_day and rx_day:
        classification = "both_day"
    elif tx_day != rx_day:
        classification = "cross_terminator"
    elif tx_elev > -12 or rx_elev > -12:
        classification = "both_twilight"
    else:
        classification = "both_dark"

    return classification, tx_elev, rx_elev


def month_to_mid_doy(month: int) -> int:
    """Convert month (1-12) to approximate day-of-year at mid-month."""
    # Cumulative days at start of each month (non-leap)
    starts = [0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    m = max(1, min(12, month))
    return starts[m] + 15
