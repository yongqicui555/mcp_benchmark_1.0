# Time-MCP
### This is an MCP server for agents to get the current time (and date).
<img width="635" alt="Screenshot 2025-03-20 at 1 02 54 AM" src="https://github.com/user-attachments/assets/b3a0d85b-36c9-4be0-8281-5365b4724263" />


## Usage

### Claude Desktop App
Add `time_mcp_server.py` to the list of MCP servers in the Claude Desktop App config file at `~/Library/Application\ Support/Claude/claude_desktop_config.json` like this:
```
{
    "mcpServers": {
        "time": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/time-mcp",
                "run",
                "time_mcp_server.py"
            ]
        }
    }
}
```
Save the file, and restart Claude for Desktop.

**Note**: You may need to put the full path to the `uv` executable in the command field. You can get this by running `which uv` on MacOS/Linux or `where uv` on Windows.

This is based on **_Testing your server with Claude for Desktop_** from https://modelcontextprotocol.io/quickstart/server. 

### Custom client (or Linux)
Since this is an STDIO-based MCP server, the best way is to implement a client in a similar fashion as the official example client tutorial (https://modelcontextprotocol.io/quickstart/client). Instead of the example `weather.py` MCP server, use `time_mcp_server.py`.

## Why?
It seems helpful and kind of important for agents to know what time (and date) it is. Enables agents to fulfill time-dependent tasks such as "what time is it in Pacifica?" or "what will the weather be 3 hours from now?"

## Tools
Time-MCP provides two tools, `get_datetime` and `get_current_unix_timestamp` which return a formatted datetime in the specified timezone (UTC if none specified) and the current UNIX timestamp, respectively.

### With/Without Time-MCP:
##### Without:
<img width="632" alt="Screenshot 2025-03-20 at 1 02 21 AM" src="https://github.com/user-attachments/assets/acb9947d-3f55-45f6-ac7b-4e03bba95a4a" />

##### With:
<img width="635" alt="Screenshot 2025-03-20 at 1 02 54 AM" src="https://github.com/user-attachments/assets/fcf7c41e-a159-4cd5-bbb3-e5afbc059fe9" />



