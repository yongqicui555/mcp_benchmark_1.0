# MCP Dice Roller 🎲

A simple MCP (Model Context Protocol) server for rolling dice. Perfect for tabletop games, random decisions, and more!

<!-- mcp-name: io.github.vandewilly/dice-roller -->

## Features

- **Standard Dice Notation** - Roll any dice using notation like `2d6`, `1d20+5`, `3d8-2`
- **Keep Highest/Lowest** - Support for `4d6kh3` (keep highest 3) and `2d20kl1` (keep lowest)
- **D&D Stat Rolling** - Quick character stat generation using 4d6 drop lowest
- **Coin Flips** - Simple heads or tails
- **Random Picker** - Choose randomly from a list of options
- **Percentile Dice** - Roll d100 with tens and ones dice

## Installation

```bash
pip install mcp-dice-roller
```

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "dice-roller": {
      "command": "python",
      "args": ["-m", "mcp_dice_roller"]
    }
  }
}
```

### With VS Code

Add to your VS Code MCP settings:

```json
{
  "mcp.servers": {
    "dice-roller": {
      "command": "python",
      "args": ["-m", "mcp_dice_roller"]
    }
  }
}
```

## Tools

### roll_dice

Roll dice using standard notation.

```
roll_dice("2d6")       → Roll two 6-sided dice
roll_dice("1d20+5")    → Roll d20 and add 5
roll_dice("4d6kh3")    → Roll 4d6, keep highest 3
roll_dice("2d20kl1")   → Roll 2d20, keep lowest (disadvantage)
```

**Example Response:**
```json
{
  "notation": "2d6+3",
  "rolls": [4, 6],
  "kept": [4, 6],
  "subtotal": 10,
  "modifier": 3,
  "total": 13
}
```

### roll_multiple

Roll the same dice multiple times with statistics.

```
roll_multiple("1d20", 5)  → Roll d20 five times
```

**Example Response:**
```json
{
  "notation": "1d20",
  "times": 5,
  "totals": [15, 8, 20, 3, 12],
  "statistics": {
    "min": 3,
    "max": 20,
    "sum": 58,
    "average": 11.6
  }
}
```

### roll_dnd_stats

Generate D&D 5e character ability scores.

**Example Response:**
```json
{
  "method": "4d6 drop lowest",
  "stats": [
    {"rolls": [4, 3, 5, 6], "kept": [4, 5, 6], "total": 15},
    {"rolls": [2, 4, 4, 3], "kept": [3, 4, 4], "total": 11},
    ...
  ],
  "totals": [15, 11, 14, 13, 10, 16],
  "sum": 79
}
```

### flip_coin

Flip a coin.

```
flip_coin()      → Flip once
flip_coin(10)    → Flip 10 times
```

### pick_random

Pick randomly from options.

```
pick_random("pizza, burger, sushi, tacos")
```

**Example Response:**
```json
{
  "options": ["pizza", "burger", "sushi", "tacos"],
  "selected": "sushi",
  "total_options": 4
}
```

### roll_percentile

Roll d100 (percentile dice).

**Example Response:**
```json
{
  "tens_die": 7,
  "ones_die": 3,
  "result": 73
}
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/vandewilly/mcp-dice-roller.git
cd mcp-dice-roller

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Running Locally

```bash
python -m mcp_dice_roller
```

## MCP Registry

**MCP Name:** `io.github.vandewilly/dice-roller`

This server is published to the [MCP Registry](https://registry.modelcontextprotocol.io/).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Vandewilly Silva ([@vandewilly](https://github.com/vandewilly))
