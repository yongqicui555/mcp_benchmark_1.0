
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('data-processor-server')



# ---------------- Tools ----------------
@mcp.tool()
def csv_statistics(file_path: str, delimiter: str = ',') -> str:
    """Reads a CSV file and calculates comprehensive statistics including:
    - Row and column counts
    - Data types for each column
    - Missing values analysis
    - Numeric column statistics (min, max, mean, median)
    - Categorical column frequency
    Returns a detailed statistical report."""
    import os
    import csv
    from collections import Counter, defaultdict
    
    try:
        expanded_path = os.path.expanduser(file_path)
        
        with open(expanded_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader)
            rows = list(reader)
        
        if not rows:
            return "CSV file is empty (no data rows)"
        
        num_rows = len(rows)
        num_cols = len(headers)
        
        # Analyze each column
        column_data = defaultdict(list)
        for row in rows:
            for i, value in enumerate(row):
                if i < len(headers):
                    column_data[headers[i]].append(value)
        
        report = f"""
CSV Statistics: {file_path}
{'='*70}
Dimensions:
  - Rows: {num_rows}
  - Columns: {num_cols}

Column Analysis:
"""
        
        for header in headers:
            values = column_data[header]
            non_empty = [v for v in values if v.strip()]
            missing = num_rows - len(non_empty)
            
            report += f"\n[{header}]"
            report += f"\n  Missing values: {missing} ({missing/num_rows*100:.1f}%)"
            
            # Try to detect if numeric
            numeric_values = []
            for v in non_empty:
                try:
                    numeric_values.append(float(v))
                except ValueError:
                    break
            
            if len(numeric_values) == len(non_empty) and numeric_values:
                # Numeric column
                numeric_values.sort()
                mean_val = sum(numeric_values) / len(numeric_values)
                median_val = numeric_values[len(numeric_values)//2]
                
                report += f"\n  Type: Numeric"
                report += f"\n  Min: {min(numeric_values):.2f}"
                report += f"\n  Max: {max(numeric_values):.2f}"
                report += f"\n  Mean: {mean_val:.2f}"
                report += f"\n  Median: {median_val:.2f}"
            else:
                # Categorical column
                counter = Counter(non_empty)
                unique_count = len(counter)
                most_common = counter.most_common(5)
                
                report += f"\n  Type: Categorical"
                report += f"\n  Unique values: {unique_count}"
                report += f"\n  Top values: {', '.join([f'{v}({c})' for v, c in most_common[:3]])}"
        
        return report.strip()
        
    except Exception as e:
        return f"Failed to analyze CSV file: {e}"


@mcp.tool()
def merge_json_files(file_paths: str, output_path: str, merge_strategy: str = 'list') -> str:
    """Merges multiple JSON files into a single file.
    
    Args:
        file_paths: Comma-separated list of JSON file paths to merge
        output_path: Path where the merged JSON will be saved
        merge_strategy: How to merge the files:
            - 'list': Create a list of all JSON objects
            - 'merge': Merge dictionaries (later files override earlier ones)
            - 'array': Combine all arrays into one
    
    Returns a summary of the merge operation."""
    import os
    import json
    
    try:
        paths = [p.strip() for p in file_paths.split(',')]
        expanded_paths = [os.path.expanduser(p) for p in paths]
        
        # Read all JSON files
        json_data = []
        for path in expanded_paths:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                json_data.append((path, data))
        
        # Merge based on strategy
        if merge_strategy == 'list':
            merged = [{'source': os.path.basename(path), 'data': data} for path, data in json_data]
        
        elif merge_strategy == 'merge':
            merged = {}
            for path, data in json_data:
                if isinstance(data, dict):
                    merged.update(data)
                else:
                    return f"Error: Cannot merge non-dictionary data in 'merge' mode (file: {path})"
        
        elif merge_strategy == 'array':
            merged = []
            for path, data in json_data:
                if isinstance(data, list):
                    merged.extend(data)
                else:
                    merged.append(data)
        
        else:
            return f"Invalid merge_strategy: {merge_strategy}. Use 'list', 'merge', or 'array'."
        
        # Write merged data
        output_expanded = os.path.expanduser(output_path)
        with open(output_expanded, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        
        # Generate summary
        total_size = sum(os.path.getsize(p) for p in expanded_paths)
        output_size = os.path.getsize(output_expanded)
        
        report = f"""
JSON Merge Complete
{'='*60}
Strategy: {merge_strategy}
Files merged: {len(paths)}
Input files:
"""
        for i, path in enumerate(paths, 1):
            report += f"\n  {i}. {path}"
        
        report += f"\n\nOutput: {output_path}"
        report += f"\nTotal input size: {total_size} bytes"
        report += f"\nOutput size: {output_size} bytes"
        
        if merge_strategy == 'list':
            report += f"\nMerged items: {len(merged)}"
        elif merge_strategy == 'merge':
            report += f"\nMerged keys: {len(merged)}"
        elif merge_strategy == 'array':
            report += f"\nTotal elements: {len(merged)}"
        
        return report.strip()
        
    except Exception as e:
        return f"Failed to merge JSON files: {e}"


if __name__ == "__main__":
    mcp.run()
