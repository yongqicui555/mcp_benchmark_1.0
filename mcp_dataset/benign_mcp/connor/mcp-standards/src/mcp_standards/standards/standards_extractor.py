"""
Standards extractor for detecting project conventions and patterns.

Analyzes:
- Project type (Python, JavaScript, Rust, etc.)
- Package manager (npm, yarn, pnpm, uv, pip, cargo)
- Test framework and commands
- Build process
- Common conventions from README
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class StandardsExtractor:
    """Extract high-level coding standards and project conventions."""

    def __init__(self, project_path: str):
        """
        Initialize the standards extractor.

        Args:
            project_path: Root path of the project to analyze
        """
        self.project_path = Path(project_path).resolve()
        self.conventions: Dict[str, Any] = {
            "project_type": None,
            "languages": [],
            "package_manager": None,
            "test_framework": None,
            "test_command": None,
            "build_command": None,
            "conventions": [],
        }

    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all project conventions and standards.

        Returns:
            Dictionary containing extracted conventions
        """
        self.detect_project_type()
        self.detect_package_manager()
        self.detect_test_framework()
        self.extract_readme_conventions()
        self.detect_common_patterns()

        return self.conventions

    def detect_project_type(self) -> None:
        """Detect the project type based on config files."""
        project_files = {
            "Python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
            "JavaScript": ["package.json", "tsconfig.json"],
            "TypeScript": ["tsconfig.json", "package.json"],
            "Rust": ["Cargo.toml"],
            "Go": ["go.mod", "go.sum"],
            "Ruby": ["Gemfile", "Gemfile.lock"],
            "PHP": ["composer.json"],
            "Java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "C#": ["*.csproj", "*.sln"],
        }

        detected_languages = []
        for language, indicator_files in project_files.items():
            for indicator in indicator_files:
                if indicator.startswith("*"):
                    # Glob pattern
                    if list(self.project_path.glob(indicator)):
                        detected_languages.append(language)
                        break
                else:
                    if (self.project_path / indicator).exists():
                        detected_languages.append(language)
                        break

        self.conventions["languages"] = detected_languages
        if detected_languages:
            # Primary language is the first detected
            self.conventions["project_type"] = detected_languages[0]

    def detect_package_manager(self) -> None:
        """Detect the package manager used by the project."""
        # Python package managers
        if (self.project_path / "uv.lock").exists():
            self.conventions["package_manager"] = "uv"
        elif (self.project_path / "poetry.lock").exists():
            self.conventions["package_manager"] = "poetry"
        elif (self.project_path / "Pipfile.lock").exists():
            self.conventions["package_manager"] = "pipenv"
        elif (self.project_path / "requirements.txt").exists():
            self.conventions["package_manager"] = "pip"

        # JavaScript/TypeScript package managers
        elif (self.project_path / "pnpm-lock.yaml").exists():
            self.conventions["package_manager"] = "pnpm"
        elif (self.project_path / "yarn.lock").exists():
            self.conventions["package_manager"] = "yarn"
        elif (self.project_path / "package-lock.json").exists():
            self.conventions["package_manager"] = "npm"
        elif (self.project_path / "bun.lockb").exists():
            self.conventions["package_manager"] = "bun"

        # Rust package manager
        elif (self.project_path / "Cargo.lock").exists():
            self.conventions["package_manager"] = "cargo"

        # Go package manager
        elif (self.project_path / "go.sum").exists():
            self.conventions["package_manager"] = "go"

    def detect_test_framework(self) -> None:
        """Detect the test framework and test command."""
        project_type = self.conventions["project_type"]

        # Python test frameworks
        if project_type == "Python":
            if (self.project_path / "pytest.ini").exists() or self._has_dependency("pytest"):
                self.conventions["test_framework"] = "pytest"
                self.conventions["test_command"] = self._get_test_command("pytest")
            elif self._has_dependency("unittest"):
                self.conventions["test_framework"] = "unittest"
                self.conventions["test_command"] = "python -m unittest"

        # JavaScript/TypeScript test frameworks
        elif project_type in ["JavaScript", "TypeScript"]:
            if self._has_dependency("jest"):
                self.conventions["test_framework"] = "Jest"
                self.conventions["test_command"] = self._get_npm_script("test", default="npm test")
            elif self._has_dependency("vitest"):
                self.conventions["test_framework"] = "Vitest"
                self.conventions["test_command"] = self._get_npm_script(
                    "test", default="npm run test"
                )
            elif self._has_dependency("mocha"):
                self.conventions["test_framework"] = "Mocha"
                self.conventions["test_command"] = self._get_npm_script(
                    "test", default="npm test"
                )

        # Rust test framework
        elif project_type == "Rust":
            self.conventions["test_framework"] = "cargo test"
            self.conventions["test_command"] = "cargo test"

        # Go test framework
        elif project_type == "Go":
            self.conventions["test_framework"] = "go test"
            self.conventions["test_command"] = "go test ./..."

    def extract_readme_conventions(self) -> None:
        """Extract conventions mentioned in README files."""
        readme_files = ["README.md", "README.rst", "README.txt", "README"]

        for readme_name in readme_files:
            readme_path = self.project_path / readme_name
            if not readme_path.exists():
                continue

            with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Extract common conventions
            conventions = []

            # Look for "Conventions", "Code Style", "Development" sections
            convention_patterns = [
                r"##\s*(?:Conventions|Code Style|Coding Standards|Development Guidelines)",
                r"###\s*(?:Conventions|Code Style|Coding Standards|Development Guidelines)",
            ]

            for pattern in convention_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Extract the section content (until next header or end)
                    start_pos = match.end()
                    section_content = content[start_pos:]

                    # Find next header
                    next_header = re.search(r"\n##", section_content)
                    if next_header:
                        section_content = section_content[: next_header.start()]

                    # Extract bullet points or numbered lists
                    lines = section_content.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
                            # Clean up the line
                            clean_line = re.sub(r"^[-*•]\s*", "", line)
                            clean_line = re.sub(r"^\d+\.\s*", "", clean_line)
                            if clean_line:
                                conventions.append(clean_line)

            # Look for common patterns in README
            patterns = {
                "Use .* instead of .*": "tool_preference",
                "Always .*": "best_practice",
                "Never .*": "anti_pattern",
                "Prefer .* over .*": "preference",
            }

            for pattern_regex, category in patterns.items():
                matches = re.finditer(pattern_regex, content, re.IGNORECASE)
                for match in matches:
                    conventions.append({"text": match.group(0), "category": category})

            if conventions:
                self.conventions["conventions"] = conventions

    def detect_common_patterns(self) -> None:
        """Detect common coding patterns from project structure."""
        patterns = []

        # Check for common directory structures
        if (self.project_path / "tests").exists():
            patterns.append("Tests in tests/ directory")
        elif (self.project_path / "test").exists():
            patterns.append("Tests in test/ directory")

        if (self.project_path / "src").exists():
            patterns.append("Source code in src/ directory")

        if (self.project_path / "docs").exists():
            patterns.append("Documentation in docs/ directory")

        # Check for CI/CD
        if (self.project_path / ".github" / "workflows").exists():
            patterns.append("GitHub Actions CI/CD")
        elif (self.project_path / ".gitlab-ci.yml").exists():
            patterns.append("GitLab CI/CD")
        elif (self.project_path / ".circleci").exists():
            patterns.append("CircleCI CI/CD")

        # Check for Docker
        if (self.project_path / "Dockerfile").exists():
            patterns.append("Dockerized application")
        if (self.project_path / "docker-compose.yml").exists():
            patterns.append("Docker Compose for local development")

        # Check for Git hooks
        if (self.project_path / ".pre-commit-config.yaml").exists():
            patterns.append("Pre-commit hooks configured")

        if patterns:
            if "patterns" not in self.conventions:
                self.conventions["patterns"] = []
            self.conventions["patterns"].extend(patterns)

    def _has_dependency(self, dep_name: str) -> bool:
        """Check if a dependency exists in the project."""
        # Check Python dependencies
        pyproject_path = self.project_path / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            if dep_name in content:
                return True

        # Check package.json
        package_json_path = self.project_path / "package.json"
        if package_json_path.exists():
            with open(package_json_path, "r") as f:
                try:
                    package_data = json.load(f)
                    deps = package_data.get("dependencies", {})
                    dev_deps = package_data.get("devDependencies", {})
                    if dep_name in deps or dep_name in dev_deps:
                        return True
                except json.JSONDecodeError:
                    pass

        return False

    def _get_test_command(self, framework: str) -> str:
        """Get the test command based on package manager and framework."""
        pkg_mgr = self.conventions.get("package_manager")

        if pkg_mgr == "uv":
            return f"uv run {framework}"
        elif pkg_mgr == "poetry":
            return f"poetry run {framework}"
        elif pkg_mgr == "pipenv":
            return f"pipenv run {framework}"
        else:
            return framework

    def _get_npm_script(self, script_name: str, default: str) -> str:
        """Get npm script command or default."""
        package_json_path = self.project_path / "package.json"
        if not package_json_path.exists():
            return default

        with open(package_json_path, "r") as f:
            try:
                package_data = json.load(f)
                scripts = package_data.get("scripts", {})
                if script_name in scripts:
                    pkg_mgr = self.conventions.get("package_manager", "npm")
                    if pkg_mgr == "npm":
                        return f"npm run {script_name}"
                    else:
                        return f"{pkg_mgr} {script_name}"
            except json.JSONDecodeError:
                pass

        return default

    def get_conventions(self) -> Dict[str, Any]:
        """Get the extracted conventions."""
        return self.conventions
