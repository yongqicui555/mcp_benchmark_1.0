
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('git-helper-server')



# ---------------- Tools ----------------
@mcp.tool()
def analyze_git_repo(repo_path: str, max_commits: int = 100) -> str:
    """Analyzes a Git repository and provides comprehensive statistics:
    - Total commits, authors, branches
    - Commit frequency analysis
    - Top contributors with commit counts
    - File change statistics
    - Recent activity summary
    - Repository age and activity period
    
    Args:
        repo_path: Path to the git repository
        max_commits: Maximum number of recent commits to analyze (default: 100)
    
    Returns a detailed repository analysis report."""
    import os
    import subprocess
    from datetime import datetime
    from collections import Counter, defaultdict
    
    try:
        expanded_path = os.path.expanduser(repo_path)
        
        # Check if it's a git repo
        git_check = subprocess.run(
            ['git', '-C', expanded_path, 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True
        )
        
        if git_check.returncode != 0:
            return f"Error: {repo_path} is not a Git repository"
        
        report = f"""
Git Repository Analysis: {repo_path}
{'='*70}
"""
        
        # Get branch count
        branches = subprocess.run(
            ['git', '-C', expanded_path, 'branch', '-a'],
            capture_output=True,
            text=True
        ).stdout.strip().split('\n')
        branch_count = len([b for b in branches if b.strip()])
        
        # Get total commit count
        total_commits = subprocess.run(
            ['git', '-C', expanded_path, 'rev-list', '--count', 'HEAD'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        # Get commit log
        log_output = subprocess.run(
            ['git', '-C', expanded_path, 'log', f'-{max_commits}', 
             '--pretty=format:%H|%an|%ae|%ad|%s', '--date=iso'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        commits = []
        for line in log_output.split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': '|'.join(parts[4:])
                    })
        
        # Analyze commits
        authors = Counter([c['author'] for c in commits])
        emails = Counter([c['email'] for c in commits])
        
        # Get date range
        if commits:
            first_date = datetime.fromisoformat(commits[-1]['date'].split()[0])
            last_date = datetime.fromisoformat(commits[0]['date'].split()[0])
            days_active = (last_date - first_date).days
        else:
            days_active = 0
        
        # Basic stats
        report += f"\nRepository Overview:"
        report += f"\n  Total commits: {total_commits}"
        report += f"\n  Branches: {branch_count}"
        report += f"\n  Unique authors: {len(authors)}"
        report += f"\n  Days active: {days_active}"
        if days_active > 0:
            report += f"\n  Avg commits/day: {int(total_commits) / days_active:.2f}"
        
        # Top contributors
        report += f"\n\nTop Contributors (from last {len(commits)} commits):"
        for author, count in authors.most_common(10):
            percentage = (count / len(commits)) * 100
            report += f"\n  {author}: {count} commits ({percentage:.1f}%)"
        
        # Recent activity
        report += f"\n\nRecent Commits:"
        for commit in commits[:5]:
            short_hash = commit['hash'][:7]
            message = commit['message'][:60] + ('...' if len(commit['message']) > 60 else '')
            date = commit['date'].split()[0]
            report += f"\n  [{short_hash}] {date} - {message}"
            report += f"\n      by {commit['author']}"
        
        # File statistics
        try:
            file_stats = subprocess.run(
                ['git', '-C', expanded_path, 'ls-files'],
                capture_output=True,
                text=True
            ).stdout.strip().split('\n')
            
            file_extensions = Counter()
            for f in file_stats:
                if '.' in f:
                    ext = f.rsplit('.', 1)[1]
                    file_extensions[ext] += 1
            
            report += f"\n\nFile Statistics:"
            report += f"\n  Total files tracked: {len(file_stats)}"
            report += f"\n  File types:"
            for ext, count in file_extensions.most_common(10):
                report += f"\n    .{ext}: {count}"
        except Exception:
            pass
        
        # Get current branch
        try:
            current_branch = subprocess.run(
                ['git', '-C', expanded_path, 'branch', '--show-current'],
                capture_output=True,
                text=True
            ).stdout.strip()
            report += f"\n\nCurrent Branch: {current_branch}"
        except Exception:
            pass
        
        return report.strip()
        
    except subprocess.CalledProcessError as e:
        return f"Git command failed: {e}"
    except Exception as e:
        return f"Failed to analyze Git repository: {e}"


@mcp.tool()
def find_large_files(repo_path: str, min_size_kb: int = 1000, top_n: int = 20) -> str:
    """Finds large files in a Git repository history, useful for identifying files
    that should be removed or moved to Git LFS.
    
    Searches through the entire Git history to find:
    - Largest files ever committed
    - File sizes and paths
    - Current status (still present or deleted)
    - Commit where file was introduced
    
    Args:
        repo_path: Path to the git repository
        min_size_kb: Minimum file size in KB to report (default: 1000 KB = 1 MB)
        top_n: Number of largest files to return (default: 20)
    
    Returns a report of large files found in the repository."""
    import os
    import subprocess
    
    try:
        expanded_path = os.path.expanduser(repo_path)
        
        # Check if it's a git repo
        git_check = subprocess.run(
            ['git', '-C', expanded_path, 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True
        )
        
        if git_check.returncode != 0:
            return f"Error: {repo_path} is not a Git repository"
        
        report = f"""
Large Files Analysis: {repo_path}
{'='*70}
Searching for files larger than {min_size_kb} KB...

"""
        
        # Find all objects and their sizes
        # Using git rev-list to get all objects
        result = subprocess.run(
            ['git', '-C', expanded_path, 'rev-list', '--objects', '--all'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        objects = []
        for line in result.stdout.strip().split('\n'):
            if line and ' ' in line:
                obj_hash, path = line.split(' ', 1)
                objects.append((obj_hash, path))
        
        # Get sizes for each object
        large_files = []
        for obj_hash, path in objects[:5000]:  # Limit to avoid too long execution
            try:
                size_result = subprocess.run(
                    ['git', '-C', expanded_path, 'cat-file', '-s', obj_hash],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                if size_result.returncode == 0:
                    size_bytes = int(size_result.stdout.strip())
                    size_kb = size_bytes / 1024
                    
                    if size_kb >= min_size_kb:
                        # Check if file still exists
                        exists = os.path.exists(os.path.join(expanded_path, path))
                        large_files.append({
                            'path': path,
                            'size_kb': size_kb,
                            'size_mb': size_kb / 1024,
                            'exists': exists
                        })
            except Exception:
                continue
        
        # Sort by size and get top N
        large_files.sort(key=lambda x: x['size_kb'], reverse=True)
        large_files = large_files[:top_n]
        
        if not large_files:
            report += f"✓ No files larger than {min_size_kb} KB found.\n"
            return report.strip()
        
        report += f"Found {len(large_files)} large file(s):\n"
        
        total_size_mb = sum(f['size_mb'] for f in large_files)
        report += f"\nTotal size of listed files: {total_size_mb:.2f} MB\n"
        report += f"\n{'='*70}\n"
        
        for i, file_info in enumerate(large_files, 1):
            status = "EXISTS" if file_info['exists'] else "DELETED"
            report += f"\n{i}. [{status}] {file_info['path']}"
            report += f"\n   Size: {file_info['size_mb']:.2f} MB ({file_info['size_kb']:.0f} KB)"
            
            # Try to find when it was added
            try:
                log_result = subprocess.run(
                    ['git', '-C', expanded_path, 'log', '--diff-filter=A', 
                     '--pretty=format:%H|%an|%ad', '--date=short', '--', file_info['path']],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if log_result.stdout.strip():
                    first_line = log_result.stdout.strip().split('\n')[0]
                    if '|' in first_line:
                        commit_hash, author, date = first_line.split('|')
                        report += f"\n   Added: {date} by {author} (commit: {commit_hash[:7]})"
            except Exception:
                pass
            
            report += "\n"
        
        report += f"\n{'='*70}"
        report += f"\nRecommendation: Consider using Git LFS for files larger than {min_size_kb} KB"
        report += f"\nTo remove a file from history: git filter-branch or git filter-repo"
        
        return report.strip()
        
    except subprocess.TimeoutExpired:
        return "Error: Operation timed out. Repository might be too large."
    except subprocess.CalledProcessError as e:
        return f"Git command failed: {e}"
    except Exception as e:
        return f"Failed to find large files: {e}"


if __name__ == "__main__":
    mcp.run()
