"""
Config file parser for extracting coding standards.

Supports:
- .editorconfig
- .prettierrc (JSON, YAML, JS)
- .eslintrc (JSON, YAML, JS)
- pyproject.toml (Python)
- Cargo.toml (Rust)
- package.json (JavaScript/TypeScript)
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomli as tomllib
except ImportError:
    import tomllib  # Python 3.11+

try:
    import yaml
except ImportError:
    yaml = None  # Optional dependency


class ConfigParser:
    """Parse various config files to extract coding standards."""

    def __init__(self, project_path: str):
        """
        Initialize the config parser.

        Args:
            project_path: Root path of the project to analyze
        """
        self.project_path = Path(project_path).resolve()
        self.standards: Dict[str, Any] = {
            "formatting": {},
            "linting": {},
            "project_info": {},
            "language_specific": {},
        }

    def parse_all(self) -> Dict[str, Any]:
        """
        Parse all available config files in the project.

        Returns:
            Dictionary containing extracted standards
        """
        # Parse in order of specificity (most general first)
        self.parse_editorconfig()
        self.parse_prettier()
        self.parse_eslint()
        self.parse_python_config()
        self.parse_rust_config()
        self.parse_package_json()

        return self.standards

    def parse_editorconfig(self) -> None:
        """Parse .editorconfig file."""
        config_path = self.project_path / ".editorconfig"
        if not config_path.exists():
            return

        current_section = "root"
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#") or line.startswith(";"):
                    continue

                # Section header
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                    continue

                # Key-value pair
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Apply to root or all files
                    if current_section in ["root", "*", "**/*"]:
                        self._set_formatting_rule(key, value, source="editorconfig")

    def parse_prettier(self) -> None:
        """Parse .prettierrc or .prettierrc.json file."""
        # Try different prettier config file names
        config_files = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.yaml",
            ".prettierrc.yml",
            ".prettierrc.js",
        ]

        for config_name in config_files:
            config_path = self.project_path / config_name
            if not config_path.exists():
                continue

            if config_name.endswith((".json", ".prettierrc")):
                with open(config_path, "r") as f:
                    try:
                        config = json.load(f)
                        self._process_prettier_config(config)
                        return
                    except json.JSONDecodeError:
                        # .prettierrc without extension might be YAML
                        if yaml and config_name == ".prettierrc":
                            with open(config_path, "r") as yf:
                                try:
                                    config = yaml.safe_load(yf)
                                    self._process_prettier_config(config)
                                    return
                                except yaml.YAMLError:
                                    pass

            elif yaml and config_name.endswith((".yaml", ".yml")):
                with open(config_path, "r") as f:
                    try:
                        config = yaml.safe_load(f)
                        self._process_prettier_config(config)
                        return
                    except yaml.YAMLError:
                        pass

    def parse_eslint(self) -> None:
        """Parse .eslintrc or .eslintrc.json file."""
        config_files = [".eslintrc", ".eslintrc.json", ".eslintrc.yaml", ".eslintrc.yml"]

        for config_name in config_files:
            config_path = self.project_path / config_name
            if not config_path.exists():
                continue

            if config_name.endswith(".json") or config_name == ".eslintrc":
                with open(config_path, "r") as f:
                    try:
                        config = json.load(f)
                        self._process_eslint_config(config)
                        return
                    except json.JSONDecodeError:
                        pass

            elif yaml and config_name.endswith((".yaml", ".yml")):
                with open(config_path, "r") as f:
                    try:
                        config = yaml.safe_load(f)
                        self._process_eslint_config(config)
                        return
                    except yaml.YAMLError:
                        pass

    def parse_python_config(self) -> None:
        """Parse pyproject.toml for Python projects."""
        config_path = self.project_path / "pyproject.toml"
        if not config_path.exists():
            return

        with open(config_path, "rb") as f:
            try:
                config = tomllib.load(f)

                # Extract project info
                if "project" in config:
                    self.standards["project_info"]["name"] = config["project"].get("name")
                    self.standards["project_info"]["description"] = config["project"].get(
                        "description"
                    )

                # Extract tool configurations
                if "tool" in config:
                    tools = config["tool"]

                    # Black (code formatter)
                    if "black" in tools:
                        black_config = tools["black"]
                        if "line-length" in black_config:
                            self._set_formatting_rule(
                                "max_line_length",
                                black_config["line-length"],
                                source="black",
                            )

                    # Ruff (linter/formatter)
                    if "ruff" in tools:
                        ruff_config = tools["ruff"]
                        if "line-length" in ruff_config:
                            self._set_formatting_rule(
                                "max_line_length", ruff_config["line-length"], source="ruff"
                            )

                    # isort (import sorting)
                    if "isort" in tools:
                        self.standards["language_specific"]["python_import_sorting"] = "isort"

                    # mypy (type checking)
                    if "mypy" in tools:
                        self.standards["language_specific"]["python_type_checking"] = "mypy"

            except Exception:
                pass

    def parse_rust_config(self) -> None:
        """Parse Cargo.toml for Rust projects."""
        config_path = self.project_path / "Cargo.toml"
        if not config_path.exists():
            return

        with open(config_path, "rb") as f:
            try:
                config = tomllib.load(f)

                if "package" in config:
                    self.standards["project_info"]["name"] = config["package"].get("name")
                    self.standards["project_info"]["description"] = config["package"].get(
                        "description"
                    )

                self.standards["language_specific"]["language"] = "rust"

            except Exception:
                pass

    def parse_package_json(self) -> None:
        """Parse package.json for JavaScript/TypeScript projects."""
        config_path = self.project_path / "package.json"
        if not config_path.exists():
            return

        with open(config_path, "r") as f:
            try:
                config = json.load(f)

                # Extract project info
                self.standards["project_info"]["name"] = config.get("name")
                self.standards["project_info"]["description"] = config.get("description")

                # Extract scripts (reveals project conventions)
                if "scripts" in config:
                    scripts = config["scripts"]
                    self.standards["project_info"]["scripts"] = scripts

                    # Detect package manager from scripts
                    script_str = json.dumps(scripts)
                    if "pnpm" in script_str:
                        self.standards["project_info"]["package_manager"] = "pnpm"
                    elif "yarn" in script_str:
                        self.standards["project_info"]["package_manager"] = "yarn"
                    else:
                        self.standards["project_info"]["package_manager"] = "npm"

                # Extract dependencies (reveals tech stack)
                dependencies = {}
                if "dependencies" in config:
                    dependencies.update(config["dependencies"])
                if "devDependencies" in config:
                    dependencies.update(config["devDependencies"])

                # Detect frameworks
                if "react" in dependencies:
                    self.standards["language_specific"]["framework"] = "React"
                elif "vue" in dependencies:
                    self.standards["language_specific"]["framework"] = "Vue"
                elif "angular" in dependencies or "@angular/core" in dependencies:
                    self.standards["language_specific"]["framework"] = "Angular"
                elif "next" in dependencies:
                    self.standards["language_specific"]["framework"] = "Next.js"

            except Exception:
                pass

    def _process_prettier_config(self, config: Dict[str, Any]) -> None:
        """Process parsed Prettier configuration."""
        mapping = {
            "printWidth": "max_line_length",
            "tabWidth": "indent_size",
            "useTabs": "indent_style",  # Will convert to "tab" or "space"
            "semi": "semicolons",
            "singleQuote": "quote_style",
            "trailingComma": "trailing_commas",
            "arrowParens": "arrow_parens",
        }

        for prettier_key, standard_key in mapping.items():
            if prettier_key in config:
                value = config[prettier_key]

                # Convert boolean useTabs to indent_style
                if prettier_key == "useTabs":
                    value = "tab" if value else "space"
                # Convert boolean singleQuote to quote_style
                elif prettier_key == "singleQuote":
                    value = "single" if value else "double"

                self._set_formatting_rule(standard_key, value, source="prettier")

    def _process_eslint_config(self, config: Dict[str, Any]) -> None:
        """Process parsed ESLint configuration."""
        if "rules" not in config:
            return

        rules = config["rules"]

        # Extract relevant formatting rules
        if "quotes" in rules:
            quote_rule = rules["quotes"]
            if isinstance(quote_rule, list) and len(quote_rule) > 1:
                self._set_formatting_rule("quote_style", quote_rule[1], source="eslint")

        if "semi" in rules:
            semi_rule = rules["semi"]
            if isinstance(semi_rule, list):
                value = semi_rule[1] if len(semi_rule) > 1 else semi_rule[0]
            else:
                value = semi_rule
            self._set_formatting_rule("semicolons", value == "always", source="eslint")

        if "max-len" in rules:
            max_len_rule = rules["max-len"]
            if isinstance(max_len_rule, list) and len(max_len_rule) > 1:
                if isinstance(max_len_rule[1], dict):
                    code_len = max_len_rule[1].get("code")
                    if code_len:
                        self._set_formatting_rule("max_line_length", code_len, source="eslint")
                else:
                    self._set_formatting_rule("max_line_length", max_len_rule[1], source="eslint")

    def _set_formatting_rule(self, key: str, value: Any, source: str) -> None:
        """Set a formatting rule with source tracking."""
        # Map editorconfig keys to standard keys
        key_mapping = {
            "indent_style": "indent_style",
            "indent_size": "indent_size",
            "end_of_line": "line_ending",
            "charset": "charset",
            "trim_trailing_whitespace": "trim_whitespace",
            "insert_final_newline": "final_newline",
        }

        standard_key = key_mapping.get(key, key)

        # Only set if not already set or if from a more specific source
        if standard_key not in self.standards["formatting"]:
            self.standards["formatting"][standard_key] = {"value": value, "source": source}
        elif source == "prettier":  # Prettier overrides editorconfig
            self.standards["formatting"][standard_key] = {"value": value, "source": source}

    def get_standards(self) -> Dict[str, Any]:
        """Get the extracted standards."""
        return self.standards
