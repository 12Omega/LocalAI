"""Property-based tests for HTML content extraction.

This module tests Property 1: HTML Content Extraction
**Validates: Requirements 5.3**

The property ensures that for any valid HTML document, extracting text and
code examples produces output where:
- All text content from the document body is present in the extracted text
- All code blocks (identified by <code> or <pre> tags) are captured
- Code formatting is preserved (whitespace, indentation, line breaks)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from bs4 import BeautifulSoup

from src.web.web_research import WebResearchModule, CodeExample


# Strategy for generating HTML text content
# Exclude control characters, HTML special chars, and & for valid HTML
html_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'),
        blacklist_characters='<>&"\'',  # Exclude HTML special chars
        min_codepoint=32,  # Start from space character
        max_codepoint=126  # ASCII printable range
    ),
    min_size=1,
    max_size=500
)

# Strategy for generating code content with formatting
# Avoid HTML special characters in code
code_content_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'),
        whitelist_characters='_{}[]();,.\n\t ',
        blacklist_characters='<>&"\'#'  # Exclude HTML special chars and # which causes encoding issues
    ),
    min_size=10,
    max_size=1000
)

# Strategy for generating programming language names
language_strategy = st.sampled_from([
    'python', 'javascript', 'typescript', 'java', 'cpp',
    'rust', 'go', 'sql', 'bash', 'html', 'css', 'json', 'yaml'
])


@st.composite
def html_with_text(draw):
    """Generate HTML document with text content in body."""
    texts = draw(st.lists(html_text_strategy, min_size=1, max_size=10))
    
    # Create HTML with text in various tags
    body_content = []
    for text in texts:
        tag = draw(st.sampled_from(['p', 'div', 'span', 'h1', 'h2', 'li', 'td']))
        body_content.append(f"<{tag}>{text}</{tag}>")
    
    html = f"<html><body>{''.join(body_content)}</body></html>"
    return html, texts


@st.composite
def html_with_code_blocks(draw):
    """Generate HTML document with code blocks in <pre> and <code> tags."""
    num_blocks = draw(st.integers(min_value=1, max_value=5))
    code_blocks = []
    
    html_parts = ["<html><body>"]
    
    for _ in range(num_blocks):
        code_text = draw(code_content_strategy)
        assume(len(code_text.strip()) > 10)  # Ensure substantial code
        
        # Choose between <pre><code>, <pre>, or standalone <code>
        block_type = draw(st.sampled_from(['pre_code', 'pre', 'code']))
        language = draw(st.one_of(st.none(), language_strategy))
        
        if block_type == 'pre_code':
            if language:
                html_parts.append(f'<pre><code class="language-{language}">{code_text}</code></pre>')
            else:
                html_parts.append(f'<pre><code>{code_text}</code></pre>')
        elif block_type == 'pre':
            if language:
                html_parts.append(f'<pre class="language-{language}">{code_text}</pre>')
            else:
                html_parts.append(f'<pre>{code_text}</pre>')
        else:  # standalone code
            # Make it multi-line to ensure it's captured
            code_text_multiline = code_text + '\n' + draw(code_content_strategy)
            if language:
                html_parts.append(f'<code class="language-{language}">{code_text_multiline}</code>')
            else:
                html_parts.append(f'<code>{code_text_multiline}</code>')
            code_text = code_text_multiline
        
        code_blocks.append((code_text, language))
    
    html_parts.append("</body></html>")
    html = ''.join(html_parts)
    
    return html, code_blocks


@st.composite
def html_with_nested_structure(draw):
    """Generate HTML with nested tags and mixed content."""
    # Text content - only include text that's in the main content area
    text1 = draw(html_text_strategy)  # Will be in header (filtered out)
    text2 = draw(html_text_strategy)  # Will be in main
    text3 = draw(html_text_strategy)  # Will be in main
    
    # Code content
    code1 = draw(code_content_strategy)
    assume(len(code1.strip()) > 10)
    
    # Create nested structure
    html = f"""
    <html>
        <head><title>Test Page</title></head>
        <body>
            <header><h1>{text1}</h1></header>
            <main>
                <div>
                    <p>{text2}</p>
                    <pre><code>{code1}</code></pre>
                </div>
                <article>
                    <p>{text3}</p>
                </article>
            </main>
        </body>
    </html>
    """
    
    # Only return texts that are in the main content area (text2, text3)
    # text1 is in header and will be filtered out
    return html, [text2, text3], [code1]


@st.composite
def html_with_formatting(draw):
    """Generate code blocks with various formatting (whitespace, indentation)."""
    # Create code with specific formatting patterns
    indent = draw(st.sampled_from(['    ', '  ', '\t']))
    lines = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=5,
            max_size=50
        ),
        min_size=3,
        max_size=10
    ))
    
    # Create indented code
    code_lines = [f"{indent}{line}" for line in lines]
    code_text = '\n'.join(code_lines)
    
    html = f"<html><body><pre><code>{code_text}</code></pre></body></html>"
    
    return html, code_text, indent


@pytest.mark.property
class TestHTMLContentExtraction:
    """Property-based tests for HTML content extraction.
    
    Tag: Feature: local-ai-dev-environment, Property 1: HTML Content Extraction
    """
    
    def setup_method(self):
        """Initialize WebResearchModule for each test."""
        self.web_research = WebResearchModule()
    
    @given(html_data=html_with_text())
    @settings(max_examples=100, deadline=None)
    def test_all_text_content_extracted(self, html_data):
        """Test that all text content from body is present in extracted text.
        
        **Validates: Requirements 5.3**
        
        Property: For any valid HTML document, the extracted text SHALL contain
        all text content from the document body.
        
        Tag: Feature: local-ai-dev-environment, Property 1: HTML Content Extraction
        """
        html, expected_texts = html_data
        
        # Parse HTML and extract main content
        soup = BeautifulSoup(html, 'lxml')
        extracted_text = self.web_research._extract_main_content(soup)
        
        # Verify all expected text is present in extracted content
        for expected_text in expected_texts:
            expected_text_stripped = expected_text.strip()
            if expected_text_stripped:  # Only check non-empty text
                assert expected_text_stripped in extracted_text, (
                    f"Expected text '{expected_text_stripped}' not found in extracted content. "
                    f"Extracted: {extracted_text[:200]}..."
                )
    
    @given(html_data=html_with_code_blocks())
    @settings(max_examples=100, deadline=None)
    def test_all_code_blocks_captured(self, html_data):
        """Test that all code blocks are captured as separate code examples.
        
        **Validates: Requirements 5.3**
        
        Property: For any valid HTML document, all code blocks (identified by
        <code> or <pre> tags) SHALL be captured as separate code examples.
        
        Tag: Feature: local-ai-dev-environment, Property 1: HTML Content Extraction
        """
        html, expected_code_blocks = html_data
        
        # Extract code examples
        code_examples = self.web_research.extract_code_examples(html)
        
        # Verify we captured at least as many code blocks as expected
        assert len(code_examples) >= len(expected_code_blocks), (
            f"Expected at least {len(expected_code_blocks)} code blocks, "
            f"but found {len(code_examples)}"
        )
        
        # Verify each expected code block is present in extracted examples
        extracted_codes = [example.code for example in code_examples]
        
        for expected_code, expected_lang in expected_code_blocks:
            # Check if the code text is present in any extracted code
            found = any(expected_code.strip() in extracted.strip() 
                       for extracted in extracted_codes)
            
            assert found, (
                f"Expected code block not found in extracted examples. "
                f"Expected code (first 100 chars): {expected_code[:100]}... "
                f"Extracted codes: {[c[:100] for c in extracted_codes]}"
            )
    
    @given(html_data=html_with_formatting())
    @settings(max_examples=100, deadline=None)
    def test_code_formatting_preserved(self, html_data):
        """Test that code formatting is preserved (whitespace, indentation, line breaks).
        
        **Validates: Requirements 5.3**
        
        Property: For any valid HTML document, code formatting SHALL be preserved
        including whitespace, indentation, and line breaks.
        
        Tag: Feature: local-ai-dev-environment, Property 1: HTML Content Extraction
        """
        html, expected_code, expected_indent = html_data
        
        # Extract code examples
        code_examples = self.web_research.extract_code_examples(html)
        
        # Should have at least one code example
        assert len(code_examples) > 0, "No code examples extracted"
        
        # Get the extracted code
        extracted_code = code_examples[0].code
        
        # Verify the code text matches (may have minor whitespace differences)
        # The key is that indentation and line breaks are preserved
        assert extracted_code.strip() == expected_code.strip(), (
            f"Code content mismatch. Expected:\n{expected_code}\n\nGot:\n{extracted_code}"
        )
        
        # Verify indentation is preserved
        if expected_indent in expected_code:
            assert expected_indent in extracted_code, (
                f"Expected indentation '{repr(expected_indent)}' not preserved in extracted code"
            )
        
        # Verify line breaks are preserved
        expected_line_count = expected_code.count('\n')
        extracted_line_count = extracted_code.count('\n')
        
        # Allow for minor differences due to trailing whitespace handling
        assert abs(expected_line_count - extracted_line_count) <= 1, (
            f"Line break count mismatch. Expected ~{expected_line_count} lines, "
            f"got {extracted_line_count} lines"
        )
    
    @given(html_data=html_with_nested_structure())
    @settings(max_examples=100, deadline=None)
    def test_nested_structure_extraction(self, html_data):
        """Test extraction from nested HTML structures.
        
        **Validates: Requirements 5.3**
        
        Property: For any valid HTML document with nested tags, all text and
        code content SHALL be extracted regardless of nesting depth.
        
        Tag: Feature: local-ai-dev-environment, Property 1: HTML Content Extraction
        """
        html, expected_texts, expected_codes = html_data
        
        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract text content
        extracted_text = self.web_research._extract_main_content(soup)
        
        # Verify all text content is present
        for expected_text in expected_texts:
            expected_text_stripped = expected_text.strip()
            if expected_text_stripped:
                assert expected_text_stripped in extracted_text, (
                    f"Expected nested text '{expected_text_stripped}' not found"
                )
        
        # Extract code examples
        code_examples = self.web_research.extract_code_examples(soup)
        
        # Verify code blocks are captured
        assert len(code_examples) >= len(expected_codes), (
            f"Expected at least {len(expected_codes)} code blocks from nested structure"
        )
        
        # Verify code content
        extracted_codes = [example.code for example in code_examples]
        for expected_code in expected_codes:
            found = any(expected_code.strip() in extracted.strip() 
                       for extracted in extracted_codes)
            assert found, f"Expected code from nested structure not found"
    
    @given(
        code_text=code_content_strategy,
        language=st.one_of(st.none(), language_strategy)
    )
    @settings(max_examples=100, deadline=None)
    def test_language_detection_preserved(self, code_text, language):
        """Test that language hints in HTML are detected and preserved.
        
        **Validates: Requirements 5.3**
        
        While not strictly part of the core property, language detection
        enhances the extracted code examples with useful metadata.
        
        Tag: Feature: local-ai-dev-environment, Property 1: HTML Content Extraction
        """
        assume(len(code_text.strip()) > 10)
        
        # Create HTML with language hint
        if language:
            html = f'<html><body><pre><code class="language-{language}">{code_text}</code></pre></body></html>'
        else:
            html = f'<html><body><pre><code>{code_text}</code></pre></body></html>'
        
        # Extract code examples
        code_examples = self.web_research.extract_code_examples(html)
        
        # Should have at least one code example
        assert len(code_examples) > 0, "No code examples extracted"
        
        # If language was specified, verify it was detected
        if language:
            detected_language = code_examples[0].language
            assert detected_language == language, (
                f"Expected language '{language}', but detected '{detected_language}'"
            )
    
    @given(
        texts=st.lists(html_text_strategy, min_size=1, max_size=5),
        codes=st.lists(code_content_strategy, min_size=1, max_size=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_mixed_content_extraction(self, texts, codes):
        """Test extraction from HTML with mixed text and code content.
        
        **Validates: Requirements 5.3**
        
        Property: For any HTML document containing both text and code,
        both SHALL be extracted independently and completely.
        
        Tag: Feature: local-ai-dev-environment, Property 1: HTML Content Extraction
        """
        # Filter codes to ensure they're substantial
        codes = [c for c in codes if len(c.strip()) > 10]
        assume(len(codes) > 0)
        
        # Build HTML with alternating text and code
        html_parts = ["<html><body>"]
        
        # Iterate over max length to include all texts and codes
        max_len = max(len(texts), len(codes))
        for i in range(max_len):
            if i < len(texts):
                html_parts.append(f"<p>{texts[i]}</p>")
            if i < len(codes):
                html_parts.append(f"<pre><code>{codes[i]}</code></pre>")
        
        html_parts.append("</body></html>")
        html = ''.join(html_parts)
        
        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract text
        extracted_text = self.web_research._extract_main_content(soup)
        
        # Verify text content
        for text in texts:
            if text.strip():
                assert text.strip() in extracted_text
        
        # Extract code
        code_examples = self.web_research.extract_code_examples(soup)
        
        # Verify code content
        assert len(code_examples) >= len(codes)
        extracted_codes = [example.code for example in code_examples]
        
        for expected_code in codes:
            found = any(expected_code.strip() in extracted.strip() 
                       for extracted in extracted_codes)
            assert found, f"Expected code not found in mixed content extraction"
