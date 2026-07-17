# mif-tools

<!-- mcp-name: io.github.varun29ankuS/mif-tools -->

Vendor-neutral memory portability for AI agents. Convert between memory formats (mem0, markdown, generic JSON) and the [Memory Interchange Format (MIF)](https://github.com/varun29ankuS/mif-spec).

## Install

```bash
pip install mif-tools

# With schema validation support:
pip install mif-tools[validate]
```

## CLI

```bash
# Convert mem0 export to MIF
mif convert memories.json --from mem0 --to shodh -o memories.mif.json

# Convert with auto-detection
mif convert memories.json -o output.mif.json

# Convert MIF to markdown
mif convert memories.mif.json --to markdown -o memories.md

# Validate MIF document
mif validate memories.mif.json

# Inspect any memory file
mif inspect memories.json

# List available formats
mif formats
```

## Python API

```python
from mif import load, dump, convert, MifDocument, Memory

# Load from any format (auto-detects)
doc = load(open("mem0_export.json").read())
print(f"{len(doc.memories)} memories loaded")

# Access memories
for mem in doc.memories:
    print(f"[{mem.memory_type}] {mem.content}")

# Convert between formats
markdown = dump(doc, format="markdown")
mif_json = dump(doc, format="shodh")

# One-liner conversion
result = convert(input_data, from_format="mem0", to_format="shodh")

# Create from scratch
doc = MifDocument(memories=[
    Memory(
        id="123e4567-e89b-12d3-a456-426614174000",
        content="User prefers dark mode",
        created_at="2026-01-15T10:30:00Z",
        memory_type="observation",
        tags=["preferences", "ui"],
    )
])
print(dump(doc))

# Validate
from mif import validate
is_valid, errors = validate(mif_json)
```

## Supported Formats

| Format | ID | Description |
|--------|----|-------------|
| MIF v2 (Shodh) | `shodh` | Native MIF v2 JSON, lossless round-trip |
| mem0 | `mem0` | mem0 JSON array (`[{"memory": "..."}]`) |
| Generic JSON | `generic` | JSON array with `content` field |
| Markdown | `markdown` | YAML frontmatter blocks (Letta/Obsidian style) |

## MCP Integration

Any MCP memory server can add MIF support:

```python
from mif import load, dump

# In your export_memories tool handler:
def handle_export(user_id: str) -> str:
    memories = my_storage.get_all(user_id)
    return dump(memories)

# In your import_memories tool handler:
def handle_import(data: str) -> dict:
    doc = load(data)  # auto-detects mem0, markdown, generic, MIF
    imported = 0
    for mem in doc.memories:
        my_storage.save(mem.id, mem.content, mem.created_at)
        imported += 1
    return {"memories_imported": imported}
```

## License

Apache 2.0
