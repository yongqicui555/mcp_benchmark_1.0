import os
import httpx
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

# Read Bugcrowd API credentials from environment variables
BUGCROWD_API_USERNAME = os.getenv("BUGCROWD_API_USERNAME")
BUGCROWD_API_PASSWORD = os.getenv("BUGCROWD_API_PASSWORD")
BUGCROWD_API_BASE = "https://api.bugcrowd.com"
BUGCROWD_API_VERSION = "2025-04-23"

async def bugcrowd_request(method, endpoint, **kwargs):
    """
    Async helper to make authenticated requests to the Bugcrowd API.
    """
    BUGCROWD_API_USERNAME = os.getenv("BUGCROWD_API_USERNAME")
    BUGCROWD_API_PASSWORD = os.getenv("BUGCROWD_API_PASSWORD")
    if not BUGCROWD_API_USERNAME or not BUGCROWD_API_PASSWORD:
        raise RuntimeError("BUGCROWD_API_USERNAME and BUGCROWD_API_PASSWORD must be set in environment variables.")
    url = f"{BUGCROWD_API_BASE}{endpoint}"
    headers = kwargs.pop("headers", {})
    headers["Accept"] = "application/vnd.bugcrowd+json"
    headers["Authorization"] = f"Token {BUGCROWD_API_USERNAME}:{BUGCROWD_API_PASSWORD}"
    headers["Bugcrowd-Version"] = BUGCROWD_API_VERSION
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

# Create the MCP server
mcp = FastMCP("Bugcrowd-MCP")

# ACCESS INVITATIONS
@mcp.tool()
async def get_access_invitations(**query_params):
    """List all access invitations."""
    return await bugcrowd_request("GET", "/access_invitations", params=query_params)

@mcp.tool()
async def get_access_invitation(id: str, **query_params):
    """Get a specific access invitation by ID."""
    return await bugcrowd_request("GET", f"/access_invitations/{id}", params=query_params)

@mcp.tool()
async def post_access_invitations(data: dict):
    """Create a new access invitation."""
    return await bugcrowd_request("POST", "/access_invitations", json=data)

@mcp.tool()
async def delete_access_invitation(id: str):
    """Delete an access invitation by ID."""
    return await bugcrowd_request("DELETE", f"/access_invitations/{id}")

# ASSETS
@mcp.tool()
async def get_customer_assets(**query_params):
    """List all customer assets."""
    return await bugcrowd_request("GET", "/customer_assets", params=query_params)

@mcp.tool()
async def get_customer_asset(id: str, **query_params):
    """Get a specific customer asset by ID."""
    return await bugcrowd_request("GET", f"/customer_assets/{id}", params=query_params)

@mcp.tool()
async def post_customer_assets(data: dict):
    """Create a new customer asset."""
    return await bugcrowd_request("POST", "/customer_assets", json=data)

@mcp.tool()
async def patch_customer_asset(id: str, data: dict):
    """Update a customer asset by ID."""
    return await bugcrowd_request("PATCH", f"/customer_assets/{id}", json=data)

@mcp.tool()
async def delete_customer_asset(id: str):
    """Delete a customer asset by ID."""
    return await bugcrowd_request("DELETE", f"/customer_assets/{id}")

# ORGANIZATIONS
@mcp.tool()
async def get_organizations(**query_params):
    """List all organizations."""
    return await bugcrowd_request("GET", "/organizations", params=query_params)

@mcp.tool()
async def get_organization(id: str, **query_params):
    """Get a specific organization by ID."""
    return await bugcrowd_request("GET", f"/organizations/{id}", params=query_params)

@mcp.tool()
async def patch_organization(id: str, data: dict):
    """Update an organization by ID."""
    return await bugcrowd_request("PATCH", f"/organizations/{id}", json=data)

# PROGRAMS
@mcp.tool()
async def get_programs(**query_params):
    """List all programs."""
    return await bugcrowd_request("GET", "/programs", params=query_params)

@mcp.tool()
async def get_program(id: str, **query_params):
    """Get a specific program by ID."""
    return await bugcrowd_request("GET", f"/programs/{id}", params=query_params)

# REPORTS
@mcp.tool()
async def get_reports(**query_params):
    """List all reports."""
    return await bugcrowd_request("GET", "/reports", params=query_params)

@mcp.tool()
async def get_report(id: str, **query_params):
    """Get a specific report by ID."""
    return await bugcrowd_request("GET", f"/reports/{id}", params=query_params)

@mcp.tool()
async def post_reports(data: dict):
    """Create a new report."""
    return await bugcrowd_request("POST", "/reports", json=data)

@mcp.tool()
async def patch_report(id: str, data: dict):
    """Update a report by ID."""
    return await bugcrowd_request("PATCH", f"/reports/{id}", json=data)

@mcp.tool()
async def delete_report(id: str):
    """Delete a report by ID."""
    return await bugcrowd_request("DELETE", f"/reports/{id}")

# SUBMISSIONS
@mcp.tool()
async def get_submissions(**query_params):
    """List all submissions."""
    return await bugcrowd_request("GET", "/submissions", params=query_params)

@mcp.tool()
async def get_submission(id: str, **query_params):
    """Get a specific submission by ID."""
    return await bugcrowd_request("GET", f"/submissions/{id}", params=query_params)

@mcp.tool()
async def post_submissions(data: dict):
    """Create a new submission."""
    return await bugcrowd_request("POST", "/submissions", json=data)

@mcp.tool()
async def patch_submission(id: str, data: dict):
    """Update a submission by ID."""
    return await bugcrowd_request("PATCH", f"/submissions/{id}", json=data)

@mcp.tool()
async def delete_submission(id: str):
    """Delete a submission by ID."""
    return await bugcrowd_request("DELETE", f"/submissions/{id}")

# SUBMISSION ACTIVITIES
@mcp.tool()
async def get_submission_activities(**query_params):
    """List all submission activities."""
    return await bugcrowd_request("GET", "/submission_activities", params=query_params)

@mcp.tool()
async def get_submission_activity(id: str, **query_params):
    """Get a specific submission activity by ID."""
    return await bugcrowd_request("GET", f"/submission_activities/{id}", params=query_params)

# SUBMISSION COMMENTS
@mcp.tool()
async def get_submission_comments(**query_params):
    """List all submission comments."""
    return await bugcrowd_request("GET", "/submission_comments", params=query_params)

@mcp.tool()
async def get_submission_comment(id: str, **query_params):
    """Get a specific submission comment by ID."""
    return await bugcrowd_request("GET", f"/submission_comments/{id}", params=query_params)

# AUTHENTICATION LOGS
@mcp.tool()
async def get_authentication_logs(**query_params):
    """List all authentication logs."""
    return await bugcrowd_request("GET", "/authentication_logs", params=query_params)

# AUTHORIZATION LOGS
@mcp.tool()
async def get_authorization_logs(**query_params):
    """List all authorization logs."""
    return await bugcrowd_request("GET", "/authorization_logs", params=query_params)

# DISCLOSURE REQUESTS
@mcp.tool()
async def get_disclosure_requests(**query_params):
    """List all disclosure requests."""
    return await bugcrowd_request("GET", "/disclosure_requests", params=query_params)

@mcp.tool()
async def get_disclosure_request(id: str, **query_params):
    """Get a specific disclosure request by ID."""
    return await bugcrowd_request("GET", f"/disclosure_requests/{id}", params=query_params)

@mcp.tool()
async def post_disclosure_requests(data: dict):
    """Create a new disclosure request."""
    return await bugcrowd_request("POST", "/disclosure_requests", json=data)

# EXTERNAL ISSUES
@mcp.tool()
async def get_external_issues(**query_params):
    """List all external issues."""
    return await bugcrowd_request("GET", "/external_issues", params=query_params)

@mcp.tool()
async def get_external_issue(id: str, **query_params):
    """Get a specific external issue by ID."""
    return await bugcrowd_request("GET", f"/external_issues/{id}", params=query_params)

@mcp.tool()
async def post_external_issues(data: dict):
    """Create a new external issue."""
    return await bugcrowd_request("POST", "/external_issues", json=data)

@mcp.tool()
async def patch_external_issue(id: str, data: dict):
    """Update an external issue by ID."""
    return await bugcrowd_request("PATCH", f"/external_issues/{id}", json=data)

@mcp.tool()
async def delete_external_issue(id: str):
    """Delete an external issue by ID."""
    return await bugcrowd_request("DELETE", f"/external_issues/{id}")

# MONETARY REWARDS
@mcp.tool()
async def get_monetary_rewards(**query_params):
    """List all monetary rewards."""
    return await bugcrowd_request("GET", "/monetary_rewards", params=query_params)

@mcp.tool()
async def get_monetary_reward(id: str, **query_params):
    """Get a specific monetary reward by ID."""
    return await bugcrowd_request("GET", f"/monetary_rewards/{id}", params=query_params)

# PAYMENTS
@mcp.tool()
async def get_payments(**query_params):
    """List all payments."""
    return await bugcrowd_request("GET", "/payments", params=query_params)

@mcp.tool()
async def get_payment(id: str, **query_params):
    """Get a specific payment by ID."""
    return await bugcrowd_request("GET", f"/payments/{id}", params=query_params)

# TARGET GROUPS
@mcp.tool()
async def get_target_groups(**query_params):
    """List all target groups."""
    return await bugcrowd_request("GET", "/target_groups", params=query_params)

@mcp.tool()
async def get_target_group(id: str, **query_params):
    """Get a specific target group by ID."""
    return await bugcrowd_request("GET", f"/target_groups/{id}", params=query_params)

# USERS
@mcp.tool()
async def get_users(**query_params):
    """List all users."""
    return await bugcrowd_request("GET", "/users", params=query_params)

@mcp.tool()
async def get_user(id: str, **query_params):
    """Get a specific user by ID."""
    return await bugcrowd_request("GET", f"/users/{id}", params=query_params)

# ... more tools for other endpoints can be added in the same pattern ...

if __name__ == "__main__":
    mcp.run("stdio")
