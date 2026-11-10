import mimetypes
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os
import json
from tika import parser
from langdetect import detect
from deep_translator import GoogleTranslator
import whisper

# Initialize FastMCP server
mcp = FastMCP("file_summarizer")

def read_any_file(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type and mime_type.startswith("audio"):
        return transcribe_audio(file_path)
    elif mime_type and mime_type.startswith("video"):
        return transcribe_audio(file_path)
    else:
        try:
            parsed = parser.from_file(file_path)
            text = parsed.get("content", "")
            if text:
                return text.strip()
            else:
                return "No text content found in the file."
        except Exception as e:
            return f"Error reading file: {str(e)}"

def summarize_content(content: str) -> str:
    """Summarize the input text with a line and character limit."""
    if not content.strip():
        return "No content to summarize."

    #detect language
    language = detect_language_fn(content)
    if language != "en":
        content = translate_text_fn(content)

    lines = content.strip().splitlines()
    summary = "\n".join(lines[:])   

    '''if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."'''

    return summary

'''def summarize_text_with_hf(text: str) -> str:
    if not text.strip():
        return "No content to summarize."

    try:
        # Hugging Face summarization (max 1024 input tokens)
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        summaries = []
        for chunk in chunks:
            summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        return "\n".join(summaries)
    except Exception as e:
        return f"Error summarizing text: {str(e)}"'''

def detect_language_fn(text: str) -> str:
    """Detect the language of the input text."""
    try:
        return detect(text)
    except Exception as e:
        return f"Error detecting language: {str(e)}"

def translate_text_fn(text: str) -> str:
    """Translate the input text to English."""
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        return f"Error translating text: {str(e)}"
    
# Load Whisper model once (can load 'base', 'small', 'medium', 'large')
model = whisper.load_model("base")

def transcribe_audio(file_path: str) -> str:
    """Convert the audio file or audio of video file into text."""
    try:
        result = model.transcribe(file_path)
        return result
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

@mcp.tool()
async def read_file(file_path: str) -> str:
    """Read the raw content of a text file.

    Args:
        file_path: Path to the file.
    """
    if not os.path.exists(file_path):
        return "Error: File not found."
    
    # use tika to read the file
    return read_any_file(file_path)

    '''try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"'''


@mcp.tool()
async def summarize_file(file_path: str) -> str:
    """Summarize the content of a file.

    Args:
        file_path: Path to the file.
    """
    if not os.path.exists(file_path):
        return "Error: File not found."

    content = read_any_file(file_path)
    if content == "No text content found in the file." or content == "Error reading file: No text content found in the file.":
        return content
    
    '''try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"'''

    return summarize_content(content)


@mcp.tool()
async def summarize_text(text: str) -> str:
    """Summarize raw input text.

    Args:
        text: The full text to summarize.
    
    return summarize_content(text)"""
    
    #LLM summarization
    return summarize_content(text)

@mcp.tool()
async def translate_text(text: str) -> str:
    """Translate the input text to English."""
    return translate_text_fn(text)

@mcp.tool()
async def detect_language(text: str) -> str:
    """Detect the language of the input text."""
    return detect_language_fn(text)

@mcp.tool()
async def transcribe_file(file_path: str) -> str:
    """transcribe the audio or video file."""
    return transcribe_audio(file_path)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()