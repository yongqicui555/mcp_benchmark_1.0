"""Storage credential and external location management tools for Databricks MCP.

Provides tools for managing Unity Catalog storage credentials (which define
how to authenticate to cloud storage) and external locations (which map
cloud storage paths to Unity Catalog for governance).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all storage credential and external location tools with the MCP server."""

    # -- Storage Credentials ---------------------------------------------------

    @mcp.tool()
    def databricks_list_storage_credentials() -> str:
        """List all storage credentials in the Unity Catalog metastore.

        Storage credentials define authentication methods for accessing cloud
        storage (AWS S3, Azure ADLS, GCS). Each credential can be used by
        one or more external locations.

        Returns:
            JSON array of storage credential objects with name, owner,
            cloud-specific credential info, and metadata.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.storage_credentials.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_storage_credential(name: str) -> str:
        """Get detailed information about a specific storage credential.

        Args:
            name: The name of the storage credential to retrieve.

        Returns:
            JSON object with credential details including name, owner,
            cloud-specific configuration, created_at, and updated_at.
        """
        try:
            w = get_workspace_client()
            result = w.storage_credentials.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_storage_credential(
        name: str,
        comment: str = "",
        aws_iam_role_arn: str = "",
        azure_service_principal_application_id: str = "",
        azure_service_principal_client_secret: str = "",
        azure_service_principal_directory_id: str = "",
    ) -> str:
        """Create a new storage credential in the Unity Catalog metastore.

        Provide cloud-specific authentication parameters for the storage
        credential. For AWS, provide the IAM role ARN. For Azure, provide
        the service principal details.

        The caller must be a metastore admin or have the CREATE_STORAGE_CREDENTIAL
        privilege.

        Args:
            name: Name for the new storage credential. Must be unique.
            comment: Optional human-readable description.
            aws_iam_role_arn: For AWS — the IAM role ARN that provides access
                              to the target S3 bucket(s).
            azure_service_principal_application_id: For Azure — the application
                              (client) ID of the service principal.
            azure_service_principal_client_secret: For Azure — the client secret
                              of the service principal.
            azure_service_principal_directory_id: For Azure — the directory
                              (tenant) ID of the service principal.

        Returns:
            JSON object with the created storage credential details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"name": name}
            if comment:
                kwargs["comment"] = comment

            # Build cloud-specific credential object
            if aws_iam_role_arn:
                from databricks.sdk.service.catalog import AwsIamRoleRequest

                kwargs["aws_iam_role"] = AwsIamRoleRequest(role_arn=aws_iam_role_arn)
            elif azure_service_principal_application_id:
                from databricks.sdk.service.catalog import AzureServicePrincipal

                kwargs["azure_service_principal"] = AzureServicePrincipal(
                    directory_id=azure_service_principal_directory_id,
                    application_id=azure_service_principal_application_id,
                    client_secret=azure_service_principal_client_secret,
                )

            result = w.storage_credentials.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_storage_credential(
        name: str,
        new_name: str = "",
        comment: str = "",
        aws_iam_role_arn: str = "",
    ) -> str:
        """Update an existing storage credential.

        Allows renaming, changing the comment, or updating the cloud-specific
        authentication configuration. Only provided fields are updated.

        Args:
            name: Current name of the storage credential to update.
            new_name: Optional new name for the credential.
            comment: Optional new description.
            aws_iam_role_arn: For AWS — updated IAM role ARN.

        Returns:
            JSON object with the updated storage credential details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"name": name}
            if new_name:
                kwargs["new_name"] = new_name
            if comment:
                kwargs["comment"] = comment
            if aws_iam_role_arn:
                from databricks.sdk.service.catalog import AwsIamRoleRequest

                kwargs["aws_iam_role"] = AwsIamRoleRequest(role_arn=aws_iam_role_arn)

            result = w.storage_credentials.update(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_storage_credential(name: str, force: bool = False) -> str:
        """Delete a storage credential from the Unity Catalog metastore.

        The credential must not be referenced by any external locations unless
        force=True is specified. The caller must be the credential owner or
        a metastore admin.

        Args:
            name: Name of the storage credential to delete.
            force: If True, delete even if referenced by external locations.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.storage_credentials.delete(name, force=force)
            return f"Storage credential '{name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_validate_storage_credential(
        storage_credential_name: str = "",
        url: str = "",
        aws_iam_role_arn: str = "",
    ) -> str:
        """Validate a storage credential's access to a cloud storage location.

        Tests whether the credential can access the specified URL. Can validate
        an existing credential by name or test a new credential configuration
        before creating it.

        Args:
            storage_credential_name: Name of an existing credential to validate.
                                     If empty, provide aws_iam_role_arn to test
                                     a new configuration.
            url: Cloud storage URL to validate access against
                 (e.g. "s3://my-bucket/path" or "abfss://container@account.dfs.core.windows.net/path").
            aws_iam_role_arn: For testing a new AWS credential — the IAM role ARN.

        Returns:
            JSON object with validation results including is_dir, results
            (list of validation checks), and any error messages.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {}
            if storage_credential_name:
                kwargs["storage_credential_name"] = storage_credential_name
            if url:
                kwargs["url"] = url
            if aws_iam_role_arn:
                from databricks.sdk.service.catalog import AwsIamRoleRequest

                kwargs["aws_iam_role"] = AwsIamRoleRequest(role_arn=aws_iam_role_arn)

            result = w.storage_credentials.validate(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    # -- External Locations ----------------------------------------------------

    @mcp.tool()
    def databricks_list_external_locations() -> str:
        """List all external locations in the Unity Catalog metastore.

        External locations map cloud storage paths to Unity Catalog for
        governance. Each external location references a storage credential
        and a cloud storage URL.

        Returns:
            JSON array of external location objects with name, url,
            credential_name, owner, and metadata.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.external_locations.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_external_location(name: str) -> str:
        """Get detailed information about a specific external location.

        Args:
            name: The name of the external location to retrieve.

        Returns:
            JSON object with external location details including name, url,
            credential_name, owner, created_at, and updated_at.
        """
        try:
            w = get_workspace_client()
            result = w.external_locations.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_external_location(
        name: str,
        url: str,
        credential_name: str,
        comment: str = "",
    ) -> str:
        """Create a new external location in the Unity Catalog metastore.

        Maps a cloud storage URL to a storage credential, enabling Unity Catalog
        to govern access to that storage path.

        The caller must be a metastore admin or have the CREATE_EXTERNAL_LOCATION
        privilege.

        Args:
            name: Name for the new external location. Must be unique.
            url: Cloud storage URL that this external location represents
                 (e.g. "s3://my-bucket/path" or "abfss://container@account.dfs.core.windows.net/").
            credential_name: Name of the storage credential to use for access.
            comment: Optional human-readable description.

        Returns:
            JSON object with the created external location details.
        """
        try:
            w = get_workspace_client()
            result = w.external_locations.create(
                name=name,
                url=url,
                credential_name=credential_name,
                comment=comment,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_external_location(name: str, force: bool = False) -> str:
        """Delete an external location from the Unity Catalog metastore.

        The caller must be the external location owner or a metastore admin.

        Args:
            name: Name of the external location to delete.
            force: If True, delete even if the location is used by managed
                   tables or volumes.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.external_locations.delete(name, force=force)
            return f"External location '{name}' deleted successfully."
        except Exception as e:
            return format_error(e)
