# TKU-MCP - TKU Model Context Protocol Integration 

![](https://badge.mcpx.dev?type=server 'MCP Server')

> [!WARNING]  
> Reminder: This project is intended only to demonstrate the use of MCP. It is not meant for production use or full implementation.

TKU-MCP connects TronClass to Claude AI through the Model Context Protocol (MCP), allowing Claude to directly interact with TronClass

## Installation


### Prerequisites
- Python 3.10 or newer
- uv package manager: 

**Install uv as**
```bash
brew install uv
```
### Environment variables set up
add `.env` to the project folder
```bash
USERNAME="YOURSTUDENTID"
PASSWORD="YOURSSOPASSWORD"
```
### Claude for Desktop Integration
Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the following:

```json
{
  "mcpServers": {
      "tku-mcp": {
          "command": "uv",
          "args": [
              "--directory",
              "ABSOLUTE PATH TO FOLDER",
              "run",
              "server.py"
          ]
      }
  }
}
```
