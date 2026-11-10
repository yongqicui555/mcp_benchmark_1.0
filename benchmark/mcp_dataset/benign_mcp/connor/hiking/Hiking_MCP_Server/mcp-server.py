from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from bs4 import BeautifulSoup

# Initialize FastMCP server
mcp = FastMCP("wikiloc")

# Constants
WIKILOC_API_BASE = "https://es.wikiloc.com/wikiloc/find.do"
USER_AGENT = "wikiloc-app/1.0"
difficulty_translation = {
        "Fácil": "Easy",
        "Moderado": "Moderate",
        "Difícil": "Hard",
        "Muy Difícil": "Very Hard",
        "Solo expertos": "Experts Only"
}


async def make_wikiloc_request(url: str, params: dict) -> str | dict[str, Any] | None:
    """Make a request to Wikiloc and return either HTML or JSON based on response."""
    headers = {
        "User-Agent": USER_AGENT
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                return response.text  # HTML u otro formato
        except Exception as e:
            print(f"Error en la solicitud: {e}")
            return None


def format_route(route: dict) -> str:
    """Format a route feature into a readable string with the new keys."""
    difficulty = difficulty_translation.get(route.get("Dificultad técnica", ""), "Unknown")
    return f"""
Title: {route['title']}
URL: {route['url']}
Distance: {route['Distancia']} 
Elevation gain: {route['Desnivel positivo']}
Elevation loss: {route['Desnivel negativo']}
Difficulty : {difficulty}
Maximum altitude: {route['Altitud máxima']}
TrailRank: {route['TrailRank']}
Minimum altitude: {route['Altitud mínima']}
Route type: {route['Tipo de ruta']}
"""


def extract_trail_statistics(html: str) -> dict:
    """Extracts trail statistics from Wikiloc HTML."""
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find("section", id="trail-data")

    if not section:
        return {}

    data = {}
    for item in section.select("dl.data-items .d-item"):
        dt = item.find("dt")
        dd = item.find("dd")
        if not (dt and dd):
            continue

        key = dt.get_text(strip=True).replace('\xa0', ' ')

        # Caso especial: TrailRank
        if "TrailRank" in key:
            # Buscar solo el primer <span> con número
            first_span = dd.find("span")
            value = first_span.get_text(strip=True) if first_span else ''
        else:
            # Para otros casos, extraer todo el texto del dd
            value = dd.get_text(strip=True).replace('\xa0', ' ')

        data[key] = value

    return data


@mcp.tool()
async def get_routes(query: str, sw_lat: float, sw_lon: float, ne_lat: float, ne_lon: float, page: int = 1, max_results: int = 5) -> str:
    """Search for routes on Wikiloc based on geographical area.

    Args:
        query: Search query (e.g. "Vall de Núria - Ribes de Freser").
        sw_lat: Latitude of the southwest corner of the bounding box.
        sw_lon: Longitude of the southwest corner of the bounding box.
        ne_lat: Latitude of the northeast corner of the bounding box.
        ne_lon: Longitude of the northeast corner of the bounding box.
        page: The page of results to fetch.
        max_results: The maximum number of results to return.


    Output: 
        "title": Name of the trail,
        "url": Url,
        "distance_km": Distance in KM,
        "slope": Slope of the trail in meters,
        "author": Author of the trail,
        "location": Location of the trail,
        "trailrank": Punctuation of the trail.
    """
    params = {
        "event": "map",
        "to": 25,
        "sw": f"{sw_lat},{sw_lon}",
        "ne": f"{ne_lat},{ne_lon}",
        "q": query,
        "page": page
    }

    # Make the request to the Wikiloc API
    url = WIKILOC_API_BASE
    data = await make_wikiloc_request(url, params)

    if not data or "spas" not in data:
        return "Unable to fetch routes or no routes found."

    if not data["spas"]:
        return "No routes found for this search."

    # Extract and sort the routes by TrailRank (descending order)
    routes = []
    for spa in data["spas"]:
        route = {
            "title": spa["name"],
            "url": f"https://es.wikiloc.com{spa['prettyURL']}",
            "distance_km": spa.get("distance"),
            "slope": spa.get("slope"),
            "author": spa.get("author"),
            "location": spa.get("near"),
            "trailrank": spa.get("trailrank")
        }
        
        # Obtain the route details (HTML response)
        response = await make_wikiloc_request(route["url"], {})
        if isinstance(response, str):  # Ensure we got HTML response
            details = extract_trail_statistics(response)
            # Add details to the 'route' dictionary
            route.update(details)
        
        routes.append(route)

    # Format the top results
    top_routes = [format_route(route) for route in routes[:max_results]]
    
    return "\n---\n".join(top_routes)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
