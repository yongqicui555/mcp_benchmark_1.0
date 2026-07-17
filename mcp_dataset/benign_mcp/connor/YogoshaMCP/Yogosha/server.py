import os
import httpx
from mcp.server.fastmcp import FastMCP
from typing import Optional

YOGOSHA_API_KEY = os.environ.get("YOGOSHA_API_KEY")
YOGOSHA_API_BASE = "https://api.yogosha.com/v1"  # Adjust if needed

mcp = FastMCP("Yogosha MCP Server")

def get_auth_headers():
    if not YOGOSHA_API_KEY:
        raise RuntimeError("YOGOSHA_API_KEY environment variable not set.")
    return {"Authorization": f"Bearer {YOGOSHA_API_KEY}", "Accept": "application/json"}

async def yogosha_api_request(method: str, endpoint: str, params: Optional[dict] = None, data: Optional[dict] = None):
    url = f"{YOGOSHA_API_BASE}{endpoint}"
    headers = get_auth_headers()
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, params=params, json=data)
        response.raise_for_status()
        return response.json()

# --- Programs ---
@mcp.tool()
async def list_programs():
    """List all programs."""
    return await yogosha_api_request("GET", "/programs")

@mcp.tool()
async def get_program(program_id: str):
    """Get a specific program by ID."""
    return await yogosha_api_request("GET", f"/programs/{program_id}")

# --- Assets ---
@mcp.tool()
async def list_assets(program_id: str):
    """List all assets for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/assets")

@mcp.tool()
async def get_asset(program_id: str, asset_id: str):
    """Get a specific asset by ID for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/assets/{asset_id}")

# --- Create Asset ---
@mcp.tool()
async def create_asset(program_id: str, asset_data: dict):
    """Create a new asset for a program. Pass asset_data as a dict with required fields."""
    return await yogosha_api_request("POST", f"/programs/{program_id}/assets", data=asset_data)

# --- Update Asset ---
@mcp.tool()
async def update_asset(program_id: str, asset_id: str, asset_data: dict):
    """Update an asset for a program. Pass asset_data as a dict with fields to update."""
    return await yogosha_api_request("PUT", f"/programs/{program_id}/assets/{asset_id}", data=asset_data)

# --- Delete Asset ---
@mcp.tool()
async def delete_asset(program_id: str, asset_id: str):
    """Delete an asset from a program."""
    return await yogosha_api_request("DELETE", f"/programs/{program_id}/assets/{asset_id}")

# --- Reports ---
@mcp.tool()
async def list_reports(program_id: str):
    """List all reports for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/reports")

@mcp.tool()
async def get_report(program_id: str, report_id: str):
    """Get a specific report by ID for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/reports/{report_id}")

# --- Create Report ---
@mcp.tool()
async def create_report(program_id: str, report_data: dict):
    """Create a new report for a program. Pass report_data as a dict with required fields."""
    return await yogosha_api_request("POST", f"/programs/{program_id}/reports", data=report_data)

# --- Update Report ---
@mcp.tool()
async def update_report(program_id: str, report_id: str, report_data: dict):
    """Update a report for a program. Pass report_data as a dict with fields to update."""
    return await yogosha_api_request("PUT", f"/programs/{program_id}/reports/{report_id}", data=report_data)

# --- Delete Report ---
@mcp.tool()
async def delete_report(program_id: str, report_id: str):
    """Delete a report from a program."""
    return await yogosha_api_request("DELETE", f"/programs/{program_id}/reports/{report_id}")

# --- Users ---
@mcp.tool()
async def list_users():
    """List all users."""
    return await yogosha_api_request("GET", "/users")

@mcp.tool()
async def get_user(user_id: str):
    """Get a specific user by ID."""
    return await yogosha_api_request("GET", f"/users/{user_id}")

# --- Create User ---
@mcp.tool()
async def create_user(user_data: dict):
    """Create a new user. Pass user_data as a dict with required fields."""
    return await yogosha_api_request("POST", "/users", data=user_data)

# --- Update User ---
@mcp.tool()
async def update_user(user_id: str, user_data: dict):
    """Update a user. Pass user_data as a dict with fields to update."""
    return await yogosha_api_request("PUT", f"/users/{user_id}", data=user_data)

# --- Delete User ---
@mcp.tool()
async def delete_user(user_id: str):
    """Delete a user by ID."""
    return await yogosha_api_request("DELETE", f"/users/{user_id}")

# --- Vulnerabilities ---
@mcp.tool()
async def list_vulnerabilities(program_id: str):
    """List all vulnerabilities for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/vulnerabilities")

@mcp.tool()
async def get_vulnerability(program_id: str, vulnerability_id: str):
    """Get a specific vulnerability by ID for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/vulnerabilities/{vulnerability_id}")

# --- Create Vulnerability ---
@mcp.tool()
async def create_vulnerability(program_id: str, vuln_data: dict):
    """Create a new vulnerability for a program. Pass vuln_data as a dict with required fields."""
    return await yogosha_api_request("POST", f"/programs/{program_id}/vulnerabilities", data=vuln_data)

# --- Update Vulnerability ---
@mcp.tool()
async def update_vulnerability(program_id: str, vulnerability_id: str, vuln_data: dict):
    """Update a vulnerability for a program. Pass vuln_data as a dict with fields to update."""
    return await yogosha_api_request("PUT", f"/programs/{program_id}/vulnerabilities/{vulnerability_id}", data=vuln_data)

# --- Delete Vulnerability ---
@mcp.tool()
async def delete_vulnerability(program_id: str, vulnerability_id: str):
    """Delete a vulnerability from a program."""
    return await yogosha_api_request("DELETE", f"/programs/{program_id}/vulnerabilities/{vulnerability_id}")

# --- Scopes ---
@mcp.tool()
async def list_scopes(program_id: str):
    """List all scopes for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/scopes")

@mcp.tool()
async def get_scope(program_id: str, scope_id: str):
    """Get a specific scope by ID for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/scopes/{scope_id}")

# --- Invitations ---
@mcp.tool()
async def list_invitations(program_id: str):
    """List all invitations for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/invitations")

@mcp.tool()
async def get_invitation(program_id: str, invitation_id: str):
    """Get a specific invitation by ID for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/invitations/{invitation_id}")

# --- Submissions ---
@mcp.tool()
async def list_submissions(program_id: str):
    """List all submissions for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/submissions")

@mcp.tool()
async def get_submission(program_id: str, submission_id: str):
    """Get a specific submission by ID for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/submissions/{submission_id}")

# --- Comments (for a report) ---
@mcp.tool()
async def list_report_comments(program_id: str, report_id: str):
    """List all comments for a report."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/reports/{report_id}/comments")

@mcp.tool()
async def get_report_comment(program_id: str, report_id: str, comment_id: str):
    """Get a specific comment by ID for a report."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/reports/{report_id}/comments/{comment_id}")

# --- Create Comment (for a report) ---
@mcp.tool()
async def create_report_comment(program_id: str, report_id: str, comment_data: dict):
    """Create a new comment for a report. Pass comment_data as a dict with required fields."""
    return await yogosha_api_request("POST", f"/programs/{program_id}/reports/{report_id}/comments", data=comment_data)

# --- Update Comment (for a report) ---
@mcp.tool()
async def update_report_comment(program_id: str, report_id: str, comment_id: str, comment_data: dict):
    """Update a comment for a report. Pass comment_data as a dict with fields to update."""
    return await yogosha_api_request("PUT", f"/programs/{program_id}/reports/{report_id}/comments/{comment_id}", data=comment_data)

# --- Delete Comment (for a report) ---
@mcp.tool()
async def delete_report_comment(program_id: str, report_id: str, comment_id: str):
    """Delete a comment from a report."""
    return await yogosha_api_request("DELETE", f"/programs/{program_id}/reports/{report_id}/comments/{comment_id}")

# --- PATCH and Custom Actions ---
@mcp.tool()
async def patch_asset(program_id: str, asset_id: str, patch_data: dict):
    """Patch (partially update) an asset for a program."""
    return await yogosha_api_request("PATCH", f"/programs/{program_id}/assets/{asset_id}", data=patch_data)

@mcp.tool()
async def patch_report(program_id: str, report_id: str, patch_data: dict):
    """Patch (partially update) a report for a program."""
    return await yogosha_api_request("PATCH", f"/programs/{program_id}/reports/{report_id}", data=patch_data)

@mcp.tool()
async def patch_user(user_id: str, patch_data: dict):
    """Patch (partially update) a user."""
    return await yogosha_api_request("PATCH", f"/users/{user_id}", data=patch_data)

@mcp.tool()
async def patch_vulnerability(program_id: str, vulnerability_id: str, patch_data: dict):
    """Patch (partially update) a vulnerability for a program."""
    return await yogosha_api_request("PATCH", f"/programs/{program_id}/vulnerabilities/{vulnerability_id}", data=patch_data)

# --- Attachments ---
@mcp.tool()
async def list_attachments(program_id: str, report_id: str):
    """List all attachments for a report."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/reports/{report_id}/attachments")

@mcp.tool()
async def get_attachment(program_id: str, report_id: str, attachment_id: str):
    """Get a specific attachment by ID for a report."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/reports/{report_id}/attachments/{attachment_id}")

@mcp.tool()
async def create_attachment(program_id: str, report_id: str, attachment_data: dict):
    """Create a new attachment for a report. Pass attachment_data as a dict with required fields."""
    return await yogosha_api_request("POST", f"/programs/{program_id}/reports/{report_id}/attachments", data=attachment_data)

@mcp.tool()
async def delete_attachment(program_id: str, report_id: str, attachment_id: str):
    """Delete an attachment from a report."""
    return await yogosha_api_request("DELETE", f"/programs/{program_id}/reports/{report_id}/attachments/{attachment_id}")

# --- Tags ---
@mcp.tool()
async def list_tags(program_id: str):
    """List all tags for a program."""
    return await yogosha_api_request("GET", f"/programs/{program_id}/tags")

@mcp.tool()
async def create_tag(program_id: str, tag_data: dict):
    """Create a new tag for a program. Pass tag_data as a dict with required fields."""
    return await yogosha_api_request("POST", f"/programs/{program_id}/tags", data=tag_data)

@mcp.tool()
async def delete_tag(program_id: str, tag_id: str):
    """Delete a tag from a program."""
    return await yogosha_api_request("DELETE", f"/programs/{program_id}/tags/{tag_id}")

# --- Notifications ---
@mcp.tool()
async def list_notifications(params: Optional[dict] = None):
    """List all notifications. Optional query params supported."""
    if params is None:
        params = {}
    return await yogosha_api_request("GET", "/notifications", params=params)

@mcp.tool()
async def get_notification(notification_id: str):
    """Get a specific notification by ID."""
    return await yogosha_api_request("GET", f"/notifications/{notification_id}")

@mcp.tool()
async def delete_notification(notification_id: str):
    """Delete a notification by ID."""
    return await yogosha_api_request("DELETE", f"/notifications/{notification_id}")

# --- Settings ---
@mcp.tool()
async def get_settings():
    """Get global settings."""
    return await yogosha_api_request("GET", "/settings")

@mcp.tool()
async def update_settings(settings_data: dict):
    """Update global settings. Pass settings_data as a dict with fields to update."""
    return await yogosha_api_request("PUT", "/settings", data=settings_data)

if __name__ == "__main__":
    mcp.run(transport="stdio")
