import subprocess
import tempfile
import os
import asyncio
import mcp.types as types
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import base64
from PIL import Image
import io


server = Server("illustrator")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="view",
            description="View a screenshot of the Adobe Ullustrator window",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="run",
            description="Run ExtendScript code in Illustrator",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "ExtendScript/JavaScript code to execute in Illustrator. It will run on the current document. you only need to make the document once",
                    }
                },
                "required": ["code"],
            },
        ),
    ]


def captureIllustrator() -> list[types.TextContent | types.ImageContent]:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        screenshot_path = f.name

    try:
        # Get the position and size of the Illustrator window
        window_info_script = """
            tell application "Adobe Illustrator"
                activate
                delay 1.5
            end tell
            
            tell application "System Events"
                tell process "Adobe Illustrator"
                    set frontWindow to first window
                    set {x, y} to position of frontWindow
                    set {width, height} to size of frontWindow
                    return x & "," & y & "," & width & "," & height
                end tell
            end tell
        """
        
        # Get window position and dimensions
        window_info_result = subprocess.run(
            ["osascript", "-e", window_info_script],
            capture_output=True, text=True
        )
        
        if window_info_result.returncode != 0:
            return [types.TextContent(type="text", text=f"Failed to get Illustrator window info: {window_info_result.stderr}")]
            
        window_info = window_info_result.stdout.strip()
        
        # Capture the window using the coordinates
        result = subprocess.run(
            [
                "screencapture",
                "-R", window_info,
                "-x",  # No sound
                screenshot_path,
            ]
        )

        if result.returncode != 0:
            return [types.TextContent(type="text", text="Failed to capture screenshot")]

        # Tell Claude to activate after the screenshot is taken
        subprocess.run(["osascript", "-e", 'tell application "Claude" to activate'])

        with Image.open(screenshot_path) as img:
            if img.mode in ("RGBA", "LA"):
                img = img.convert("RGB")
            buffer = io.BytesIO()
            # Higher quality for better recognition
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            compressed_data = buffer.getvalue()
            screenshot_data = base64.b64encode(compressed_data).decode("utf-8")

        return [
            types.ImageContent(
                type="image",
                mimeType="image/jpeg",
                data=screenshot_data,
            )
        ]

    finally:
        if os.path.exists(screenshot_path):
            os.unlink(screenshot_path)


def runIllustratorScript(code: str) -> list[types.TextContent]:
    script = code.replace('"', '\\"').replace("\n", "\\n")

    applescript = f"""
        tell application "Adobe Illustrator"
            do javascript "{script}"
        end tell
    """

    result = subprocess.run(
        ["osascript", "-e", applescript], capture_output=True, text=True
    )

    if result.returncode != 0:
        return [
            types.TextContent(
                type="text", text=f"Error executing script: {result.stderr}"
            )
        ]

    success_message = "Script executed successfully"
    if result.stdout:
        success_message += f"\nOutput: {result.stdout}"

    return [types.TextContent(type="text", text=success_message)]


@server.call_tool()
async def handleCallTool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "view":
        return captureIllustrator()
    elif name == "run":
        if not arguments or "code" not in arguments:
            return [types.TextContent(type="text", text="No code provided")]
        return runIllustratorScript(arguments["code"])
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="illustrator",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
