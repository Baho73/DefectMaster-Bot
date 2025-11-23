"""
Markdown utilities for safe text formatting in Telegram
"""
import re


def escape_markdown(text: str) -> str:
    """
    Escape special Markdown characters in user input

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for Markdown formatting
    """
    if not text:
        return text

    # Characters that need escaping in Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in special_chars:
        text = text.replace(char, f'\\{char}')

    return text


def safe_markdown_format(text: str, user_data: dict) -> str:
    """
    Format text with Markdown, escaping user-provided data

    Args:
        text: Format string with {key} placeholders
        user_data: Dictionary with user-provided values to escape

    Returns:
        Formatted text with escaped user data
    """
    # Escape all user-provided values
    escaped_data = {k: escape_markdown(str(v)) for k, v in user_data.items()}

    return text.format(**escaped_data)
