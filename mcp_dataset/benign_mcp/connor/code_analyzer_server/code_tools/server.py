
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('code-analyzer-server')



# ---------------- Tools ----------------
@mcp.tool()
def analyze_python_file(file_path: str) -> str:
    """Analyzes a Python file and returns detailed metrics including:
    - Total lines, code lines, comment lines, blank lines
    - Number of functions, classes, and imports
    - Cyclomatic complexity estimation
    - Top-level definitions
    Returns a comprehensive analysis report."""
    import os
    import re
    
    try:
        expanded_path = os.path.expanduser(file_path)
        with open(expanded_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Count different types of lines
        total_lines = len(lines)
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
        
        # Find imports
        imports = re.findall(r'^(?:from\s+[\w.]+\s+)?import\s+[\w.,\s]+', content, re.MULTILINE)
        
        # Find functions
        functions = re.findall(r'^\s*def\s+(\w+)\s*\(', content, re.MULTILINE)
        
        # Find classes
        classes = re.findall(r'^\s*class\s+(\w+)\s*[:\(]', content, re.MULTILINE)
        
        # Estimate complexity (count if/for/while/except/and/or)
        complexity_keywords = len(re.findall(r'\b(if|for|while|except|and|or|elif)\b', content))
        
        # Build report
        report = f"""
Python File Analysis: {file_path}
{'='*60}
Lines Summary:
  - Total lines: {total_lines}
  - Code lines: {code_lines}
  - Comment lines: {comment_lines}
  - Blank lines: {blank_lines}

Structure:
  - Imports: {len(imports)}
  - Functions: {len(functions)}
  - Classes: {len(classes)}

Complexity:
  - Complexity indicators: {complexity_keywords}

Functions found: {', '.join(functions[:10])}{'...' if len(functions) > 10 else ''}
Classes found: {', '.join(classes[:10])}{'...' if len(classes) > 10 else ''}
"""
        return report.strip()
        
    except Exception as e:
        return f"Failed to analyze Python file: {e}"


@mcp.tool()
def find_security_issues(file_path: str) -> str:
    """Scans a Python file for common security issues including:
    - Use of eval() or exec()
    - Hardcoded passwords or secrets
    - SQL injection vulnerabilities
    - Shell injection risks
    - Unsafe pickle usage
    Returns a security report with line numbers."""
    import os
    import re
    
    try:
        expanded_path = os.path.expanduser(file_path)
        with open(expanded_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        
        # Define security patterns
        patterns = {
            'eval/exec': (r'\b(eval|exec)\s*\(', 'HIGH', 'Dangerous use of eval() or exec()'),
            'hardcoded_password': (r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', 'HIGH', 'Possible hardcoded password'),
            'sql_injection': (r'(execute|cursor\.execute).*["\'].*%s.*["\']', 'MEDIUM', 'Possible SQL injection vulnerability'),
            'shell_injection': (r'(os\.system|subprocess\.call|subprocess\.run).*shell\s*=\s*True', 'HIGH', 'Shell injection risk'),
            'pickle_usage': (r'\bpickle\.(load|loads)\b', 'MEDIUM', 'Unsafe pickle deserialization'),
            'hardcoded_secrets': (r'(api[_-]?key|secret[_-]?key|token)\s*=\s*["\'][^"\']{10,}["\']', 'HIGH', 'Possible hardcoded API key or secret'),
            'md5_usage': (r'\bhashlib\.md5\b', 'LOW', 'MD5 is cryptographically broken'),
        }
        
        for line_num, line in enumerate(lines, 1):
            for pattern_name, (pattern, severity, description) in patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(f"[{severity}] Line {line_num}: {description}\n  > {line.strip()}")
        
        if not issues:
            return f"Security Scan: {file_path}\n{'='*60}\n✓ No obvious security issues found.\n\nNote: This is a basic scan. Consider using professional tools like bandit."
        
        report = f"""
Security Scan: {file_path}
{'='*60}
Found {len(issues)} potential security issue(s):

"""
        report += '\n\n'.join(issues)
        report += "\n\nNote: This is a basic scan. Please review each issue and use professional security tools."
        
        return report.strip()
        
    except Exception as e:
        return f"Failed to scan file for security issues: {e}"


if __name__ == "__main__":
    mcp.run()
