## EVE Fleet Manager MCP Server

An MCP server that provides tools and resources for EVE Online fleet management: authorize your fleet via SSO, inspect composition and structure, organize squads, invite/kick members, and update MOTD.

mcp-name: io.github.tedfytw1209/mcp-server-EVEfleet

### Features
- Fleet SSO authorization and status
- Auto-refreshing fleet data and structure
- Organize formations (squads/wings) by ship types
- Bulk invite and kick utilities
- Fleet MOTD updates (append/replace)
- Composition and losses history
- Ship utilities (type → group, lists of types/groups)

### Install
- pip: `pip install mcp-server-evefleet`
- uv: `uv pip install mcp-server-evefleet`

### Authenticate (first run)
- On first run you’ll be guided through EVE SSO. A refresh token will be saved automatically to a cross‑platform location:
  - Windows: %LOCALAPPDATA%/mcp_server_evefleet/refresh_token.txt
  - macOS: ~/Library/Application Support/mcp_server_evefleet/refresh_token.txt
  - Linux: ~/.config/mcp_server_evefleet/refresh_token.txt
- If `refresh_token.txt` exists in the current directory, it will be used and then persisted to the proper location.

### Tools (MCP)
- ping: Health check
- fleet_authorize(force_refresh=False): Re‑authorize/refresh SSO and connect
- organize_fleet_formation(members_per_squad=8, location_match=True, number_of_squads=None)
- invite_to_fleet(ids_or_names)
- kick_from_fleet(ids_or_names, sleep_time=0.1)
- update_fleet_motd(text, append=True)
- get_fleet_history(limit=5)
- get_fleet_losses(limit=5)
- ship_type2group(type_name)

### Resources (MCP)
- character://status
- fleet://status
- fleet://composition
- fleet://structure
- ship://types
- ship://groups
- ship://types2groups


### Development
- Clone repo, then:
  - `pip install -e .` or `uv pip install -e .`
- Packaged data includes `config.yaml` and `setting/*`. The token file is not packaged and is created at runtime.

### MCP Test
```cmd
uv run mcp dev ./src/mcp_server_evefleet/server.py
```
