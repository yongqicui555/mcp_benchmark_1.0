# Copyright (c) 2025 chris-sun-star
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

import os
import subprocess
import logging
from mcp.server.fastmcp import FastMCP

env = os.environ.copy()

mcp = FastMCP("kubernetes")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("kubernetes")

@mcp.tool()
def execute_kubectl_command(cmd: str) -> str:
    """Execute kubectl command and return the output.

    Args:
        cmd: A bash command using kubectl to interact with Kubernetes cluster.(e.g. 'kubectl get pods -n default')
    """
    try:
        logger.info("run kubectl cmd {0}".format(cmd))
        result = subprocess.run(["bash", "-c", cmd],
                                env=env,
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                                )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"Run kubectl command failed: {e.stderr}")

if __name__ == "__main__":
    mcp.run(transport='stdio')
