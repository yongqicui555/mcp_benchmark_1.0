from fastmcp import FastMCP
from urllib.parse import quote
import requests
import os


def serve(obsidian_vault_path: str):
    mcp = FastMCP("obsidian-omnisearch", log_level="ERROR")

    @mcp.tool()
    def obsidian_notes_search(query: str):
        """Search Obsidian(옵시디언) notes and return absolute paths to the matching notes.
        The returned paths can be used with the read_note tool to view the note contents.
        """
        try:
            search_url: str = "http://localhost:51361/search?q={query}"
            response = requests.get(search_url.format(query=quote(query)))
            response.raise_for_status()  # Raise an exception for bad status codes
            json_response = response.json()
            sorted_results = sorted(
                json_response, key=lambda x: x["score"], reverse=True
            )
            return [
                f"<title>{item['basename']}</title>\n"
                f"<excerpt>{item['excerpt']}</excerpt>\n"
                f"<score>{item['score']}</score>\n"
                f"<filepath>{os.path.join(obsidian_vault_path, item['path'].lstrip('/'))}</filepath>"
                for item in sorted_results
            ]

        except Exception:
            return []

    @mcp.tool()
    def read_note(filepath: str):
        """Read and return the contents of an Obsidian note file."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content

    mcp.run()
