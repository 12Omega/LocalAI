"""Unit tests for WebResearchModule.

Tests web search, HTML parsing, content extraction, code block extraction,
and error handling using mock HTTP responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import ConnectionError, Timeout, HTTPError
from bs4 import BeautifulSoup

from src.web.web_research import (
    WebResearchModule,
    SearchResult,
    WebPage,
    CodeExample,
)


class TestWebResearchModuleInit:
    """Tests for WebResearchModule initialization."""
    
    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        module = WebResearchModule()
        
        assert module.timeout == 10
        assert "LocalAIDevBot" in module.user_agent
        assert module.session is not None
        assert module.session.headers.get('User-Agent') == module.user_agent
    
    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        module = WebResearchModule(timeout=30)
        
        assert module.timeout == 30
    
    def test_init_custom_user_agent(self):
        """Test initialization with custom user agent."""
        custom_agent = "TestBot/1.0"
        module = WebResearchModule(user_agent=custom_agent)
        
        assert module.user_agent == custom_agent
        assert module.session.headers.get('User-Agent') == custom_agent


class TestWebSearch:
    """Tests for web search functionality."""
    
    @patch('src.web.web_research.WebResearchModule._search_duckduckgo')
    def test_search_basic_query(self, mock_search):
        """Test basic web search with query."""
        mock_results = [
            SearchResult(
                title="Python Documentation",
                url="https://docs.python.org",
                snippet="Official Python docs",
                domain="docs.python.org"
            ),
            SearchResult(
                title="Python Tutorial",
                url="https://example.com/python",
                snippet="Learn Python",
                domain="example.com"
            )
        ]
        mock_search.return_value = mock_results
        
        module = WebResearchModule()
        results = module.search("Python documentation")
        
        assert len(results) == 2
        assert results[0].title == "Python Documentation"
        mock_search.assert_called_once_with("Python documentation", 10)
    
    @patch('src.web.web_research.WebResearchModule._search_duckduckgo')
    def test_search_max_results_parameter(self, mock_search):
        """Test search respects max_results parameter."""
        mock_results = [
            SearchResult(
                title=f"Result {i}",
                url=f"https://example.com/{i}",
                snippet=f"Snippet {i}",
                domain="example.com"
            ) for i in range(20)
        ]
        mock_search.return_value = mock_results
        
        module = WebResearchModule()
        results = module.search("test query", max_results=5)
        
        assert len(results) == 5
        mock_search.assert_called_once_with("test query", 5)
    
    @patch('src.web.web_research.WebResearchModule._search_duckduckgo')
    def test_search_prioritizes_official_docs(self, mock_search):
        """Test search prioritizes official documentation domains."""
        mock_results = [
            SearchResult(
                title="Blog Post",
                url="https://blog.example.com/python",
                snippet="Informal blog",
                domain="blog.example.com"
            ),
            SearchResult(
                title="Python Docs",
                url="https://docs.python.org/tutorial",
                snippet="Official tutorial",
                domain="docs.python.org"
            ),
            SearchResult(
                title="Another Blog",
                url="https://medium.com/python",
                snippet="Medium post",
                domain="medium.com"
            )
        ]
        mock_search.return_value = mock_results
        
        module = WebResearchModule()
        results = module.search("Python tutorial")
        
        # Official docs should be first
        assert results[0].domain == "docs.python.org"
        assert results[0].title == "Python Docs"
    
    @patch('src.web.web_research.WebResearchModule._search_duckduckgo')
    def test_search_exception_handling(self, mock_search):
        """Test search handles exceptions gracefully."""
        mock_search.side_effect = Exception("Network error")
        
        module = WebResearchModule()
        results = module.search("test query")
        
        # Should return empty list on error
        assert results == []
    
    @patch('src.web.web_research.WebResearchModule._search_duckduckgo')
    def test_search_returns_empty_on_timeout(self, mock_search):
        """Test search returns empty list on timeout."""
        mock_search.side_effect = Timeout("Request timed out")
        
        module = WebResearchModule()
        results = module.search("test query")
        
        assert results == []
    
    def test_search_privacy_only_query_sent(self):
        """Test that only search query is sent, not code content.
        
        This test verifies privacy requirement: search queries are sent,
        but no local code content is transmitted.
        """
        with patch('src.web.web_research.WebResearchModule._search_duckduckgo') as mock_search:
            mock_search.return_value = []
            
            module = WebResearchModule()
            
            # Search with a query that could contain code
            query = "How to implement factorial"
            module.search(query)
            
            # Verify only the query string was passed
            mock_search.assert_called_once()
            call_args = mock_search.call_args[0]
            assert call_args[0] == query
            # Verify no additional code content was sent
            assert len(call_args) == 2  # query and max_results only


class TestDuckDuckGoSearch:
    """Tests for DuckDuckGo search implementation."""
    
    @patch('src.web.web_research.requests.Session.post')
    def test_duckduckgo_search_success(self, mock_post):
        """Test successful DuckDuckGo search."""
        html_response = """
        <html>
            <body>
                <div class="result">
                    <a class="result__a" href="https://python.org">Python</a>
                    <a class="result__snippet">Python programming language</a>
                </div>
                <div class="result">
                    <a class="result__a" href="https://docs.python.org">Python Docs</a>
                    <a class="result__snippet">Official documentation</a>
                </div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_response.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        module = WebResearchModule()
        results = module._search_duckduckgo("Python", max_results=10)
        
        assert len(results) == 2
        assert results[0].title == "Python"
        assert results[0].url == "https://python.org"
        assert results[0].snippet == "Python programming language"
        assert results[0].domain == "python.org"
    
    @patch('src.web.web_research.requests.Session.post')
    def test_duckduckgo_search_respects_max_results(self, mock_post):
        """Test that search respects max_results limit."""
        # Create HTML with 10 results
        html_results = "".join([
            f'<div class="result"><a class="result__a" href="https://example.com/{i}">Result {i}</a></div>'
            for i in range(10)
        ])
        html_response = f"<html><body>{html_results}</body></html>"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_response.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        module = WebResearchModule()
        results = module._search_duckduckgo("test", max_results=3)
        
        # Should stop at max_results
        assert len(results) == 3
    
    @patch('src.web.web_research.requests.Session.post')
    def test_duckduckgo_search_skips_invalid_results(self, mock_post):
        """Test that invalid results (missing title or URL) are skipped."""
        html_response = """
        <html>
            <body>
                <div class="result">
                    <a class="result__a" href="https://valid.com">Valid Result</a>
                </div>
                <div class="result">
                    <a class="result__a">No URL</a>
                </div>
                <div class="result">
                    <a class="result__snippet">No title link</a>
                </div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_response.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        module = WebResearchModule()
        results = module._search_duckduckgo("test", max_results=10)
        
        # Only the valid result should be returned
        assert len(results) == 1
        assert results[0].url == "https://valid.com"


class TestOfficialDocsPrioritization:
    """Tests for official documentation prioritization."""
    
    def test_prioritize_official_docs_basic(self):
        """Test basic prioritization of official docs."""
        results = [
            SearchResult(
                title="Blog",
                url="https://blog.com",
                snippet="Blog post",
                domain="blog.com"
            ),
            SearchResult(
                title="Python Docs",
                url="https://docs.python.org",
                snippet="Official docs",
                domain="docs.python.org"
            ),
        ]
        
        module = WebResearchModule()
        prioritized = module._prioritize_official_docs(results)
        
        assert len(prioritized) == 2
        assert prioritized[0].domain == "docs.python.org"
        assert prioritized[1].domain == "blog.com"
    
    def test_prioritize_preserves_order_within_categories(self):
        """Test that relative order is preserved within official and informal categories."""
        results = [
            SearchResult(title="Blog1", url="https://blog1.com", snippet="", domain="blog1.com"),
            SearchResult(title="Blog2", url="https://blog2.com", snippet="", domain="blog2.com"),
            SearchResult(title="PythonDocs", url="https://docs.python.org", snippet="", domain="docs.python.org"),
            SearchResult(title="MozillaDocs", url="https://developer.mozilla.org", snippet="", domain="developer.mozilla.org"),
            SearchResult(title="Blog3", url="https://blog3.com", snippet="", domain="blog3.com"),
        ]
        
        module = WebResearchModule()
        prioritized = module._prioritize_official_docs(results)
        
        # Official docs should be first (in original order)
        assert prioritized[0].title == "PythonDocs"
        assert prioritized[1].title == "MozillaDocs"
        # Informal should be after (in original order)
        assert prioritized[2].title == "Blog1"
        assert prioritized[3].title == "Blog2"
        assert prioritized[4].title == "Blog3"
    
    def test_prioritize_handles_subdomain_official_docs(self):
        """Test prioritization recognizes official doc subdomains."""
        results = [
            SearchResult(title="Blog", url="https://example.com", snippet="", domain="example.com"),
            SearchResult(title="Rust Docs", url="https://doc.rust-lang.org", snippet="", domain="doc.rust-lang.org"),
        ]
        
        module = WebResearchModule()
        prioritized = module._prioritize_official_docs(results)
        
        assert prioritized[0].domain == "doc.rust-lang.org"
    
    def test_prioritize_all_official_docs(self):
        """Test when all results are official docs."""
        results = [
            SearchResult(title="Python", url="https://python.org", snippet="", domain="python.org"),
            SearchResult(title="MDN", url="https://developer.mozilla.org", snippet="", domain="developer.mozilla.org"),
        ]
        
        module = WebResearchModule()
        prioritized = module._prioritize_official_docs(results)
        
        # All should remain, order preserved
        assert len(prioritized) == 2
        assert prioritized[0].domain == "python.org"
        assert prioritized[1].domain == "developer.mozilla.org"
    
    def test_prioritize_no_official_docs(self):
        """Test when no results are official docs."""
        results = [
            SearchResult(title="Blog1", url="https://blog1.com", snippet="", domain="blog1.com"),
            SearchResult(title="Blog2", url="https://blog2.com", snippet="", domain="blog2.com"),
        ]
        
        module = WebResearchModule()
        prioritized = module._prioritize_official_docs(results)
        
        # All should remain, order preserved
        assert len(prioritized) == 2
        assert prioritized[0].domain == "blog1.com"
        assert prioritized[1].domain == "blog2.com"


class TestFetchPage:
    """Tests for web page fetching and parsing."""
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetch and parsing."""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <main>
                    <p>This is the main content.</p>
                    <p>Second paragraph.</p>
                </main>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        module = WebResearchModule()
        page = module.fetch_page("https://example.com")
        
        assert page.success is True
        assert page.title == "Test Page"
        assert "This is the main content" in page.main_content
        assert "Second paragraph" in page.main_content
        assert page.error_message is None
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_page_extracts_code_examples(self, mock_get):
        """Test that code examples are extracted from page."""
        html_content = """
        <html>
            <body>
                <pre><code>def hello():
    print("Hello")</code></pre>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        module = WebResearchModule()
        page = module.fetch_page("https://example.com")
        
        assert page.success is True
        assert len(page.code_examples) >= 1
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_page_timeout(self, mock_get):
        """Test handling of page fetch timeout."""
        mock_get.side_effect = Timeout("Request timed out")
        
        module = WebResearchModule()
        page = module.fetch_page("https://example.com")
        
        assert page.success is False
        assert "timeout" in page.error_message.lower()
        assert page.main_content == ""
        assert page.code_examples == []
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_page_connection_error(self, mock_get):
        """Test handling of connection error."""
        mock_get.side_effect = ConnectionError("Connection refused")
        
        module = WebResearchModule()
        page = module.fetch_page("https://example.com")
        
        assert page.success is False
        assert "network error" in page.error_message.lower()
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_page_http_error(self, mock_get):
        """Test handling of HTTP error (404, 500, etc.)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found", response=mock_response)
        mock_get.return_value = mock_response
        
        module = WebResearchModule()
        page = module.fetch_page("https://example.com/notfound")
        
        assert page.success is False
        assert page.error_message is not None
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_page_no_title(self, mock_get):
        """Test handling of page without title tag."""
        html_content = "<html><body><p>Content without title</p></body></html>"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        module = WebResearchModule()
        page = module.fetch_page("https://example.com")
        
        assert page.success is True
        assert page.title == "Untitled"


class TestContentExtraction:
    """Tests for HTML content extraction."""
    
    def test_extract_main_content_from_main_tag(self):
        """Test extraction from <main> tag."""
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <main>
                    <p>Main content here</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        
        module = WebResearchModule()
        content = module._extract_main_content(soup)
        
        assert "Main content here" in content
        assert "Navigation" not in content
        assert "Footer" not in content
    
    def test_extract_main_content_from_article_tag(self):
        """Test extraction from <article> tag when no <main>."""
        html = """
        <html>
            <body>
                <article>
                    <p>Article content</p>
                </article>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        
        module = WebResearchModule()
        content = module._extract_main_content(soup)
        
        assert "Article content" in content
    
    def test_extract_removes_script_and_style(self):
        """Test that scripts and styles are removed."""
        html = """
        <html>
            <head>
                <style>.test { color: red; }</style>
            </head>
            <body>
                <main>
                    <p>Visible content</p>
                    <script>console.log('hidden');</script>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        
        module = WebResearchModule()
        content = module._extract_main_content(soup)
        
        assert "Visible content" in content
        assert "console.log" not in content
        assert ".test" not in content
    
    def test_extract_removes_navigation_elements(self):
        """Test that navigation, header, footer are removed."""
        html = """
        <html>
            <body>
                <header>Header content</header>
                <nav>Navigation links</nav>
                <main>
                    <p>Main content</p>
                </main>
                <footer>Footer content</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        
        module = WebResearchModule()
        content = module._extract_main_content(soup)
        
        assert "Main content" in content
        assert "Header content" not in content
        assert "Navigation links" not in content
        assert "Footer content" not in content
    
    def test_extract_cleans_whitespace(self):
        """Test that excessive whitespace is cleaned up."""
        html = """
        <html>
            <body>
                <main>
                    <p>Line 1</p>
                    
                    
                    <p>Line 2</p>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        
        module = WebResearchModule()
        content = module._extract_main_content(soup)
        
        # Should not have multiple consecutive newlines
        assert "\n\n\n" not in content
        assert "Line 1" in content
        assert "Line 2" in content


class TestCodeExampleExtraction:
    """Tests for code block extraction."""
    
    def test_extract_code_from_pre_tag(self):
        """Test extraction of code from <pre> tags."""
        html = """
        <html>
            <body>
                <pre><code>def hello():
    print("Hello")
    return True</code></pre>
            </body>
        </html>
        """
        
        module = WebResearchModule()
        examples = module.extract_code_examples(html)
        
        assert len(examples) == 1
        assert "def hello():" in examples[0].code
        assert "print(\"Hello\")" in examples[0].code
    
    def test_extract_code_preserves_formatting(self):
        """Test that code formatting (indentation, whitespace) is preserved."""
        html = """
        <pre><code>def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)</code></pre>
        """
        
        module = WebResearchModule()
        examples = module.extract_code_examples(html)
        
        assert len(examples) == 1
        # Check indentation is preserved
        assert "    if n <= 1:" in examples[0].code
        assert "        return 1" in examples[0].code
    
    def test_extract_code_with_language_tag(self):
        """Test extraction of code with language identification."""
        html = """
        <pre><code class="language-python">print("Python code")</code></pre>
        <pre><code class="language-javascript">console.log("JS code");</code></pre>
        """
        
        module = WebResearchModule()
        examples = module.extract_code_examples(html)
        
        assert len(examples) == 2
        assert examples[0].language == "python"
        assert examples[1].language == "javascript"
    
    def test_extract_code_detects_various_language_formats(self):
        """Test language detection from various class formats."""
        test_cases = [
            ('<code class="python">code</code>', "python"),
            ('<code class="lang-python">code</code>', "python"),
            ('<code class="language-python">code</code>', "python"),
            ('<code class="highlight-python">code</code>', "python"),
            ('<code class="js">code</code>', "javascript"),
            ('<code class="language-typescript">code</code>', "typescript"),
            ('<code class="language-rust">code</code>', "rust"),
            ('<code class="language-go">code</code>', "go"),
        ]
        
        module = WebResearchModule()
        
        for html_snippet, expected_lang in test_cases:
            html = f"<html><body><pre>{html_snippet * 5}</pre></body></html>"
            examples = module.extract_code_examples(html)
            if examples:
                assert examples[0].language == expected_lang, f"Failed for {html_snippet}"
    
    def test_extract_code_from_standalone_code_tags(self):
        """Test extraction from <code> tags not inside <pre>."""
        html = """
        <html>
            <body>
                <p>Use <code>print("single line")</code> to output.</p>
                <code>function longCode() {
    return "multi-line standalone";
}</code>
            </body>
        </html>
        """
        
        module = WebResearchModule()
        examples = module.extract_code_examples(html)
        
        # Should extract the multi-line standalone code
        assert len(examples) >= 1
        # Single-line inline code should be skipped
        standalone = [ex for ex in examples if "function longCode" in ex.code]
        assert len(standalone) == 1
    
    def test_extract_code_skips_short_snippets(self):
        """Test that very short code snippets are skipped."""
        html = """
        <html>
            <body>
                <pre><code>x</code></pre>
                <pre><code>short</code></pre>
                <pre><code>This is a longer code snippet that should be included</code></pre>
            </body>
        </html>
        """
        
        module = WebResearchModule()
        examples = module.extract_code_examples(html)
        
        # Only the longer snippet should be extracted
        assert len(examples) == 1
        assert "longer code snippet" in examples[0].code
    
    def test_extract_code_from_beautifulsoup_object(self):
        """Test extraction from BeautifulSoup object (not just string)."""
        html = '<html><body><pre><code>def test():\n    pass</code></pre></body></html>'
        soup = BeautifulSoup(html, 'lxml')
        
        module = WebResearchModule()
        examples = module.extract_code_examples(soup)
        
        assert len(examples) == 1
        assert "def test():" in examples[0].code
    
    def test_extract_code_with_data_language_attribute(self):
        """Test language detection from data-language attribute."""
        html = """
        <pre><code data-language="python">print("test")</code></pre>
        <pre><code data-lang="rust">fn main() {}</code></pre>
        """
        
        module = WebResearchModule()
        examples = module.extract_code_examples(html)
        
        assert len(examples) == 2
        assert examples[0].language == "python"
        assert examples[1].language == "rust"
    
    def test_extract_code_multiple_blocks(self):
        """Test extraction of multiple code blocks from same page."""
        html = """
        <html>
            <body>
                <h2>Example 1</h2>
                <pre><code>def example1():
    return "first"</code></pre>
                <h2>Example 2</h2>
                <pre><code>def example2():
    return "second"</code></pre>
                <h2>Example 3</h2>
                <pre><code>def example3():
    return "third"</code></pre>
            </body>
        </html>
        """
        
        module = WebResearchModule()
        examples = module.extract_code_examples(html)
        
        assert len(examples) == 3
        assert "example1" in examples[0].code
        assert "example2" in examples[1].code
        assert "example3" in examples[2].code


class TestLanguageDetection:
    """Tests for programming language detection."""
    
    def test_detect_language_from_class(self):
        """Test language detection from class attribute."""
        test_cases = [
            ('class="language-python"', "python"),
            ('class="lang-javascript"', "javascript"),
            ('class="typescript"', "typescript"),
            ('class="java"', "java"),
            ('class="cpp"', "cpp"),
            ('class="rust"', "rust"),
            ('class="go"', "go"),
            ('class="sql"', "sql"),
            ('class="bash"', "bash"),
            ('class="shell"', "bash"),
            ('class="html"', "html"),
            ('class="css"', "css"),
            ('class="json"', "json"),
            ('class="yaml"', "yaml"),
        ]
        
        module = WebResearchModule()
        
        for class_attr, expected_lang in test_cases:
            html = f'<code {class_attr}>code</code>'
            soup = BeautifulSoup(html, 'lxml')
            tag = soup.find('code')
            
            detected = module._detect_language(tag)
            assert detected == expected_lang, f"Failed for {class_attr}"
    
    def test_detect_language_no_indicators(self):
        """Test that None is returned when no language indicators present."""
        html = '<code>some code</code>'
        soup = BeautifulSoup(html, 'lxml')
        tag = soup.find('code')
        
        module = WebResearchModule()
        detected = module._detect_language(tag)
        
        assert detected is None
    
    def test_detect_language_multiple_classes(self):
        """Test language detection when tag has multiple classes."""
        html = '<code class="highlight language-python line-numbers">code</code>'
        soup = BeautifulSoup(html, 'lxml')
        tag = soup.find('code')
        
        module = WebResearchModule()
        detected = module._detect_language(tag)
        
        assert detected == "python"
    
    def test_detect_language_case_insensitive(self):
        """Test that language detection is case-insensitive."""
        html = '<code class="language-PYTHON">code</code>'
        soup = BeautifulSoup(html, 'lxml')
        tag = soup.find('code')
        
        module = WebResearchModule()
        detected = module._detect_language(tag)
        
        assert detected == "python"
    
    def test_detect_language_distinguishes_java_javascript(self):
        """Test that java and javascript are properly distinguished."""
        # Java should be detected
        html_java = '<code class="language-java">code</code>'
        soup = BeautifulSoup(html_java, 'lxml')
        tag = soup.find('code')
        
        module = WebResearchModule()
        assert module._detect_language(tag) == "java"
        
        # JavaScript should be detected
        html_js = '<code class="language-javascript">code</code>'
        soup = BeautifulSoup(html_js, 'lxml')
        tag = soup.find('code')
        
        assert module._detect_language(tag) == "javascript"


class TestPrivacyRequirements:
    """Tests verifying privacy requirements."""
    
    @patch('src.web.web_research.requests.Session.post')
    def test_search_only_sends_query_not_code(self, mock_post):
        """Test that web search only sends query, never code content.
        
        This is a critical privacy requirement: the system must not
        transmit local code to external search services.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html></html>"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        module = WebResearchModule()
        
        # Simulate searching with what could be code content
        query = "Python list comprehension"
        module.search(query)
        
        # Verify the request
        assert mock_post.called
        call_args = mock_post.call_args
        
        # Check that only the query was sent
        posted_data = call_args[1]['data']
        assert posted_data['q'] == query
        # Ensure no additional code-like content was sent
        assert len(posted_data) == 1  # Only the query parameter
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_logs_all_urls(self, mock_get):
        """Test that all fetched URLs are logged for transparency."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        module = WebResearchModule()
        
        with patch('src.web.web_research.logger') as mock_logger:
            url = "https://example.com/page"
            module.fetch_page(url)
            
            # Verify URL was logged
            logged = False
            for call in mock_logger.info.call_args_list:
                if url in str(call):
                    logged = True
                    break
            
            assert logged, "URL should be logged for transparency"
    
    def test_no_code_transmission_in_fetch(self):
        """Test that fetch_page doesn't send local code content.
        
        Fetch only receives a URL and doesn't transmit any local code.
        """
        with patch('src.web.web_research.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"<html><body>Content</body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            module = WebResearchModule()
            module.fetch_page("https://example.com")
            
            # Verify only URL was used in request
            call_args = mock_get.call_args
            assert len(call_args[0]) == 1  # Only URL argument
            assert call_args[0][0] == "https://example.com"
            # Verify no code content in kwargs
            kwargs = call_args[1]
            assert 'data' not in kwargs
            assert 'json' not in kwargs


class TestErrorRecovery:
    """Tests for error handling and recovery."""
    
    @patch('src.web.web_research.requests.Session.get')
    def test_fetch_page_unavailable_returns_failure(self, mock_get):
        """Test that unavailable website returns WebPage with success=False."""
        mock_get.side_effect = ConnectionError("Connection refused")
        
        module = WebResearchModule()
        page = module.fetch_page("https://unavailable.com")
        
        assert isinstance(page, WebPage)
        assert page.success is False
        assert page.error_message is not None
        assert page.url == "https://unavailable.com"
    
    @patch('src.web.web_research.requests.Session.get')
    def test_multiple_fetch_failures_handled_independently(self, mock_get):
        """Test that multiple fetch failures are handled independently."""
        # Create a properly configured mock response for the second call
        success_response = Mock()
        success_response.status_code = 200
        success_response.content = b"<html><head><title>Success</title></head><body>Success</body></html>"
        success_response.raise_for_status = Mock()  # Does nothing (successful request)
        
        # First call fails (with retry exhaustion: initial + 3 retries = 4 failures)
        # Second call succeeds
        mock_get.side_effect = [
            ConnectionError("Connection refused"),  # Initial attempt for first call
            ConnectionError("Connection refused"),  # Retry 1 for first call
            ConnectionError("Connection refused"),  # Retry 2 for first call
            ConnectionError("Connection refused"),  # Retry 3 for first call
            success_response  # Second call succeeds
        ]
        
        module = WebResearchModule()
        
        page1 = module.fetch_page("https://fail.com")
        assert page1.success is False
        
        page2 = module.fetch_page("https://success.com")
        assert page2.success is True
    
    @patch('src.web.web_research.requests.Session.post')
    def test_search_continues_after_network_error(self, mock_post):
        """Test that search failures don't break the module."""
        mock_post.side_effect = Timeout("Network timeout")
        
        module = WebResearchModule()
        
        # First search fails
        results1 = module.search("query1")
        assert results1 == []
        
        # Module should still work for subsequent searches
        mock_post.side_effect = None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body></body></html>"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # This should work
        results2 = module.search("query2")
        assert isinstance(results2, list)
    
    def test_extract_code_handles_malformed_html(self):
        """Test code extraction handles malformed HTML gracefully."""
        malformed_html = "<pre><code>def test()\n    print('missing closing tags"
        
        module = WebResearchModule()
        # Should not raise exception
        examples = module.extract_code_examples(malformed_html)
        
        # BeautifulSoup is lenient, should still extract something
        assert isinstance(examples, list)
