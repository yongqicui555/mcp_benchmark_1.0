# MCP Server Setup Documentation

## Overview

This guide provides detailed instructions for setting up a Model Control Protocol (MCP) server that integrates with Claude Desktop. The MCP server extends Claude's capabilities by allowing it to interact with external systems and APIs, including AWS services and GitHub.

## Prerequisites

- Python 3.8+ installed
- Claude Desktop application
- `uv` package manager installed
- Basic understanding of Python and command-line operations

## Installation Steps

### 1. Install Required Packages

First, ensure you have the necessary packages:

```bash
# Install UV if not already installed
pip install uv

# Install MCP and dependencies using UV
uv add mcp[cli] pygithub boto3
```

### 2. Create Your Server Script

Create a file named `server.py` in your desired directory with your custom function implementations.

Example structure for `server.py`:

```python
from mcp.server.fastmcp import FastMCP
import boto3
from dotenv import load_dotenv
from github import Github

load_dotenv()

# Initialize MCP server
mcp = FastMCP("Custom MCP Server", "0.1.0")

# Define your custom functions
@mcp.tool()
def fetch_aws_ec2_instances(region_name="us-east-1"):
    """
    Fetches and describes all EC2 instances in the specified AWS region.
    :param region_name: The name of the AWS region (e.g., 'us-east-1')
    :return: A list of EC2 instances in the specified region.
    """
    ec2 = boto3.client('ec2', region_name=region_name)
    return ec2.describe_instances()

# Add more custom tools as needed...
```

### 3. Test Your Server

Before connecting to Claude Desktop, test your server to ensure it works properly:

```bash
uv run mcp install server.py
```

You should see output indicating the server is running, typically on port 8000.

### 4. Configure Claude Desktop

1. Open Claude Desktop application
2. Navigate to File > Settings > Developer > Edit Config
3. Update the configuration with your MCP server details:

```json
{
  "mcpServers": {
    "Custom MCP Server": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli], pygithub, boto3",
        "mcp",
        "run",
        "/full/path/to/your/server.py"
      ]
    }
  }
}
```

**Important Configuration Notes:**
- Replace `/full/path/to/your/server.py` with the absolute path to your server.py file
- Add any additional required packages to the `--with` argument
- You can rename "Custom MCP Server" to any name you prefer

### 5. Enable and Start Your MCP Server

1. In Claude Desktop, go to File > Settings > Developer
2. Toggle on the MCP server you configured
3. Claude will attempt to connect to your server

## Advanced Configuration

### Environment Variables

To securely handle API keys and credentials, use a .env file:

Create a .env file in the same directory as your server.py:

# .env file
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
GITHUB_TOKEN=your_github_token_here
# Add other environment variables as needed

### Adding Custom Dependencies

If your server requires additional Python packages, add them to the `--with` argument in your Claude Desktop configuration:

```json
"args": [
  "run",
  "--with",
  "mcp[cli], pygithub, boto3, pandas, requests",
  "mcp",
  "run",
  "/path/to/server.py"
]
```

### Error Handling

Implement proper error handling in your server functions:

```python
@server.function()
def some_function(param):
    try:
        # Function logic
        return result
    except Exception as e:
        return {"error": str(e), "status": "failed"}
```

## Troubleshooting

### Common Issues and Solutions

1. **Connection Refused**
   - Ensure the server is running
   - Check if the port is already in use
   - Verify firewall settings

2. **Import Errors**
   - Confirm all dependencies are included in the `--with` argument
   - Try installing packages manually: `uv pip install [package-name]`

3. **Permission Errors**
   - Check file permissions for server.py
   - Ensure proper AWS/GitHub credentials are available

4. **Function Not Found**
   - Verify function is properly decorated with `@server.function()`
   - Restart both the server and Claude Desktop

## Example Use Cases

### AWS Resource Management

```python
@server.function()
def describe_ec2_instances(region_name="us-east-1"):
    ec2 = boto3.client('ec2', region_name=region_name)
    return ec2.describe_instances()

@server.function()
def start_ec2_instance(instance_id, region_name="us-east-1"):
    ec2 = boto3.client('ec2', region_name=region_name)
    return ec2.start_instances(InstanceIds=[instance_id])
```

### GitHub Integration

```python
@server.function()
def fetch_github_repo_info(repo):
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(repo)
    return {
        "name": repo.name,
        "description": repo.description,
        "stars": repo.stargazers_count,
        "forks": repo.forks_count
    }
```

## Security Considerations

- Never hardcode credentials in your server.py file
- Use environment variables for sensitive information
- Consider implementing authentication for your MCP server
- Be cautious about which functions you expose through the MCP server

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/introduction)
