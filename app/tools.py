"""
Disaster Relief Tools

Plain Python functions that mirror the MCP server tools.
These are used directly by ADK agents to avoid the stdio-based MCP session
startup issues on Windows (SelectorEventLoop subprocess limitations).

The mcp_server.py file is kept for standalone MCP server usage.
"""
import logging

logger = logging.getLogger("disaster_relief_tools")


def get_shelters(location: str, disaster_type: str) -> str:
    """Finds nearby emergency shelters for a given location and disaster type.

    Args:
        location: The user's current city or region.
        disaster_type: The type of disaster (e.g., flood, wildfire, earthquake).
    """
    logger.info(f"get_shelters called for location={location}, disaster={disaster_type}")
    dis = disaster_type.lower()

    if "flood" in dis:
        return (
            f"Shelters in {location} for floods:\n"
            f"1. Central High School (Elevated area, Capacity: 500, Status: OPEN, Pets Allowed: Yes, Coordinates: 34.05,-118.24)\n"
            f"2. Hillside Community Center (Capacity: 300, Status: OPEN, Pets Allowed: No, Coordinates: 34.07,-118.26)"
        )
    elif "wildfire" in dis:
        return (
            f"Shelters in {location} for wildfires:\n"
            f"1. Westside Arena (Safe zone, Capacity: 1000, Status: OPEN, Pets Allowed: Yes)\n"
            f"2. County Fairgrounds (Large capacity, Status: OPEN, Livestock Accepted: Yes)"
        )
    else:
        return (
            f"Emergency shelters in {location}:\n"
            f"1. Civic Center Plaza (General shelter, Capacity: 400, Status: OPEN)\n"
            f"2. Safe Haven Church (Capacity: 150, Status: OPEN)"
        )


def get_hospitals(location: str) -> str:
    """Finds nearby hospitals and emergency medical services for a location.

    Args:
        location: The user's current city or region.
    """
    logger.info(f"get_hospitals called for location={location}")
    return (
        f"Hospitals and medical stations in {location}:\n"
        f"1. City General Hospital (Emergency Room 24/7, Status: OPERATIONAL, Trauma Level: 1)\n"
        f"2. Red Cross Medical Tent 3 (Location: Near Town Hall, Status: ACTIVE for minor injuries)"
    )


def get_weather_alerts(location: str, disaster_type: str = "general") -> str:
    """Retrieves current weather alerts and hazard levels for a location.

    Args:
        location: The user's current city or region.
        disaster_type: The type of disaster (e.g., flood, wildfire, earthquake). Defaults to 'general'.
    """
    logger.info(f"get_weather_alerts called for location={location}, disaster={disaster_type}")
    dis = disaster_type.lower()

    if "wildfire" in dis or "fire" in dis:
        return (
            f"🔴 RED FLAG WARNING for {location}: Extreme wildfire danger.\n"
            f"- Wind speeds: 40-60 mph gusts expected\n"
            f"- Humidity: Below 10% (critical fire weather)\n"
            f"- Evacuation Orders: Zone A and B — LEAVE IMMEDIATELY\n"
            f"- Evacuation Warnings: Zone C and D — BE READY TO LEAVE\n"
            f"- Air Quality Index: HAZARDOUS (500+) — Do not go outside without N95 mask"
        )
    elif "flood" in dis:
        return (
            f"🔵 FLOOD WARNING for {location}:\n"
            f"- River levels: 2.3m above flood stage and rising\n"
            f"- Flash flood watch in effect until midnight\n"
            f"- Avoid all low-lying roads and underpasses\n"
            f"- Evacuation Orders: Riverside and Creek districts — LEAVE NOW"
        )
    elif "earthquake" in dis:
        return (
            f"⚠️ EARTHQUAKE ALERT for {location}:\n"
            f"- Magnitude 5.8 detected — aftershocks possible\n"
            f"- Tsunami watch: NOT in effect\n"
            f"- Check for gas leaks before re-entering buildings\n"
            f"- Emergency shelters activated at civic centers"
        )
    elif "cyclone" in dis or "hurricane" in dis or "storm" in dis:
        return (
            f"🌀 CYCLONE/STORM WARNING for {location}:\n"
            f"- Category 3 storm approaching — landfall in 6-8 hours\n"
            f"- Mandatory evacuation: Coastal zones A and B\n"
            f"- Storm surge: 4-6 feet above normal tide levels\n"
            f"- Wind speeds: 120 mph sustained"
        )
    else:
        return (
            f"⚠️ EMERGENCY ALERT for {location}:\n"
            f"- General emergency in effect — follow local authority instructions\n"
            f"- Monitor local radio and emergency broadcasts\n"
            f"- Evacuation routes are active on major highways"
        )


def get_supply_checklist(disaster_type: str) -> str:
    """Gets the standard recommended emergency supply checklist for a specific disaster.

    Args:
        disaster_type: The type of disaster (e.g., flood, wildfire, earthquake, cyclone).
    """
    logger.info(f"get_supply_checklist called for disaster={disaster_type}")
    dis = disaster_type.lower()
    common = (
        "- 3-day supply of water (1 gallon per person per day)\n"
        "- Non-perishable food items (canned goods, energy bars)\n"
        "- Flashlight and extra batteries\n"
        "- First aid kit\n"
        "- Whistle to signal for help\n"
        "- Local maps and emergency plan document\n"
        "- Cell phone with chargers and backup power bank"
    )

    if "flood" in dis:
        return (
            f"Emergency Supply Checklist for FLOODS:\n"
            f"{common}\n"
            f"- Waterproof boots and rubber gloves\n"
            f"- Personal sanitation items\n"
            f"- Important documents in a waterproof sealable bag"
        )
    elif "wildfire" in dis:
        return (
            f"Emergency Supply Checklist for WILDFIRES:\n"
            f"{common}\n"
            f"- N95 or respirator masks for smoke protection\n"
            f"- Goggles for eye protection\n"
            f"- Sturdy, heat-resistant shoes or boots"
        )
    else:
        return (
            f"General Emergency Supply Checklist:\n"
            f"{common}"
        )
