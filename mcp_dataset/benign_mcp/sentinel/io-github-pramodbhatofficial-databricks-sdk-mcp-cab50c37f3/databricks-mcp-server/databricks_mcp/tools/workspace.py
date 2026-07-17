"""Workspace object, notebook, and repository tools for Databricks MCP.

Provides tools for browsing and managing workspace objects (notebooks, files,
directories), importing/exporting notebooks, and managing Git repos.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all workspace tools with the MCP server."""

    # ── Workspace Objects ───────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_workspace(path: str = "/") -> str:
        """List objects in a workspace directory.

        Returns notebooks, files, directories, and other objects at the
        specified path. Does not recurse into subdirectories.

        Args:
            path: Absolute workspace path to list (default: root "/").
                  Example: "/Users/user@example.com" or "/Repos".

        Returns:
            JSON array of workspace objects with path, object_type
            (NOTEBOOK, DIRECTORY, FILE, etc.), language, and size.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.workspace.list(path))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_workspace_status(path: str) -> str:
        """Get the status and metadata of a workspace object.

        Returns detailed information about a notebook, file, directory,
        or other workspace object at the given path.

        Args:
            path: Absolute workspace path of the object.
                  Example: "/Users/user@example.com/my_notebook".

        Returns:
            JSON object with path, object_type, object_id, language,
            created_at, modified_at, and size information.
        """
        try:
            w = get_workspace_client()
            result = w.workspace.get_status(path)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_import_notebook(
        path: str,
        content: str,
        format: str = "SOURCE",
        language: str = "PYTHON",
        overwrite: bool = False,
    ) -> str:
        """Import a notebook or file into the workspace.

        Imports content as a notebook at the specified path. The content
        should be base64-encoded. Maximum content size is 10 MB.

        Args:
            path: Absolute workspace path where the notebook will be created.
                  Example: "/Users/user@example.com/my_notebook".
            content: Base64-encoded content of the notebook.
            format: Import format — "SOURCE" (default), "HTML", "JUPYTER",
                    "DBC", "R_MARKDOWN", or "AUTO".
            language: Notebook language — "PYTHON" (default), "SQL", "SCALA",
                      or "R". Required when format is "SOURCE".
            overwrite: If True, overwrite any existing object at the path.

        Returns:
            Confirmation message on success.
        """
        try:
            from databricks.sdk.service.workspace import ImportFormat, Language

            w = get_workspace_client()
            w.workspace.import_(
                path=path,
                content=content,
                format=ImportFormat[format],
                language=Language[language],
                overwrite=overwrite,
            )
            return f"Notebook imported successfully to '{path}'."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_export_notebook(path: str) -> str:
        """Export a notebook from the workspace.

        Exports the notebook source content. The content is returned
        as a base64-encoded string.

        Args:
            path: Absolute workspace path of the notebook to export.
                  Example: "/Users/user@example.com/my_notebook".

        Returns:
            JSON object with the exported content (base64-encoded)
            and the notebook path.
        """
        try:
            from databricks.sdk.service.workspace import ExportFormat

            w = get_workspace_client()
            result = w.workspace.export(path=path, format=ExportFormat.SOURCE)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_mkdirs(path: str) -> str:
        """Create a directory in the workspace.

        Creates the directory and all necessary parent directories if they
        do not exist (similar to "mkdir -p").

        Args:
            path: Absolute workspace path of the directory to create.
                  Example: "/Users/user@example.com/my_project/data".

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.workspace.mkdirs(path)
            return f"Directory '{path}' created successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_workspace(path: str, recursive: bool = False) -> str:
        """Delete a workspace object or directory.

        Deletes a notebook, file, or directory at the given path.
        For directories, use recursive=True to delete all contents.

        Args:
            path: Absolute workspace path of the object to delete.
            recursive: If True, recursively delete all contents of a directory.
                       Required to be True for non-empty directories.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.workspace.delete(path, recursive=recursive)
            return f"Workspace object '{path}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Repos ───────────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_repos() -> str:
        """List all Git repositories configured in the workspace.

        Returns repos accessible to the current user, including their
        URL, provider, branch, and workspace path.

        Returns:
            JSON array of repo objects with id, url, provider, path,
            branch, and head_commit_id. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.repos.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_repo(repo_id: int) -> str:
        """Get detailed information about a specific Git repository.

        Args:
            repo_id: The numeric ID of the repository.

        Returns:
            JSON object with repo details including id, url, provider,
            path, branch, and head_commit_id.
        """
        try:
            w = get_workspace_client()
            result = w.repos.get(repo_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_repo(
        url: str,
        provider: str = "github",
        path: str = "",
    ) -> str:
        """Add a Git repository to the workspace.

        Clones a remote Git repository into the workspace under /Repos.

        Args:
            url: The URL of the Git repository to clone.
                 Example: "https://github.com/org/repo.git".
            provider: Git provider — "github" (default), "gitlab",
                      "bitbucket", "azureDevOps", or "awsCodeCommit".
            path: Optional workspace path for the repo. If empty, the
                  repo is placed at /Repos/<user>/<repo_name>.

        Returns:
            JSON object with the created repo details including its id.
        """
        try:
            w = get_workspace_client()
            kwargs = {"url": url, "provider": provider}
            if path:
                kwargs["path"] = path
            result = w.repos.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_repo(repo_id: int, branch: str) -> str:
        """Update a Git repository to a different branch or tag.

        Checks out the specified branch in the repository. This updates
        all files in the repo to match the branch's HEAD commit.

        Args:
            repo_id: The numeric ID of the repository.
            branch: The name of the branch to check out (e.g. "main", "develop").

        Returns:
            JSON object with the updated repo details including the new
            branch and head_commit_id.
        """
        try:
            w = get_workspace_client()
            result = w.repos.update(repo_id, branch=branch)
            return to_json(result)
        except Exception as e:
            return format_error(e)
