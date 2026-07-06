import asyncio
import logging
import os
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("disaster_relief_mcp")

# Initialize FastMCP server
mcp = FastMCP("Disaster Relief Service")

@mcp.tool()
def get_shelters(location: str, disaster_type: str) -> str:
    """Finds nearby emergency shelters for a given location and disaster type.
    
    Args:
        location: The user's current city or region.
        disaster_type: The type of disaster (e.g., flood, wildfire, earthquake).
    """
    logger.info(f"get_shelters called for location={location}, disaster={disaster_type}")
    loc = location.lower()
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

@mcp.tool()
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

@mcp.tool()
def get_weather_alerts(location: str) -> str:
    """Retrieves current weather alerts and hazard levels for a location.
    
    Args:
        location: The user's current city or region.
    """
    logger.info(f"get_weather_alerts called for location={location}")
    loc = location.lower()
    if "valley" in loc or "forest" in loc or "california" in loc:
        return f"ALERTS for {location}: RED FLAG WARNING (Extreme fire danger, high winds). Evacuation warning in effect for Zone A."
    return f"ALERTS for {location}: Flood Warning active. River levels rising. Avoid low-lying roads."

@mcp.tool()
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

if __name__ == "__main__":
    logger.info("Starting Disaster Relief FastMCP Server...")
    mcp.run()
