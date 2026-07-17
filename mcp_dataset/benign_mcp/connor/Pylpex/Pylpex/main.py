
from app import get_mcp

mcp = get_mcp()

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()