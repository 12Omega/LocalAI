"""Web research module for searching and fetching information from websites.

This module provides web search capabilities and HTML content extraction
with a focus on privacy and official documentation sources.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging
import re
from urllib.parse import urlparse, urljoin

from src.core.error_handler import ErrorHandler, RetryStrategy


# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from web search."""
    title: str
    url: str
    snippet: str
    domain: str


@dataclass
class WebPage:
    """Fetched and parsed web page content."""
    url: str
    title: str
    main_content: str
    code_examples: List['CodeExample']
    success: bool
    error_message: Optional[str] = None


@dataclass
class CodeExample:
    """Extracted code block from web page."""
    code: str
    language: Optional[str] = None  # Programming language if detected


class WebResearchModule:
    """
    Module for web research capabilities including search and content extraction.
    
    This module prioritizes privacy by only sending search queries (not code content)
    and logs all web requests for transparency.
    """
    
    # Official documentation domains to prioritize
    OFFICIAL_DOMAINS = {
        'python.org', 'docs.python.org',
        'docs.microsoft.com', 'learn.microsoft.com',
        'developer.mozilla.org',
        'docs.oracle.com',
        'golang.org', 'go.dev',
        'doc.rust-lang.org', 'rust-lang.org',
        'cppreference.com',
        'docs.npmjs.com', 'nodejs.org',
        'reactjs.org', 'react.dev',
        'vuejs.org',
        'angular.io',
        'flask.palletsprojects.com',
        'docs.djangoproject.com',
        'spring.io',
    }
    
    def __init__(self, timeout: int = 10, user_agent: Optional[str] = None):
        """
        Initialize web research module.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string (uses default if None)
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; LocalAIDevBot/1.0; "
            "+https://github.com/local-ai-dev)"
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        # Initialize error handler with retry strategy for network operations
        self.error_handler = ErrorHandler(logger=logger)
        self.retry_strategy = RetryStrategy(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )
        
        logger.info("WebResearchModule initialized with timeout=%ds", timeout)
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search the web for relevant documentation and information.
        
        Uses automatic retry with exponential backoff for transient network failures.
        Privacy: Only the search query is sent to the search service,
        not any code content from the local project.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects, prioritized with official docs first
            
        Raises:
            None - errors are logged and empty list is returned
        """
        logger.info("Web search request: query='%s', max_results=%d", query, max_results)
        
        try:
            # Use retry logic for search with automatic recovery
            results = self.error_handler.retry_with_backoff(
                self._search_duckduckgo,
                query,
                max_results,
                strategy=self.retry_strategy,
                operation_name="web search"
            )
            
            # Prioritize official documentation domains
            results = self._prioritize_official_docs(results)
            
            logger.info("Web search completed: found %d results", len(results))
            return results[:max_results]
            
        except Exception as e:
            logger.error("Web search failed after retries: %s", str(e), exc_info=True)
            return []
    
    def fetch_page(self, url: str) -> WebPage:
        """
        Fetch and parse web page content.
        
        Uses automatic retry with exponential backoff for transient network failures.
        Extracts main content text and code examples from the page.
        Privacy: All fetched URLs are logged for transparency.
        
        Args:
            url: URL of the page to fetch
            
        Returns:
            WebPage object containing extracted content and code examples
        """
        logger.info("Fetching web page: %s", url)
        
        try:
            # Use retry logic with automatic recovery for transient network issues
            def fetch_and_parse():
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Extract title
                title = soup.title.string if soup.title else "Untitled"
                
                # Extract main content (remove scripts, styles, navigation, etc.)
                main_content = self._extract_main_content(soup)
                
                # Extract code examples
                code_examples = self.extract_code_examples(soup)
                
                logger.info("Successfully fetched page: %s (found %d code examples)",
                           url, len(code_examples))
                
                return WebPage(
                    url=url,
                    title=title.strip(),
                    main_content=main_content,
                    code_examples=code_examples,
                    success=True
                )
            
            return self.error_handler.retry_with_backoff(
                fetch_and_parse,
                strategy=self.retry_strategy,
                operation_name=f"fetch page {url}"
            )
            
        except requests.Timeout:
            error_msg = f"Request timeout after {self.timeout}s and {self.retry_strategy.max_retries} retries"
            logger.warning("Failed to fetch %s: %s", url, error_msg)
            return WebPage(
                url=url, title="", main_content="", code_examples=[],
                success=False, error_message=error_msg
            )
            
        except requests.RequestException as e:
            error_msg = f"Network error after {self.retry_strategy.max_retries} retries: {str(e)}"
            logger.warning("Failed to fetch %s: %s", url, error_msg)
            return WebPage(
                url=url, title="", main_content="", code_examples=[],
                success=False, error_message=error_msg
            )
            
        except Exception as e:
            error_msg = f"Parsing error: {str(e)}"
            logger.error("Failed to parse %s: %s", url, error_msg, exc_info=True)
            return WebPage(
                url=url, title="", main_content="", code_examples=[],
                success=False, error_message=error_msg
            )
    
    def extract_code_examples(self, content) -> List[CodeExample]:
        """
        Extract code blocks from HTML content.
        
        Identifies code blocks using <code> and <pre> tags, preserving
        formatting and attempting to detect programming language.
        
        Args:
            content: BeautifulSoup object or HTML string
            
        Returns:
            List of CodeExample objects
        """
        if isinstance(content, str):
            soup = BeautifulSoup(content, 'lxml')
        else:
            soup = content
        
        code_examples = []
        
        # Find <pre> tags (often contain multi-line code)
        for pre_tag in soup.find_all('pre'):
            # Look for <code> inside <pre>
            code_tag = pre_tag.find('code')
            if code_tag:
                code_text = code_tag.get_text()
                language = self._detect_language(code_tag)
            else:
                code_text = pre_tag.get_text()
                language = self._detect_language(pre_tag)
            
            # Only include if it looks like actual code (has some substance)
            if code_text.strip() and len(code_text.strip()) > 10:
                code_examples.append(CodeExample(
                    code=code_text,
                    language=language
                ))
        
        # Find standalone <code> tags not inside <pre>
        for code_tag in soup.find_all('code'):
            # Skip if already processed as part of <pre>
            if code_tag.find_parent('pre'):
                continue
            
            code_text = code_tag.get_text()
            
            # Only include multi-line or substantial code blocks
            if '\n' in code_text or len(code_text.strip()) > 20:
                language = self._detect_language(code_tag)
                code_examples.append(CodeExample(
                    code=code_text,
                    language=language
                ))
        
        logger.debug("Extracted %d code examples", len(code_examples))
        return code_examples
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Perform search using DuckDuckGo HTML interface.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of SearchResult objects
        """
        # DuckDuckGo HTML search endpoint
        url = "https://html.duckduckgo.com/html/"
        params = {'q': query}
        
        response = self.session.post(url, data=params, timeout=self.timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        results = []
        
        # Parse search results
        for result_div in soup.find_all('div', class_='result'):
            if len(results) >= max_results:
                break
            
            # Extract title and URL
            title_tag = result_div.find('a', class_='result__a')
            if not title_tag:
                continue
            
            title = title_tag.get_text().strip()
            url = title_tag.get('href', '')
            
            # Extract snippet
            snippet_tag = result_div.find('a', class_='result__snippet')
            snippet = snippet_tag.get_text().strip() if snippet_tag else ""
            
            # Extract domain
            domain = urlparse(url).netloc if url else ""
            
            if title and url:
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    domain=domain
                ))
        
        return results
    
    def _prioritize_official_docs(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Reorder search results to place official documentation sources first.
        
        Official docs are identified by domain matching OFFICIAL_DOMAINS.
        Relative order within each category (official/informal) is preserved.
        
        Args:
            results: List of search results
            
        Returns:
            Reordered list with official docs first
        """
        official = []
        informal = []
        
        for result in results:
            # Check if domain or any parent domain is in official list
            domain_parts = result.domain.split('.')
            is_official = False
            
            # Check full domain and parent domains
            for i in range(len(domain_parts)):
                partial_domain = '.'.join(domain_parts[i:])
                if partial_domain in self.OFFICIAL_DOMAINS:
                    is_official = True
                    break
            
            # Also check if domain ends with any official domain
            for official_domain in self.OFFICIAL_DOMAINS:
                if result.domain.endswith(official_domain):
                    is_official = True
                    break
            
            if is_official:
                official.append(result)
            else:
                informal.append(result)
        
        logger.debug("Prioritized results: %d official, %d informal",
                    len(official), len(informal))
        
        return official + informal
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from HTML, removing navigation, ads, etc.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted text content
        """
        # Remove unwanted elements
        # Note: we don't remove 'header' tags as they may contain content
        for element in soup(['script', 'style', 'nav', 'footer',
                            'aside', 'form', 'button']):
            element.decompose()
        
        # Try to find main content area
        main_content = soup.find('main')
        if not main_content:
            main_content = soup.find('article')
        if not main_content:
            main_content = soup.find('div', class_=re.compile(r'content|main|article'))
        if not main_content:
            main_content = soup.find('body')
        if not main_content:
            main_content = soup
        
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        return '\n'.join(lines)
    
    def _detect_language(self, tag) -> Optional[str]:
        """
        Attempt to detect programming language from HTML tag attributes.
        
        Args:
            tag: BeautifulSoup tag element
            
        Returns:
            Language name or None if not detected
        """
        # Check class attribute for language hints
        classes = tag.get('class', [])
        for cls in classes:
            cls_lower = cls.lower()
            
            # Common patterns: language-python, lang-python, python, highlight-python
            if 'python' in cls_lower or cls_lower == 'py':
                return 'python'
            if 'javascript' in cls_lower or cls_lower == 'js':
                return 'javascript'
            if 'typescript' in cls_lower or cls_lower == 'ts':
                return 'typescript'
            if 'java' in cls_lower and 'javascript' not in cls_lower:
                return 'java'
            if 'cpp' in cls_lower or 'c++' in cls_lower:
                return 'cpp'
            if 'rust' in cls_lower or cls_lower == 'rs':
                return 'rust'
            # Check for 'go' more carefully to avoid false positives
            if cls_lower == 'go' or 'golang' in cls_lower or cls_lower in ['language-go', 'lang-go', 'highlight-go']:
                return 'go'
            if 'sql' in cls_lower:
                return 'sql'
            if 'bash' in cls_lower or 'shell' in cls_lower or cls_lower == 'sh':
                return 'bash'
            if 'html' in cls_lower:
                return 'html'
            if 'css' in cls_lower:
                return 'css'
            if 'json' in cls_lower:
                return 'json'
            if 'yaml' in cls_lower or 'yml' in cls_lower:
                return 'yaml'
        
        # Check data-language or data-lang attributes
        if tag.get('data-language'):
            return tag.get('data-language').lower()
        if tag.get('data-lang'):
            return tag.get('data-lang').lower()
        
        return None
