<!-- mcp-name: io.github.saicharanrajoju/letswork -->

# LetsWork

**Real-time collaborative coding via Claude Code** — two developers, one codebase, each using their own Claude subscription.

One developer hosts the session. The other joins from anywhere. Both get a live Claude Code window connected to the same project — with file locking and an approval system to prevent conflicts.

---

## How It Works

1. **Host** runs `letswork start` inside their project folder
2. A secure HTTPS tunnel is created automatically via Cloudflare
3. A one-time URL + guest token is generated and printed
4. Host shares the join command with the guest
5. **Guest** runs `letswork join <url> --token <token>` on their machine
6. Both developers now have Claude Code connected to the same codebase

---

## Requirements

| Requirement | macOS | Windows (WSL) |
|-------------|-------|---------------|
| Python 3.10+ | `brew install python` | Comes with Ubuntu WSL |
| cloudflared | `brew install cloudflared` | See WSL section below |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | `npm install -g @anthropic-ai/claude-code` (inside WSL) |
| Node.js | `brew install node` | `sudo apt install nodejs npm` (inside WSL) |

---

## macOS — Host Setup

> The host is the developer who owns the project. You start the session and share the join command.

### Step 1 — Install dependencies

```bash
brew install cloudflared
pip install letswork
```

### Step 2 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### Step 3 — Start the session

Navigate to your project folder and run:

```bash
cd /path/to/your/project
letswork start
```

You will be asked for your display name, then a session box appears:

```
╔══════════════════════════════════════════════════════════════════════╗
║  🤝 LetsWork Session Active                                          ║
║                                                                      ║
║  Send this command to your collaborator:                             ║
║  letswork join https://abc123.trycloudflare.com --token a1b2c3d4    ║
║                                                                      ║
║  Press Ctrl+C to stop.                                               ║
╚══════════════════════════════════════════════════════════════════════╝
```

**Copy the full `letswork join ...` command and send it to your collaborator.**

Two new terminal windows open automatically:
- Claude Code — already connected to LetsWork
- A chat window to communicate with your collaborator

### Step 4 — Approve guest changes

When the guest edits a file, you'll see a notification in Claude Code. Ask Claude:

```
get_pending_changes
```

Then approve or reject:

```
approve_change <id>
reject_change <id>
```

### Step 5 — Stop the session

Press `Ctrl+C` in the terminal where you ran `letswork start`.

---

## macOS — Guest Setup

> The guest connects to the host's project. You need the join command from the host.

### Step 1 — Install dependencies

```bash
brew install cloudflared
pip install letswork
```

### Step 2 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### Step 3 — Join the session

Run the command the host sent you:

```bash
letswork join https://abc123.trycloudflare.com --token a1b2c3d4
```

You'll be asked for your display name. Then two windows open:
- Claude Code — connected to the host's project
- A chat window to communicate with the host

### Step 4 — Edit files

Ask Claude to read and edit files normally. When you write a file, it goes into an approval queue — the host reviews it before it's written to disk. You'll get a notification when it's approved or rejected.

---

## Windows — Guest Setup (WSL)

> LetsWork runs inside WSL (Windows Subsystem for Linux). The guest experience is the same as macOS once WSL is set up.

### Step 1 — Enable WSL and install Ubuntu

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

Restart your computer when prompted. Ubuntu will install automatically.

Open **Ubuntu** from the Start menu and set up your Linux username and password.

### Step 2 — Install dependencies inside Ubuntu

Open Ubuntu and run these one by one:

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip -y

# Install Node.js and npm
sudo apt install nodejs npm -y

# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Install letswork
pip3 install letswork
```

### Step 3 — Install Claude Code inside Ubuntu

```bash
npm install -g @anthropic-ai/claude-code
```

### Step 4 — Join the session

Run the command the host sent you, inside Ubuntu:

```bash
letswork join https://abc123.trycloudflare.com --token a1b2c3d4
```

You'll be asked for your display name. Claude Code launches directly in the same terminal window.

> **Note for Windows users:** Claude Code runs in the WSL terminal — not as a separate window. Everything else works identically to macOS.

---

## MCP Tools Available

Both host and guest have access to these tools inside Claude Code:

| Tool | Who Can Use | Description |
|------|-------------|-------------|
| `list_files` | Both | List files and directories with lock status |
| `read_file` | Both | Read file contents (1MB limit, text files only) |
| `write_file` | Both | Submit a file change (guest changes need host approval) |
| `lock_file` | Both | Lock a file for exclusive editing |
| `unlock_file` | Both | Release your own file lock |
| `get_status` | Both | Show session info, connected users, and active locks |
| `get_notifications` | Both | Quick summary of what needs attention |
| `ping` | Both | Verify connection to the host MCP server |
| `set_display_name` | Guest only | Set your display name for the session |
| `my_pending_changes` | Guest only | View your submitted changes awaiting approval |
| `get_pending_changes` | Host only | View all changes awaiting approval with diffs |
| `approve_change` | Host only | Approve a pending change and write it to disk |
| `reject_change` | Host only | Reject a pending change |
| `force_unlock` | Host only | Force-release a stuck file lock |

---

## Approval Flow

Guest file writes do not go directly to disk — they go through the host's approval queue:

1. Guest asks Claude to edit a file → `write_file` submits the change
2. Host sees: `📝 guest submitted change to server.py (ID: a1b2c3)`
3. Host asks Claude: `get_pending_changes` — sees a full diff
4. Host approves: `approve_change a1b2c3` → file is written to disk
5. Or rejects: `reject_change a1b2c3` → guest is notified

---

## Security

- Random Cloudflare subdomain — URL is unguessable
- Cryptographic token — second auth layer on top of the URL
- All traffic encrypted via HTTPS
- Path traversal prevention — guest cannot access files outside the project root
- File locks auto-expire after 30 minutes
- No accounts, no signup, no persistent credentials — session ends when host stops

---

## Constraints

- Maximum 2 users per session (Host + 1 Guest)
- Text files only — binary files not supported
- 1MB file size limit per read/write operation
- Guest has no shell access — file operations only
- `cloudflared` must be installed on the **host machine** (guest does not need it on macOS, but WSL guests do)

---

## CLI Reference

```bash
letswork start [--port PORT] [--debug]   # Start a session (default port: 8000)
letswork join <URL> --token <TOKEN>      # Join a session as guest
```

---

## Architecture

```
Host Machine:
[Project Files] ← [MCP Server :8000] ← [Cloudflare Tunnel] ← HTTPS URL
                                                                    ↑
                                             Guest connects here
                                             via stdio proxy + secret token
```

The guest connects through a stdio proxy rather than directly over HTTP — this avoids Cloudflare SSE reliability issues and gives stable MCP connectivity.

---

## License

MIT — see [LICENSE](LICENSE)

---

Built with the [Model Context Protocol](https://modelcontextprotocol.io).
