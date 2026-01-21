"""Application constants."""

# API Configuration
API_PREFIX = "/data"

# UNESCO Regional Groups
class Region:
    """UNESCO Regional Group constants."""
    EUROPE_NORTH_AMERICA = "Europe & North America"
    ARAB_STATES = "Arab States"
    AFRICA = "Africa"
    LATIN_AMERICA_CARIBBEAN = "Latin America & the Caribbean"
    ASIA_PACIFIC = "Asia & the Pacific"

# Map JSON keys to display names
REGION_DISPLAY_NAMES = {
    "EUROPE_NORTH_AMERICA": Region.EUROPE_NORTH_AMERICA,
    "ARAB_STATES": Region.ARAB_STATES,
    "AFRICA": Region.AFRICA,
    "LATIN_AMERICA_CARIBBEAN": Region.LATIN_AMERICA_CARIBBEAN,
    "ASIA_PACIFIC": Region.ASIA_PACIFIC,
}