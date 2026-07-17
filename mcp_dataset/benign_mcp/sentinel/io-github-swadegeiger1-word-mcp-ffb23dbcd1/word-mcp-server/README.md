# Word MCP Server

Minimal MCP server for Microsoft Word document operations using python-docx.

<!-- mcp-name: io.github.swadegeiger1/word-mcp -->

## Features

- **read_word_document**: Read text from .docx files
- **create_word_document**: Create new Word documents
- **append_to_document**: Add content to existing documents

## Installation

```bash
cd ~/word-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x server.py
```

## Configuration

Add to `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "word-mcp": {
      "command": "~/word-mcp-server/venv/bin/python",
      "args": ["~/word-mcp-server/server.py"]
    }
  }
}
```

**Note:** The `~` will automatically expand to your home directory, making this configuration work for any user.

## Usage Examples

**Read a document:**
```
Read the Word document at ~/Documents/report.docx
```

**Create a document:**
```
Create a Word document at ~/Documents/memo.docx with the content "Meeting Notes\n\nDiscussed Q1 goals"
```

**Append to a document:**
```
Append "Action Items:\n- Review budget" to ~/Documents/memo.docx
```
