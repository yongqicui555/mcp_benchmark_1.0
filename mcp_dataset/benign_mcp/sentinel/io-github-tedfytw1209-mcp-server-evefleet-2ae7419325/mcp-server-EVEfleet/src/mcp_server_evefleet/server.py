"""
EVE Fleet Manager MCP Server - Auto-authorizes fleet on client connection
"""

import time
import logging
from typing import Optional, Dict, Any, Union
from mcp.server.fastmcp import FastMCP
from mcp_server_evefleet.functions import fleet_manager
from mcp_server_evefleet.static_manage import ShipID_Dict, Static_Dict
from mcp_server_evefleet.config_load import CONFIG
from mcp_server_evefleet.IO.API_IO import get_refresh_token
from mcp_server_evefleet.IO.fleet_api import get_sso_fleetid

# Logger
logger = logging.getLogger(__name__)

# Global state
fleet_mgr: Optional[fleet_manager] = None
ship_dict: Optional[ShipID_Dict] = None
system_dict: Optional[Static_Dict] = None
fleet_status = {"authorized": False, "error": None, "character": None, "fleet_id": None}

## functions
def fleet_authorize_with_retry(max_retries: int = 3, force_refresh: bool = False) -> Dict[str, Any]:
    """Auto-authorize fleet with retry logic"""
    global fleet_mgr, fleet_status, ship_dict, system_dict
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fleet authorization attempt {attempt + 1}/{max_retries}")
            
            system_dict = Static_Dict('setting/system_dict.yaml','systems','solar_system')
            ship_dict = ShipID_Dict()
            # Get tokens and initialize (cross-platform path by default)
            _, access_token, character_id, character_name = get_refresh_token(reset=force_refresh)
            
            # Create fleet manager
            fleet_id = get_sso_fleetid(access_token, character_id, character_name)
            fleet_mgr = fleet_manager(access_token, fleet_id, character_id, 
                                    bomb_alt_ids=CONFIG.get('ALT_IDS', []), 
                                    ship_dict=ship_dict,
                                    system_dict=system_dict)
            
            # Update status
            fleet_status.update({
                "authorized": True, "error": None, 
                "character": character_name, "fleet_id": fleet_id
            })
            
            logger.info(f"[SUCCESS] Fleet authorized for {character_name} (Fleet: {fleet_id})")
            return {"success": True, "character": character_name, "fleet_id": fleet_id, 
                   "fleet_data": fleet_mgr.output_fleet_static()}
            
        except Exception as e:
            error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
            logger.error(error_msg)
            
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)  # Exponential backoff
            else:
                fleet_status.update({"authorized": False, "error": error_msg})
                return {"success": False, "error": error_msg, "attempts": max_retries}
    
    return {"success": False, "error": "Unexpected error"}

def get_fleet_status() -> Dict[str, Any]:
    """Get current fleet status and data.
    
    Returns:
        Fleet authorization status, character info, fleet ID, member count, composition data
    """
    if fleet_mgr and fleet_status["authorized"]:
        try:
            return {**fleet_status, "fleet_data": fleet_mgr.output_fleet_static(), 
                   "members_count": len(fleet_mgr.fleet_members_list)}
        except Exception as e:
            return {**fleet_status, "data_error": str(e)}
    return fleet_status

# Create MCP server and auto-authorize
mcp = FastMCP("EVE Fleet Manager")
logger.info("Starting EVE Fleet Manager MCP Server...")
startup_result = fleet_authorize_with_retry()

if startup_result["success"]:
    logger.info(f"[READY] Fleet: {startup_result['fleet_id']}, Character: {startup_result['character']}")
else:
    logger.error(f"[ERROR] Started with authorization error: {startup_result['error']}, waiting for Client call to retry...")

## MCP Tools
# ship dict function
@mcp.tool()
def ship_type2group(type_name: str) -> str:
    """Convert EVE ship type name to ship group name (e.g., "Rifter" -> "Assault Frigate").

    Args:
        type_name (str): Ship type name to convert

    Returns:
        str: Ship group name or None if not found
    """
    return ship_dict.type_to_groupname(type_name)
# fleet function
@mcp.tool()
def fleet_authorize(force_refresh: bool = False) -> Dict[str, Any]:
    """Authorize EVE fleet access via SSO tokens. fleet manager connection, validates FC permissions. Use when seeing "Fleet not authorized" errors.
    
    Args:
        force_refresh: Force token refresh even if tokens appear valid
    Returns:
        Success status, character name, fleet ID, fleet data, or error details
    """
    return fleet_authorize_with_retry(force_refresh=force_refresh)

@mcp.tool()
def organize_fleet_formation(members_per_squad: Optional[int] = 8, location_match: bool = True, number_of_squads: Optional[int] = None) -> Dict[str, Any]:
    """Organize fleet into tactical formations. Places combat ships in first wing, non-combat in separate wings.
    
    Args:
        members_per_squad: Max members per squad (default 8)
        location_match: Only organize members in same system as FC
        number_of_squads: Create exactly this many squads (overrides members_per_squad)
    Returns:
        Success status, organization message, updated fleet data, member count
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    try:
        fleet_mgr.fleet_formation(
            members_in_squad=members_per_squad,
            location_match=location_match,
            number_of_squads=number_of_squads
        )
        return {
            "success": True, 
            "message": f"Fleet organized into formations",
            "fleet_data": fleet_mgr.output_fleet_static(),
            "members_count": len(fleet_mgr.fleet_members_list)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def invite_to_fleet(ids_or_names: list) -> Dict[str, Any]:
    """Invite characters to fleet. Accepts character IDs, names, or ['alt'/'account'] for all configured alts.
    
    Args:
        ids_or_names: List of character IDs, names, or ['alt'/'account'] for all alts
    Returns:
        Success status, invitation count message, list of invited characters
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    if ids_or_names and (ids_or_names[0].lower() == 'alt' or ids_or_names[0].lower() == 'account'):
        ids_or_names = fleet_mgr.alts

    char_id_list = []
    for e_item in ids_or_names:
        if str(e_item).isdigit():
            char_id_list.append(int(e_item))
        else:
            char_ids = fleet_mgr.char_dict.update_names([str(e_item)])
            char_id_list.extend(char_ids)
    logger.info(f"Preparing to invite characters: {char_id_list}")
    try:
        fleet_mgr.fleet_invite(char_id_list)
        return {
            "success": True,
            "message": f"Invited {len(char_id_list)} characters to fleet",
            "invited_characters": char_id_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def kick_from_fleet(ids_or_names: list, sleep_time: float = 0.1) -> Dict[str, Any]:
    """Remove characters from fleet. Accepts character IDs, names, or ['alt'/'account'] for all alts.
    
    Args:
        ids_or_names: List of character IDs, names, or ['alt'/'account'] for all alts
        sleep_time: Delay between kicks in seconds (default 0.1s)
    Returns:
        Success status, removal count message, list of kicked characters
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    if ids_or_names and (ids_or_names[0].lower() == 'alt' or ids_or_names[0].lower() == 'account'):
        ids_or_names = fleet_mgr.alts

    char_id_list = []
    for e_item in ids_or_names:
        if str(e_item).isdigit():
            char_id_list.append(int(e_item))
        else:
            char_ids = fleet_mgr.char_dict.update_names([str(e_item)])
            char_id_list.extend(char_ids)
    logger.info(f"Preparing to kick characters: {char_id_list}")
    try:
        fleet_mgr.fleet_kick(char_id_list, sleep_time)
        return {
            "success": True,
            "message": f"Kicked {len(char_id_list)} characters from fleet",
            "kicked_characters": char_id_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def update_fleet_motd(text: str, append: bool = True) -> Dict[str, Any]:
    """Update fleet MOTD by appending text. Preserves existing content. Used for objectives, fittings, comms, loot rules, tactical info, warnings.
    
    Args:
        text: Text to append to current MOTD
        append: Append text to current MOTD (default True)
    Returns:
        Success status, confirmation message, complete updated MOTD
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    try:
        fleet_mgr.update_motd(text, append)
        fleet_mgr.renew_motd()
        return {
            "success": True,
            "message": "Fleet MOTD updated successfully",
            "new_motd": fleet_mgr.fleet_motd
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_fleet_history(limit: int = 5) -> Dict[str, Any]:
    """Get fleet composition snapshots and member patterns over time.
    
    Args:
        limit: Number of entries to return (default 5, 0 for all)
    Returns:
        Success status, fleet history entries, record count
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    try:
        history_data = fleet_mgr.fleet_history.get_data()[-limit:] if limit > 0 else fleet_mgr.fleet_history.get_data()
        return {
            "success": True,
            "fleet_history": history_data,
            "history_count": len(history_data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_fleet_losses(limit: int = 5) -> Dict[str, Any]:
    """Get estimated fleet losses based on member count changes.
    
    Args:
        limit: Number of entries to return (default 5, 0 for all)
    Returns:
        Success status, loss history data, record count
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    try:
        loss_history = fleet_mgr.fleet_loss_history.get_data()[-limit:] if limit > 0 else fleet_mgr.fleet_loss_history.get_data()
        return {
            "success": True,
            "loss_history": loss_history,
            "loss_count": len(loss_history)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Resources
@mcp.resource("character://status")
def character_status_resource() -> str:
    """Real-time EVE character status resource. Provides live location, ship info, and activity status without explicit tool calls."""
    if fleet_mgr and fleet_status["authorized"]:
        return f"Character Status: {fleet_mgr.get_user_info()}"
    else:
        return "[ERROR] Character not authorized"

@mcp.resource("fleet://status")
def fleet_status_resource() -> str:
    """Real-time EVE fleet status resource. Provides live authorization state, member count, FC info, and composition data without explicit tool calls."""
    return f"Fleet Status: {get_fleet_status()}"

@mcp.resource("fleet://composition")
def fleet_composition_resource() -> Dict[str, Any]:
    """Return fleet composition with ship type breakdown. Shows ship distribution, specific hull counts, role categorization.
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    try:
        composition = fleet_mgr.fleet_members_composition
        
        return {
            "success": True,
            "composition": composition,
            "total_members": len(fleet_mgr.fleet_members_list)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.resource("fleet://structure")
def fleet_structure_resource() -> Dict[str, Any]:
    """Get hierarchical fleet structure (Fleet > Wings > Squads > Members). Shows IDs, names, member assignments, roles, ship types, locations.
    """
    if not fleet_mgr:
        return {"success": False, "error": "Fleet not authorized"}
    
    try:
        return {
            "success": True,
            "fleet_structure": fleet_mgr.fleet_struct,
            "wings_count": len(fleet_mgr.fleet_struct),
            "total_squads": sum(len(wing.get('squads', [])) for wing in fleet_mgr.fleet_struct)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.resource("ship://types")
def ship_types_resource() -> str:
    """Return EVE ship types resource. Provides ship type names."""
    if ship_dict != None:
        return f"Ship Types: {ship_dict.ship_names}"
    else:
        return "[ERROR] Character not authorized"
    
@mcp.resource("ship://groups")
def ship_groups_resource() -> str:
    """Return EVE ship groups resource. Provides ship group names."""
    if ship_dict != None:
        return f"Ship Groups: {ship_dict.class_names}"
    else:
        return "[ERROR] Character not authorized"

@mcp.resource("ship://types2groups")
def ship_types_to_groups_resource() -> str:
    """Return EVE ship types to groups resource. Provides dictionary from ship types to group names."""
    gp_dict = {name: group for name, group in zip(ship_dict.ship_names, ship_dict.type_to_groupnames(ship_dict.ship_names))}
    if ship_dict != None:
        return f"Ship Types to Groups Dict: {gp_dict}"
    else:
        return "[ERROR] Character not authorized"

# Prompts
@mcp.prompt()
def fleet_prompt(action: str = "status") -> str:
    """Fleet management prompts for different operations. Provides specialized guidance for EVE fleet command tasks.
    
    Args:
        action: Operation type (status, formation, invite, kick, analysis, history, structure)
    """
    prompts = {
        "status": "Show current fleet status, member composition, and strength analysis. Get comprehensive fleet overview including authorization, member count, ship composition, operational issues.",
        
        "formation": "Organize fleet into optimal squad formations by ship types and location. Analyze member distribution, identify combat ships, restructure wings/squads for tactical effectiveness.",
        
        "invite": "Invite new fleet members with proper role assignments. Process character names/IDs, handle alt invitations, manage queues, ensure permissions. Use 'alt' for quick alt management.",
        
        "kick": "Remove fleet members efficiently and safely. Identify problematic/inactive members, process removals, manage bulk operations with rate limiting, maintain discipline.",
        
        "analysis": "Analyze fleet composition, estimate strength, suggest improvements. Detailed ship type breakdowns, role distributions, tactical capabilities, optimization recommendations.",
        
        "history": "Review fleet history, track losses, analyze performance trends. Examine historical data, member participation patterns, estimated losses, operational effectiveness insights.",
        
        "structure": "Manage fleet wing and squad structure for optimal organization. Understand current hierarchy, plan structural changes, coordinate command assignments, optimize tactical control."
    }
    return prompts.get(action, "Help manage EVE Online fleet operations. Available: status, formation, invite, kick, analysis, history, structure.")

@mcp.tool()
def ping() -> dict:
    """Health check"""
    return {"ok": True}

if __name__ == "__main__":
    mcp.run(transport="stdio")