
# Pylpex MCP

This is a MCP server for Pylpex interpreter.

## Installation

Assuming you are using `Claude Desktop` and have `uv` installed, follow these instructions to set up the Pylpex MCP server:

1. Clone the repository:

```bash
git clone https://github.com/Golto/pylpex-mcp.git
cd pylpex-mcp
```

2. Install dependencies:

```bash
uv sync
```

This command reads the `pyproject.toml` file and installs all the required dependencies.

3. Configure your Claude Desktop settings to use this MCP server:

Go to your Claude Desktop settings, then to the Developer Settings tab, click on "Edit config" and add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "Pylpex": {
      "command": "uv",
      "args": [
        "--directory",
        "$ABSOLUTE/PATH/TO/THE/PROJECT/pylpex-mcp", 
        "run",
        "mcp",
        "run",
        "main.py"
      ]
    }
  }
}
```

You may want to replace `uv` with the absolute path to the `uv` executable. To find `uv` location, use `which uv` on Linux/MacOS or `where uv` on Windows. Also, replace `$ABSOLUTE/PATH/TO/THE/PROJECT/pylpex-mcp` with the absolute path to the project directory. `--directory` argument is required for `uv` to find the project with dependencies.

> **Note**: Running `uv run mcp install main.py` will install the MCP server in your Claude Desktop settings directly. But it may not work because of the `--directory` argument missing.

4. Close and reopen your Claude Desktop application to apply the changes.
5. Verify that the Pylpex server is running by checking the status in the Developer Settings tab.

You should see the Pylpex tools available in your Claude Desktop interface.

## Tools

At this point, you should have access to the following tools:
- **run**: Execute Pylpex code and return the result.
- **tokenize**: Convert Pylpex code into tokens for analysis. Use the Lexer component of the Pylpex interpreter.
- **get_variables**: Get all variables in the current interpreter state.
- **reset**: Reset the interpreter state.

## Resources

- **get_documentation**: Get the documentation of the Pylpex language. It gives you the syntax and the available functions.
- **get_examples**: Get examples of Pylpex code as code snippets.

## More details

For more details about the Pylpex language, you can check the [Pylpex github repository](https://github.com/Golto/pylpex).
> **Note**: The Pylpex language is still in development and may change in the future. And it's in french...