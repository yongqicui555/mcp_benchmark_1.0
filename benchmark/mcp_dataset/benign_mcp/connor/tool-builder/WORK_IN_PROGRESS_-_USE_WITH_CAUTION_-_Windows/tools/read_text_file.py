def read_text_file(file_path):
    """
    Reads and displays the contents of a text file.
    
    Args:
        file_path (str): Path to the text file to read
        
    Returns:
        str: The content of the file, or an error message if file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except PermissionError:
        return f"Error: Permission denied for file '{file_path}'."
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
                return content + "\n\nNote: File read with latin-1 encoding (UTF-8 failed)."
        except:
            return f"Error: Could not decode file '{file_path}'. It may not be a text file."
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"