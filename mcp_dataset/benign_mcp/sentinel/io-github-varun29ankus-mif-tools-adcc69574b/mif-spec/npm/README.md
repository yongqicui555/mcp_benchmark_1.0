# @varunshodh/mif-tools

Vendor-neutral memory portability for AI agents. Convert between memory formats (mem0, CrewAI, LangChain, markdown, generic JSON) and the [Memory Interchange Format (MIF)](https://github.com/varun29ankuS/mif-spec).

## Install

```bash
npm install @varunshodh/mif-tools
```

## CLI

```bash
# Convert mem0 export to MIF
npx mif convert memories.json --from mem0 --to shodh -o output.json

# Auto-detect format
npx mif convert memories.json -o output.json

# Validate MIF document
npx mif validate memories.mif.json

# List available formats
npx mif formats
```

## API

```typescript
import { load, dump, convert, listFormats, AdapterRegistry } from '@varunshodh/mif-tools';

// Load from any format (auto-detects)
const doc = load(inputJson);
console.log(`${doc.memories.length} memories loaded`);

// Convert between formats
const markdown = dump(doc, 'markdown');
const mifJson = dump(doc, 'shodh');

// One-liner conversion
const result = convert(inputData, { from: 'mem0', to: 'shodh' });

// List supported formats
const formats = listFormats();
```

## Supported Formats

| Format | ID | Description |
|--------|----|-------------|
| MIF v2 (Shodh) | `shodh` | Native MIF v2 JSON, lossless round-trip |
| mem0 | `mem0` | mem0 JSON array |
| CrewAI | `crewai` | CrewAI LTMSQLiteStorage export |
| LangChain | `langchain` | LangChain/LangMem Item export |
| Generic JSON | `generic` | JSON array with `content` field |
| Markdown | `markdown` | YAML frontmatter blocks |

## Docs

Full documentation: https://varun29ankuS.github.io/mif-spec/

## License

Apache 2.0
