# Contributing to ai-scanner-mcp

Thanks for your interest in contributing!

## How to Contribute

### Reporting Bugs

Open an issue with:
- Which MCP client you're using (Claude Code, Cursor, etc.)
- What you asked the agent to do
- What happened vs what you expected
- Your Node.js version and OS

### Suggesting New Tools

If you have an idea for a new MCP tool that ai-scanner could expose, open a feature request with:
- The tool name and description
- Example prompts a user would give
- What the tool should return

### Submitting Code

1. Fork the repo
2. Create a branch (`git checkout -b add-new-tool`)
3. Install dependencies: `npm install`
4. Make your changes to `index.js`
5. Test locally:
   ```bash
   # Verify it loads
   node -e "import('./index.js').then(() => console.log('OK'))"
   
   # Test with Claude Code
   claude mcp add ai-scanner-dev node /path/to/your/index.js
   ```
6. Commit and open a PR

### Adding a New Tool

Tools are registered with `server.tool()` in `index.js`. Follow the existing pattern:

```javascript
server.tool(
  "tool_name",
  "Description of what this tool does — be specific, this is what the AI reads",
  {
    // Zod schema for parameters
    directory: z.string().describe("Path to scan"),
  },
  async ({ directory }) => {
    // Implementation
    return {
      content: [{ type: "text", text: "result" }],
    };
  }
);
```

## Code Style

- ESM imports (`import`/`export`)
- Single `index.js` file — keep it simple
- Descriptive tool descriptions — the AI agent reads these to decide when to use each tool

## Questions?

Open an issue — happy to help.
