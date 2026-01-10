"""
Test Markdown to HTML conversion

This script demonstrates how Markdown syntax is converted to HTML
when Telegram's Markdown parser fails.
"""

import re
import html


def markdown_to_html(text: str) -> str:
    """
    Convert common Markdown syntax to HTML tags for Telegram HTML parse mode.
    """
    # First, escape HTML special characters to avoid conflicts
    text = html.escape(text, quote=False)
    
    # Convert headings (###, ##, #) to bold
    text = re.sub(r'^#{1,6}\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    
    # Convert **bold** (must be before * for italic)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # Convert __underline__
    text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)
    
    # Convert *italic* (single asterisk)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    
    # Convert _italic_ (single underscore) 
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<i>\1</i>', text)
    
    # Convert `code`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    
    # Convert [link](url) - extract URL first since it's already escaped
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        # Unescape the URL since we escaped it earlier
        url = url.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return f'<a href="{url}">{link_text}</a>'
    
    text = re.sub(r'\[(.+?)\]\((.+?)\)', replace_link, text)
    
    # Convert bullet points (-, *, +) to • 
    text = re.sub(r'^[\-\*\+]\s+', '• ', text, flags=re.MULTILINE)
    
    # Convert numbered lists (1., 2., etc.)
    text = re.sub(r'^\d+\.\s+', lambda m: f'{m.group(0)} ', text, flags=re.MULTILINE)
    
    return text


def test_conversion():
    """Test the Markdown to HTML conversion"""
    
    print("=" * 70)
    print("Markdown to HTML Conversion Test")
    print("=" * 70)
    print()
    
    # Test cases
    test_cases = [
        ("**Bold text**", "Bold formatting"),
        ("*Italic text*", "Italic formatting"),
        ("__Underlined text__", "Underline formatting"),
        ("### Heading", "Heading formatting"),
        ("`code snippet`", "Code formatting"),
        ("**Bold** and *italic* together", "Mixed formatting"),
        ("- Item 1\n- Item 2\n- Item 3", "Bullet list"),
        ("1. First\n2. Second\n3. Third", "Numbered list"),
        ("[Link text](https://example.com)", "Link"),
    ]
    
    for markdown, description in test_cases:
        html_output = markdown_to_html(markdown)
        print(f"📝 {description}:")
        print(f"   Input:  {markdown!r}")
        print(f"   Output: {html_output!r}")
        print()
    
    # Test with a complex example (like AI response)
    print("=" * 70)
    print("Complex Example (AI Response)")
    print("=" * 70)
    print()
    
    ai_response = """This diagram shows a **microservices architecture** with the following components:

### Key Components:
1. **API Gateway** - Routes requests to services
2. **Service A** - Handles user authentication
3. **Service B** - Processes data

The architecture uses *asynchronous communication* between services via a **message queue**.

Key benefits:
- Scalability
- Fault isolation
- Independent deployment

For more details, see the [documentation](https://example.com/docs)."""
    
    print("Input (Markdown):")
    print("-" * 70)
    print(ai_response)
    print("-" * 70)
    print()
    
    html_output = markdown_to_html(ai_response)
    
    print("Output (HTML):")
    print("-" * 70)
    print(html_output)
    print("-" * 70)
    print()
    
    print("✅ Conversion complete!")
    print()
    print("💡 When Telegram's Markdown parser fails, this HTML version")
    print("   will be sent instead, preserving all formatting!")


if __name__ == "__main__":
    test_conversion()
