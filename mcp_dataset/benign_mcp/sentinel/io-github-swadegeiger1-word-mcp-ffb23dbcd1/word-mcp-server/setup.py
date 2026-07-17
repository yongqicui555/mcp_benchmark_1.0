from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="word-mcp-server",
    version="1.0.0",
    author="Swade Geiger",
    author_email="swadeg@amazon.com",
    description="Minimal MCP server for Microsoft Word document operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swadegeiger1/word-mcp-server",
    py_modules=["server"],
    python_requires=">=3.10",
    install_requires=[
        "mcp>=0.9.0",
        "python-docx>=1.1.0",
    ],
    entry_points={
        "console_scripts": [
            "word-mcp-server=server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
