"""DBFS and Unity Catalog Volumes file management tools for Databricks MCP.

Provides tools for listing, uploading, downloading, and managing files in both
the legacy DBFS (Databricks File System) and Unity Catalog Volumes file storage.
Upload and download operations use base64-encoded content strings.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all file management tools with the MCP server."""

    # -- DBFS (Databricks File System) -----------------------------------------

    @mcp.tool()
    def databricks_dbfs_list(path: str) -> str:
        """List files and directories at a DBFS path.

        Returns metadata for each entry including file name, path, size,
        and whether it is a directory.

        Args:
            path: Absolute DBFS path to list (e.g. "dbfs:/mnt/data" or "/mnt/data").

        Returns:
            JSON array of file status objects with path, is_dir, file_size,
            and modification_time. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.dbfs.list(path))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_dbfs_get_status(path: str) -> str:
        """Get the status and metadata of a single DBFS path.

        Returns information about whether the path is a file or directory,
        its size, and modification time.

        Args:
            path: Absolute DBFS path to check (e.g. "dbfs:/mnt/data/file.csv").

        Returns:
            JSON object with path, is_dir, file_size, and modification_time.
        """
        try:
            w = get_workspace_client()
            result = w.dbfs.get_status(path)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_dbfs_mkdirs(path: str) -> str:
        """Create a directory in DBFS, including any necessary parent directories.

        Works like "mkdir -p" -- creates the full directory tree if intermediate
        directories do not exist. No error if the directory already exists.

        Args:
            path: Absolute DBFS path of the directory to create
                  (e.g. "dbfs:/mnt/data/output").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.dbfs.mkdirs(path)
            return f"DBFS directory '{path}' created successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_dbfs_delete(path: str, recursive: bool = False) -> str:
        """Delete a file or directory from DBFS.

        For directories, set recursive=True to delete all contents.
        Attempting to delete a non-empty directory without recursive=True
        will result in an error.

        Args:
            path: Absolute DBFS path to delete (e.g. "dbfs:/mnt/data/old_file.csv").
            recursive: If True, recursively delete all files and subdirectories.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.dbfs.delete(path, recursive=recursive)
            return f"DBFS path '{path}' deleted successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_dbfs_upload(path: str, contents_base64: str, overwrite: bool = False) -> str:
        """Upload a file to DBFS from base64-encoded content.

        The content must be provided as a base64-encoded string. This is
        suitable for files up to a few MB. For very large files, consider
        using the DBFS streaming API directly.

        Args:
            path: Absolute DBFS destination path (e.g. "dbfs:/mnt/data/upload.csv").
            contents_base64: The file content encoded as a base64 string.
            overwrite: If True, overwrite any existing file at the path.

        Returns:
            Confirmation message on success.
        """
        try:
            import base64
            import io

            w = get_workspace_client()
            raw_bytes = base64.b64decode(contents_base64)
            w.dbfs.upload(path, io.BytesIO(raw_bytes), overwrite=overwrite)
            return f"File uploaded to DBFS path '{path}' successfully ({len(raw_bytes)} bytes)."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_dbfs_download(path: str) -> str:
        """Download a file from DBFS and return its content as base64.

        Reads the file at the given DBFS path and returns the content
        encoded as a base64 string. Suitable for files up to a few MB.

        Args:
            path: Absolute DBFS path of the file to download
                  (e.g. "dbfs:/mnt/data/report.csv").

        Returns:
            JSON object with 'path', 'content_base64' (the base64-encoded
            file content), and 'size_bytes'.
        """
        try:
            import base64
            import json

            w = get_workspace_client()
            response = w.dbfs.download(path)
            raw_bytes = response.read()
            encoded = base64.b64encode(raw_bytes).decode("ascii")
            return json.dumps({
                "path": path,
                "content_base64": encoded,
                "size_bytes": len(raw_bytes),
            }, indent=2)
        except Exception as e:
            return format_error(e)

    # -- Unity Catalog Volumes Files API ---------------------------------------

    @mcp.tool()
    def databricks_files_list_directory(directory_path: str) -> str:
        """List files and directories within a Unity Catalog Volume path.

        Returns the contents of a directory under a UC Volume. The path should
        be in the Volumes path format.

        Args:
            directory_path: Volume-relative directory path
                            (e.g. "/Volumes/my_catalog/my_schema/my_volume/data").

        Returns:
            JSON array of directory entry objects with path, name, is_directory,
            and file_size. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.files.list_directory_contents(directory_path))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_files_get_metadata(file_path: str) -> str:
        """Get metadata for a file in a Unity Catalog Volume.

        Returns metadata including content type and content length for the
        specified file. Does not return the file contents.

        Args:
            file_path: Volume-relative file path
                       (e.g. "/Volumes/my_catalog/my_schema/my_volume/data/file.csv").

        Returns:
            JSON object with file metadata including content_type and
            content_length.
        """
        try:
            w = get_workspace_client()
            result = w.files.get_metadata(file_path)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_files_create_directory(directory_path: str) -> str:
        """Create a directory in a Unity Catalog Volume.

        Creates the directory at the specified path. Parent directories
        must already exist.

        Args:
            directory_path: Volume-relative directory path to create
                            (e.g. "/Volumes/my_catalog/my_schema/my_volume/output").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.files.create_directory(directory_path)
            return f"Directory '{directory_path}' created successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_files_delete(file_path: str) -> str:
        """Delete a file from a Unity Catalog Volume.

        Permanently removes the file at the specified path. This operation
        cannot be undone.

        Args:
            file_path: Volume-relative file path to delete
                       (e.g. "/Volumes/my_catalog/my_schema/my_volume/data/old.csv").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.files.delete(file_path)
            return f"File '{file_path}' deleted successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_files_upload(file_path: str, contents_base64: str) -> str:
        """Upload a file to a Unity Catalog Volume from base64-encoded content.

        The content must be provided as a base64-encoded string. The file will
        be created at the specified path, overwriting any existing file.

        Args:
            file_path: Volume-relative destination path
                       (e.g. "/Volumes/my_catalog/my_schema/my_volume/data/upload.csv").
            contents_base64: The file content encoded as a base64 string.

        Returns:
            Confirmation message on success including bytes written.
        """
        try:
            import base64
            import io

            w = get_workspace_client()
            raw_bytes = base64.b64decode(contents_base64)
            w.files.upload(file_path, io.BytesIO(raw_bytes))
            return f"File uploaded to '{file_path}' successfully ({len(raw_bytes)} bytes)."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_files_download(file_path: str) -> str:
        """Download a file from a Unity Catalog Volume as base64-encoded content.

        Reads the file at the given Volume path and returns the content
        encoded as a base64 string. Suitable for files up to a few MB.

        Args:
            file_path: Volume-relative file path to download
                       (e.g. "/Volumes/my_catalog/my_schema/my_volume/data/report.csv").

        Returns:
            JSON object with 'path', 'content_base64' (the base64-encoded
            file content), and 'size_bytes'.
        """
        try:
            import base64
            import json

            w = get_workspace_client()
            response = w.files.download(file_path)
            raw_bytes = response.read()
            encoded = base64.b64encode(raw_bytes).decode("ascii")
            return json.dumps({
                "path": file_path,
                "content_base64": encoded,
                "size_bytes": len(raw_bytes),
            }, indent=2)
        except Exception as e:
            return format_error(e)
