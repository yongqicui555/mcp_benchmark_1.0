from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("todo-mcp")

# Constants
SERVER = "http://localhost:8000"
USER_AGENT = "todo-app/1.0"

async def make_request(method: str, path: str, json: Any = None) -> Any:
    """Make a request to the backend API.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API endpoint path
        json: Optional JSON data to send
        
    Returns:
        Response data from the API
    """
    async with httpx.AsyncClient() as client:
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json"
        }
        
        response = await client.request(
            method=method,
            url=f"{SERVER}{path}",
            json=json,
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()

def format_todo(todo: dict) -> str:
    """Format a todo item into a readable string.
    
    Args:
        todo: Dictionary containing todo item data
        
    Returns:
        Formatted string representation of the todo
    """
    created = todo["created_at"].split("T")[0]  # Get just the date part
    return f"[{created}] {todo['title']} (ID: {todo['id']})"

@mcp.tool()
async def list_todos() -> str:
    """List all todo items."""
    todos = await make_request("GET", "/api/todos")
    if not todos:
        return "No todos found."
    
    return "\n".join(format_todo(todo) for todo in todos)

@mcp.tool()
async def add_todo(title: str) -> str:
    """Add a new todo item.
    
    Args:
        title: Title of the todo item
    """
    todo = await make_request("POST", "/api/todos", {"title": title})
    return f"Added todo: {format_todo(todo)}"

@mcp.tool()
async def get_todo(todo_id: str) -> str:
    """Get details of a specific todo item.
    
    Args:
        todo_id: UUID of the todo item
    """
    try:
        todo = await make_request("GET", f"/api/todos/{todo_id}")
        return format_todo(todo)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return "Todo not found."
        raise

@mcp.tool()
async def update_todo(todo_id: str, title: str) -> str:
    """Update a todo item.
    
    Args:
        todo_id: UUID of the todo item
        title: New title for the todo item
    """
    try:
        todo = await make_request("PUT", f"/api/todos/{todo_id}", {"title": title})
        return f"Updated todo: {format_todo(todo)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return "Todo not found."
        raise

@mcp.tool()
async def delete_todo(todo_id: str) -> str:
    """Delete a todo item.
    
    Args:
        todo_id: UUID of the todo item
    """
    try:
        await make_request("DELETE", f"/api/todos/{todo_id}")
        return "Todo deleted successfully."
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return "Todo not found."
        raise

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')