from . import server
import asyncio
import argparse


def main():
    parser = argparse.ArgumentParser(description='Kusto MCP Server')
    parser.add_argument('--cluster', help='Kusto cluster', required=True)
    parser.add_argument('--authority_id', help='Kusto tenant id', required=False)
    parser.add_argument('--client_id', help='Client Id to login to kusto', required=False)
    parser.add_argument('--client_secret', help='Client secret to login to kusto', required=False)
    args = parser.parse_args()

    asyncio.run(server.main(args.cluster, args.authority_id, args.client_id, args.client_secret))


__all__ = ['main', 'server']
