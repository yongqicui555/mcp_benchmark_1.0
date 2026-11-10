#import
import os
from pathlib import Path
import base64
import hashlib
import secrets
import requests
import asyncio
import aiohttp
import webbrowser
import threading
import time
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

from mcp_server_evefleet.sso.shared_flow import print_auth_url
from mcp_server_evefleet.sso.shared_flow import send_token_request
from mcp_server_evefleet.sso.shared_flow import handle_sso_token_response_token
from mcp_server_evefleet.config_load import CONFIG
from platformdirs import user_config_dir

SSO_clientid = CONFIG['SSO_clientid']
SSO_callback = CONFIG['SSO_callback']

# Global variable to store the authorization code
auth_code_result = None

# App-specific config dir for storing refresh token cross-platform
APP_NAME = "mcp_server_evefleet"
APP_AUTHOR = "mcp_server_evefleet"

def _default_token_path() -> Path:
    cfg_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "refresh_token.txt"

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture the OAuth callback"""
    
    def do_GET(self):
        global auth_code_result
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            auth_code_result = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <html>
            <head><title>EVE SSO Authentication</title></head>
            <body>
                <h1>Authentication Successful!</h1>
                <p>You can now close this window and return to the application.</p>
                <script>window.close();</script>
            </body>
            </html>
            ''')
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <html>
            <head><title>EVE SSO Authentication Error</title></head>
            <body>
                <h1>Authentication Error</h1>
                <p>No authorization code received. Please try again.</p>
            </body>
            </html>
            ''')
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_callback_server(port=8080, timeout=300):
    """Start a local HTTP server to capture OAuth callback"""
    global auth_code_result
    auth_code_result = None
    
    server = HTTPServer(('localhost', port), CallbackHandler)
    server.timeout = timeout
    
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return server, server_thread

def wait_for_callback(server, timeout=300):
    """Wait for the OAuth callback and return the authorization code"""
    global auth_code_result
    
    start_time = time.time()
    while auth_code_result is None and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    server.shutdown()
    
    if auth_code_result:
        return auth_code_result
    else:
        raise TimeoutError("Authentication timeout - no callback received")

def get_auth_url_with_callback(client_id, code_challenge, callback_url="http://localhost:8080/callback"):
    """Generate authentication URL with local callback"""
    base_auth_url = "https://login.eveonline.com/v2/oauth/authorize/"
    params = {
        "response_type": "code",
        "redirect_uri": callback_url,
        "client_id": client_id,
        "scope": "esi-location.read_location.v1 esi-location.read_ship_type.v1 esi-fleets.read_fleet.v1 esi-fleets.write_fleet.v1 esi-ui.open_window.v1 esi-ui.write_waypoint.v1 esi-location.read_online.v1",
        "state": "unique-state"
    }

    if code_challenge:
        params.update({
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        })

    from urllib.parse import urlencode
    string_params = urlencode(params)
    full_auth_url = "{}?{}".format(base_auth_url, string_params)
    
    return full_auth_url

def get_refresh_token(file_name: str | None = None, reset: bool = False, use_browser: bool = True):
    """
    Get refresh token for EVE SSO authentication
    
    Args:
        file_name (str): File to store refresh token
        reset (bool): Force new authentication even if token exists
        use_browser (bool): Use browser-based authentication (default: True)
    
    Returns:
        tuple: (refresh_token, access_token, character_id, character_name)
    """
    # Resolve token path
    if file_name:
        token_path = Path(file_name)
        # Treat bare filename as request for default app location
        if token_path.name == 'refresh_token.txt' and (not token_path.parent or str(token_path.parent) in ('.', '')):
            token_path = _default_token_path()
    else:
        token_path = _default_token_path()

    # Backward compatibility: prefer existing CWD token if app path missing
    cwd_token = Path('refresh_token.txt')
    if not token_path.exists() and cwd_token.exists() and not reset:
        token_path = cwd_token

    if not token_path.is_file() or reset:
        random = base64.urlsafe_b64encode(secrets.token_bytes(32))
        m = hashlib.sha256()
        m.update(random)
        d = m.digest()
        code_challenge = base64.urlsafe_b64encode(d).decode().replace("=", "")
        client_id = SSO_clientid
        code_verifier = random
        
        if use_browser and SSO_callback.startswith("http://localhost"):
            # Browser-based authentication with localhost callback server
            try:
                
                # Start callback server
                server, server_thread = start_callback_server()
                
                # Generate auth URL with local callback
                auth_url = get_auth_url_with_callback(client_id, code_challenge, SSO_callback)
                
                
                # Open browser
                webbrowser.open(auth_url)
                
                # Wait for callback
                auth_code = wait_for_callback(server)
                
                
            except Exception as e:
                use_browser = False
        elif use_browser and SSO_callback.startswith("eveauth://"):
            # Custom scheme authentication (recommended by CCP)
            try:
                
                # Generate auth URL with custom scheme
                auth_url = get_auth_url_with_callback(client_id, code_challenge, SSO_callback)
                
                
                # Open browser
                webbrowser.open(auth_url)
                
                # For custom schemes, we need manual input as fallback
                auth_code = input("Enter the authorization code here (or press Enter if it was handled automatically): ").strip()
                
                # If no code was entered, we might need to implement custom scheme handling
                if not auth_code:
                    use_browser = False
                
            except Exception as e:
                use_browser = False
        elif use_browser:
            # For other callback types, use manual authentication
            use_browser = False
        
        if not use_browser:
            # Manual authentication (original method)
            print_auth_url(client_id, code_challenge=code_challenge, redirect_uri=SSO_callback)
            auth_code = input("Copy the \"code\" query parameter and enter it here: ")
        
        # Exchange code for tokens
        form_values = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": auth_code,
            "code_verifier": code_verifier
        }
        res = send_token_request(form_values)
        refresh_token, access_token, character_id, character_name = handle_sso_token_response_token(res)
    else:
        # Use existing refresh token
        with token_path.open('r', encoding='utf-8') as f:
            refresh_token = f.read()
        form_values = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": SSO_clientid
        }
        try:
            res = send_token_request(form_values)
            refresh_token, access_token, character_id, character_name = handle_sso_token_response_token(res)
        except Exception as e:
            return get_refresh_token(str(token_path), reset=True, use_browser=use_browser)

    # Persist token to a proper path
    try:
        # If user provided a custom path (with a directory), honor it; otherwise use default app path
        if file_name and Path(file_name).parent not in (Path('.'), Path('')) and Path(file_name).parent != Path('.').resolve():
            final_path = Path(file_name)
        else:
            final_path = _default_token_path()
        final_path.parent.mkdir(parents=True, exist_ok=True)
        with final_path.open('w', encoding='utf-8') as f:
            f.write(refresh_token)
    except Exception as e:
        pass
    character_id = int(character_id)
    return refresh_token, access_token, character_id, character_name

#get char info
def get_char_info(character_id):
    sso_path = ("https://esi.evetech.net/latest/characters/{}/?datasource=tranquility".format(character_id))
    res = requests.get(sso_path)
    res.raise_for_status()
    data = res.json()
    return data

#get char location
def get_sso_location(access_token, character_id):
    sso_path = ("https://esi.evetech.net/latest/characters/{}/location/?datasource=tranquility".format(character_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    res = requests.get(sso_path, headers=headers)
    #print("\nMade request to {} with headers: "
    #        "{}".format(sso_path, res.request.headers))
    res.raise_for_status()

    data = res.json()
    return data['solar_system_id']

#get station info
def get_station_info(station_id):
    sso_path = ("https://esi.evetech.net/latest/universe/stations/{}/?datasource=tranquility".format(station_id))
    res = requests.get(sso_path)
    res.raise_for_status()
    data = res.json()
    return data

#get route
def get_route(origin_id, destination_id, flag='shortest'):
    assert flag in ['shortest','secure','insecure']
    sso_path = ("https://esi.evetech.net/latest/route/{}/{}?datasource=tranquility&flag={}".format(origin_id, destination_id,flag))
    res = requests.get(sso_path)
    res.raise_for_status()
    data = res.json()
    return data

#get stargate info
def get_stargate_info(stargate_id):
    sso_path = (f'https://esi.evetech.net/latest/universe/stargates/{stargate_id}/?datasource=tranquility')
    res = requests.get(sso_path)
    res.raise_for_status()
    data = res.json()
    return data

#get system info
def get_system_info(system_id):
    sso_path = (f'https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility&language=en')
    res = requests.get(sso_path)
    res.raise_for_status()
    data = res.json()
    return data

#post bulk name->id
def post_name2id(names_list):
    '''
    {
    "characters": [
        {
        "id": 2112625428,
        "name": "CCP Zoetrope"
        },
        {
        "id": 2113359448,
        "name": "RS sol"
        }
    ]
    }
    '''
    sso_path = ("https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en")
    res = requests.post(sso_path, json=names_list)
    res.raise_for_status()
    data = res.json()
    return data

#post bulk id->name
def post_id2name(ids_list):
    '''
    [
    {
        "category": "solar_system",
        "id": 30000142,
        "name": "Jita"
    },
    {
        "category": "character",
        "id": 95465499,
        "name": "CCP Bartender"
    }
    ]
    '''
    sso_path = ("https://esi.evetech.net/latest/universe/names/?datasource=tranquility")
    res = requests.post(sso_path, json=ids_list)
    res.raise_for_status()
    data = res.json()
    return data

#set waypoint
def post_setwaypoint(access_token, destination_id, add_to_beginning=True, clear_other_waypoints=False):
    #https://esi.evetech.net/latest/ui/autopilot/waypoint/?add_to_beginning=false&clear_other_waypoints=true&datasource=tranquility&destination_id=30000861
    add_to_beginning = str(add_to_beginning).lower()
    clear_other_waypoints = str(clear_other_waypoints).lower()
    sso_path = (f"https://esi.evetech.net/latest/ui/autopilot/waypoint/?add_to_beginning={add_to_beginning}&clear_other_waypoints={clear_other_waypoints}&datasource=tranquility&destination_id={destination_id}")
    headers = {
        "Authorization": "Bearer {}".format(access_token),
        "Cache-Control": "no-cache"
    }
    res = requests.post(sso_path, headers=headers, json={})
    res.raise_for_status()
    return

# =============================================================================
# ASYNC API FUNCTIONS FOR PARALLEL PROCESSING
# =============================================================================

# Async API functions for parallel processing
async def async_get_system_info(session, system_id):
    """Async version of get_system_info"""
    url = f'https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility&language=en'
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def async_get_stargate_info(session, stargate_id):
    """Async version of get_stargate_info"""
    url = f'https://esi.evetech.net/latest/universe/stargates/{stargate_id}/?datasource=tranquility'
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def async_get_station_info(session, station_id):
    """Async version of get_station_info"""
    url = f'https://esi.evetech.net/latest/universe/stations/{station_id}/?datasource=tranquility'
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def async_get_char_info(session, character_id):
    """Async version of get_char_info"""
    url = f'https://esi.evetech.net/latest/characters/{character_id}/?datasource=tranquility'
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def async_get_sso_location(session, access_token, character_id):
    """Async version of get_sso_location"""
    url = f'https://esi.evetech.net/latest/characters/{character_id}/location/?datasource=tranquility'
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        data = await response.json()
        return data['solar_system_id']

async def async_get_route(session, origin_id, destination_id, flag='shortest'):
    """Async version of get_route"""
    assert flag in ['shortest','secure','insecure']
    url = f'https://esi.evetech.net/latest/route/{origin_id}/{destination_id}?datasource=tranquility&flag={flag}'
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

# =============================================================================
# BATCH API FUNCTIONS FOR PARALLEL PROCESSING
# =============================================================================

async def batch_get_system_info(system_ids):
    """Fetch multiple system info in parallel"""
    async with aiohttp.ClientSession() as session:
        tasks = [async_get_system_info(session, system_id) for system_id in system_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

async def batch_get_stargate_info(stargate_ids):
    """Fetch multiple stargate info in parallel"""
    async with aiohttp.ClientSession() as session:
        tasks = [async_get_stargate_info(session, stargate_id) for stargate_id in stargate_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

async def batch_get_station_info(station_ids):
    """Fetch multiple station info in parallel"""
    async with aiohttp.ClientSession() as session:
        tasks = [async_get_station_info(session, station_id) for station_id in station_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

async def batch_get_char_info(character_ids):
    """Fetch multiple character info in parallel"""
    async with aiohttp.ClientSession() as session:
        tasks = [async_get_char_info(session, char_id) for char_id in character_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

# =============================================================================
# CONVENIENCE FUNCTIONS FOR COMMON BATCH OPERATIONS
# =============================================================================

async def batch_get_route_data(system_ids, stargate_ids=None):
    """
    Fetch both system and stargate data in parallel for route calculations.
    
    Args:
        system_ids: List of system IDs to fetch
        stargate_ids: Optional list of stargate IDs to fetch
    
    Returns:
        tuple: (systems_data, stargates_data) where each is a dict mapping ID to data
    """
    async with aiohttp.ClientSession() as session:
        # Fetch systems
        system_tasks = [async_get_system_info(session, system_id) for system_id in system_ids]
        system_results = await asyncio.gather(*system_tasks, return_exceptions=True)
        
        # Create system data dict
        systems_data = {}
        for system_id, result in zip(system_ids, system_results):
            if not isinstance(result, Exception):
                systems_data[system_id] = result
        
        # Fetch stargates if provided
        stargates_data = {}
        if stargate_ids:
            stargate_tasks = [async_get_stargate_info(session, sg_id) for sg_id in stargate_ids]
            stargate_results = await asyncio.gather(*stargate_tasks, return_exceptions=True)
            
            for stargate_id, result in zip(stargate_ids, stargate_results):
                if not isinstance(result, Exception):
                    stargates_data[stargate_id] = result
        
        return systems_data, stargates_data

async def batch_get_route_with_systems(origin_id, destination_id, flag='shortest'):
    """
    Get route and fetch all required system data in one operation.
    
    Args:
        origin_id: Origin system ID
        destination_id: Destination system ID
        flag: Route flag ('shortest', 'secure', 'insecure')
    
    Returns:
        tuple: (route_systems, systems_data) where route_systems is the route list
               and systems_data is a dict mapping system_id to system data
    """
    async with aiohttp.ClientSession() as session:
        # Get route first
        route_systems = await async_get_route(session, origin_id, destination_id, flag)
        
        # Fetch all system data in parallel
        system_results = await asyncio.gather(
            *[async_get_system_info(session, system_id) for system_id in route_systems],
            return_exceptions=True
        )
        
        # Create systems data dict
        systems_data = {}
        for system_id, result in zip(route_systems, system_results):
            if not isinstance(result, Exception):
                systems_data[system_id] = result
        
        return route_systems, systems_data