from .server import serve


def main():
    import sys
    import asyncio

    if len(sys.argv) < 2:
        print("Usage: python server.py <obsidian_vault_path>")
        sys.exit(1)

    obsidian_vault_path = sys.argv[1]
    asyncio.run(serve(obsidian_vault_path))


if __name__ == "__main__":
    main()
