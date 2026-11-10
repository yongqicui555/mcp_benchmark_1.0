"""
MCP Dice Roller Server Implementation.

Provides dice rolling tools for tabletop games and random number generation.
"""

import random
import re
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("dice-roller")


@mcp.tool()
def roll_dice(notation: str = "1d6") -> dict:
    """
    Roll dice using standard dice notation (e.g., '2d6', '1d20+5', '3d8-2').

    Args:
        notation: Dice notation string. Examples:
            - '1d6' - Roll one 6-sided die
            - '2d6' - Roll two 6-sided dice
            - '1d20+5' - Roll one 20-sided die and add 5
            - '3d8-2' - Roll three 8-sided dice and subtract 2
            - '4d6kh3' - Roll 4d6, keep highest 3 (D&D stat rolling)
            - '2d20kl1' - Roll 2d20, keep lowest 1 (disadvantage)

    Returns:
        Dictionary with rolls, modifier, and total
    """
    notation = notation.lower().strip()

    # Parse the notation: XdY[kh/kl Z][+/-M]
    pattern = r"^(\d+)d(\d+)(?:(kh|kl)(\d+))?([+-]\d+)?$"
    match = re.match(pattern, notation)

    if not match:
        return {
            "error": f"Invalid dice notation: '{notation}'",
            "hint": "Use format like '2d6', '1d20+5', '4d6kh3'",
        }

    num_dice = int(match.group(1))
    die_sides = int(match.group(2))
    keep_type = match.group(3)  # 'kh' or 'kl' or None
    keep_count = int(match.group(4)) if match.group(4) else None
    modifier = int(match.group(5)) if match.group(5) else 0

    # Validate inputs
    if num_dice < 1 or num_dice > 100:
        return {"error": "Number of dice must be between 1 and 100"}
    if die_sides < 2 or die_sides > 1000:
        return {"error": "Die sides must be between 2 and 1000"}
    if keep_count and keep_count > num_dice:
        return {"error": f"Cannot keep {keep_count} dice when only rolling {num_dice}"}

    # Roll the dice
    rolls = [random.randint(1, die_sides) for _ in range(num_dice)]
    original_rolls = rolls.copy()

    # Apply keep highest/lowest
    kept_rolls = rolls
    dropped_rolls = []
    if keep_type and keep_count:
        sorted_rolls = sorted(rolls, reverse=(keep_type == "kh"))
        kept_rolls = sorted_rolls[:keep_count]
        dropped_rolls = sorted_rolls[keep_count:]

    subtotal = sum(kept_rolls)
    total = subtotal + modifier

    result = {
        "notation": notation,
        "rolls": original_rolls,
        "kept": kept_rolls if keep_type else original_rolls,
        "dropped": dropped_rolls if dropped_rolls else None,
        "subtotal": subtotal,
        "modifier": modifier if modifier != 0 else None,
        "total": total,
    }

    # Clean up None values
    return {k: v for k, v in result.items() if v is not None}


@mcp.tool()
def roll_multiple(notation: str = "1d6", times: int = 1) -> dict:
    """
    Roll the same dice multiple times.

    Args:
        notation: Dice notation (e.g., '1d20+5')
        times: Number of times to roll (1-20)

    Returns:
        Dictionary with all roll results and statistics
    """
    if times < 1 or times > 20:
        return {"error": "Times must be between 1 and 20"}

    results = []
    totals = []

    for i in range(times):
        roll_result = roll_dice(notation)
        if "error" in roll_result:
            return roll_result
        results.append(roll_result)
        totals.append(roll_result["total"])

    return {
        "notation": notation,
        "times": times,
        "results": results,
        "totals": totals,
        "statistics": {
            "min": min(totals),
            "max": max(totals),
            "sum": sum(totals),
            "average": round(sum(totals) / len(totals), 2),
        },
    }


@mcp.tool()
def roll_dnd_stats() -> dict:
    """
    Roll a set of D&D 5e character stats using the standard 4d6 drop lowest method.

    Returns:
        Six ability scores rolled using 4d6, dropping the lowest die
    """
    stats = []

    for _ in range(6):
        result = roll_dice("4d6kh3")
        stats.append(
            {
                "rolls": result["rolls"],
                "kept": result["kept"],
                "total": result["total"],
            }
        )

    totals = [s["total"] for s in stats]

    return {
        "method": "4d6 drop lowest",
        "stats": stats,
        "totals": totals,
        "sum": sum(totals),
        "modifier_total": sum((t - 10) // 2 for t in totals),
    }


@mcp.tool()
def flip_coin(times: int = 1) -> dict:
    """
    Flip a coin one or more times.

    Args:
        times: Number of times to flip (1-100)

    Returns:
        Results of the coin flip(s)
    """
    if times < 1 or times > 100:
        return {"error": "Times must be between 1 and 100"}

    flips = [random.choice(["heads", "tails"]) for _ in range(times)]

    if times == 1:
        return {"result": flips[0]}

    heads_count = flips.count("heads")
    tails_count = flips.count("tails")

    return {
        "flips": flips,
        "count": {"heads": heads_count, "tails": tails_count},
        "total": times,
    }


@mcp.tool()
def pick_random(options: str) -> dict:
    """
    Pick a random option from a comma-separated list.

    Args:
        options: Comma-separated list of options (e.g., "pizza, burger, sushi")

    Returns:
        The randomly selected option
    """
    option_list = [opt.strip() for opt in options.split(",") if opt.strip()]

    if len(option_list) < 2:
        return {"error": "Please provide at least 2 comma-separated options"}

    if len(option_list) > 100:
        return {"error": "Maximum 100 options allowed"}

    choice = random.choice(option_list)

    return {
        "options": option_list,
        "selected": choice,
        "total_options": len(option_list),
    }


@mcp.tool()
def roll_percentile() -> dict:
    """
    Roll percentile dice (d100).

    Returns:
        A random number from 1 to 100
    """
    tens = random.randint(0, 9) * 10
    ones = random.randint(0, 9)
    result = tens + ones
    if result == 0:
        result = 100

    return {
        "tens_die": tens // 10 if tens > 0 else 10,
        "ones_die": ones if ones > 0 or tens > 0 else 10,
        "result": result,
    }


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
