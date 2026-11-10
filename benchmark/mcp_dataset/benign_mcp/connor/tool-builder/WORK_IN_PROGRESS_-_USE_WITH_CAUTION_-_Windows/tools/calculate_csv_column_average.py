import csv
import statistics
from typing import Union

def calculate_csv_column_average(file_path: str, column_name: str) -> dict:
    """
    Reads a CSV file and calculates the average of a specified column.
    
    Args:
        file_path (str): Path to the CSV file
        column_name (str): Name of the column to calculate average for
        
    Returns:
        dict: Dictionary containing the average value and statistics
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        KeyError: If the specified column doesn't exist in the CSV
        ValueError: If the column contains non-numeric values
    """
    
    try:
        # Read the CSV file
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            # Try to detect the delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            # Common delimiters to try
            delimiters = [',', ';', '\t', '|']
            detected_delimiter = ','
            
            for delimiter in delimiters:
                if delimiter in sample:
                    detected_delimiter = delimiter
                    break
            
            # Read CSV with detected delimiter
            reader = csv.DictReader(csvfile, delimiter=detected_delimiter)
            
            # Check if column exists
            if column_name not in reader.fieldnames:
                available_columns = ", ".join(reader.fieldnames) if reader.fieldnames else "No columns found"
                raise KeyError(f"Column '{column_name}' not found in CSV. Available columns: {available_columns}")
            
            # Extract column values
            column_values = []
            row_count = 0
            
            for row in reader:
                row_count += 1
                value = row[column_name]
                
                # Skip empty values
                if value is None or str(value).strip() == '':
                    continue
                
                # Try to convert to float
                try:
                    numeric_value = float(value)
                    column_values.append(numeric_value)
                except ValueError:
                    raise ValueError(
                        f"Non-numeric value '{value}' found in column '{column_name}' at row {row_count}. "
                        f"All values in the column must be numeric to calculate average."
                    )
            
            # Check if we have any values
            if not column_values:
                return {
                    "success": False,
                    "error": f"No numeric values found in column '{column_name}'",
                    "file_path": file_path,
                    "column_name": column_name,
                    "total_rows": row_count,
                    "numeric_rows": 0
                }
            
            # Calculate statistics
            average = statistics.mean(column_values)
            median = statistics.median(column_values)
            min_value = min(column_values)
            max_value = max(column_values)
            
            # Calculate standard deviation if we have at least 2 values
            if len(column_values) >= 2:
                stdev = statistics.stdev(column_values)
            else:
                stdev = 0
            
            return {
                "success": True,
                "file_path": file_path,
                "column_name": column_name,
                "average": average,
                "median": median,
                "min": min_value,
                "max": max_value,
                "standard_deviation": stdev,
                "count": len(column_values),
                "total_rows": row_count,
                "missing_values": row_count - len(column_values),
                "values": column_values  # Include the actual values for reference
            }
            
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "file_path": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "column_name": column_name
        }