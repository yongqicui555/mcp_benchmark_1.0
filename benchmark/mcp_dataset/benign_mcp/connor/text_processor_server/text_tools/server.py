
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('text-processor-server')



# ---------------- Tools ----------------
@mcp.tool()
def count_words(text: str) -> str:
    """Counts the number of words in the given text.
    Returns the word count and character count."""
    words = text.split()
    chars = len(text)
    return f"Words: {len(words)}, Characters: {chars}, Non-space characters: {len(text.replace(' ', ''))}"


@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverses the given text string.
    Returns the reversed text."""
    try:
        return text[::-1]
    except Exception as e:
        return f"Failed to reverse text: {e}"


if __name__ == "__main__":
    mcp.run()
