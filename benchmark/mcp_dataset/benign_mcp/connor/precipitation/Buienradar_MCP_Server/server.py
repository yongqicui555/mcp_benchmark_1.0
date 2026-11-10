import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("precipitation")


USER_AGENT = "persoonlijk-gebruik"


def format_url(lat: float, lon: float) -> str:
    lat = round(lat, 2)
    lon = round(lon, 2)
    return f"https://gadgets.buienradar.nl/data/raintext/?lat={lat}&lon={lon}"


async def make_request(url) -> str | None:
    headers = {"User-Agent": USER_AGENT}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)
            response.raise_for_status()
    except Exception as e:
        return None

    return response.text


def format_response(data: str) -> str:
    result = ["time, mm per hour"]
    for line in data.strip().split('\n'):
        intensity, time = line.split("|")
        intensity = int(intensity)
        mm_per_hour = round(10 ** ((intensity - 109) / 32), 1)
        result.append(f"{time}, {mm_per_hour}")

    return "\n".join(result)


@mcp.tool()
async def get_precipitation_for(lat: float, lon: float) -> str:
    """Fetches precipitation data for the next 2 hours from Buienradar."""
    data = await make_request(format_url(lat, lon))
    if not data:
        return "Could not get precipitation data."
    
    return format_response(data)


if __name__ == "__main__":
    mcp.run(transport="stdio")
