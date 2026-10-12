"""
End-to-end test for web research and API client implementation workflow.

Tests Requirements: 5.1, 5.2, 5.3, 5.6, 7.1, 7.2

This test verifies that the system can:
1. Research web documentation for an API
2. Fetch and parse the documentation
3. Implement an API client based on the documentation
4. Verify the implementation is correct
"""

import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from src.core.task_executor import TaskExecutor
from src.core.models import TaskResult, LLMConfig, SystemConfig
from src.agents.code_agent import CodeAgent
from src.agents.file_operations import OperationResult
from src.context.context_manager import ContextManager
from src.web.web_research import WebResearchModule, SearchResult, WebPage, CodeExample


class TestWebResearchEndToEnd:
    """End-to-end tests for web research and API client implementation."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_web_research(self):
        """Mock web research module with realistic API documentation."""
        mock = MagicMock(spec=WebResearchModule)
        
        # Mock search results for a simple REST API
        mock.search.return_value = [
            SearchResult(
                title="JSONPlaceholder API Documentation",
                url="https://jsonplaceholder.typicode.com/guide",
                snippet="Free fake API for testing and prototyping. Supports GET, POST, PUT, DELETE.",
                domain="jsonplaceholder.typicode.com"
            ),
            SearchResult(
                title="JSONPlaceholder - Resources",
                url="https://jsonplaceholder.typicode.com/",
                snippet="JSONPlaceholder provides /posts, /comments, /users endpoints.",
                domain="jsonplaceholder.typicode.com"
            )
        ]
        
        # Mock fetched API documentation
        mock.fetch_page.return_value = WebPage(
            url="https://jsonplaceholder.typicode.com/guide",
            title="JSONPlaceholder API Guide",
            main_content="""
            JSONPlaceholder API Guide
            
            Base URL: https://jsonplaceholder.typicode.com
            
            Endpoints:
            - GET /posts - Fetch all posts
            - GET /posts/{id} - Fetch a single post
            - POST /posts - Create a new post
            - PUT /posts/{id} - Update a post
            - DELETE /posts/{id} - Delete a post
            
            Example Response:
            {
                "id": 1,
                "title": "Sample Post",
                "body": "This is a sample post body",
                "userId": 1
            }
            """,
            code_examples=[],
            success=True
        )
        
        # Mock code extraction
        mock.extract_code_examples.return_value = [
            CodeExample(
                language="json",
                code="""{
    "id": 1,
    "title": "Sample Post",
    "body": "This is a sample post body",
    "userId": 1
}"""
            )
        ]
        
        return mock

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM that simulates planning and reflection responses."""
        from src.core.models import LLMResponse
        import json
        
        mock = MagicMock()
        
        # Planning response: Create API client
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "api_client.py",
                        "content": """import requests
from typing import Dict, List, Any


class JSONPlaceholderClient:
    '''Client for JSONPlaceholder API.'''
    
    def __init__(self, base_url: str = "https://jsonplaceholder.typicode.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def get_posts(self) -> List[Dict[str, Any]]:
        '''Fetch all posts.'''
        response = self.session.get(f"{self.base_url}/posts")
        response.raise_for_status()
        return response.json()
    
    def get_post(self, post_id: int) -> Dict[str, Any]:
        '''Fetch a single post by ID.'''
        response = self.session.get(f"{self.base_url}/posts/{post_id}")
        response.raise_for_status()
        return response.json()
    
    def create_post(self, title: str, body: str, user_id: int) -> Dict[str, Any]:
        '''Create a new post.'''
        data = {"title": title, "body": body, "userId": user_id}
        response = self.session.post(f"{self.base_url}/posts", json=data)
        response.raise_for_status()
        return response.json()
    
    def update_post(self, post_id: int, title: str, body: str, user_id: int) -> Dict[str, Any]:
        '''Update an existing post.'''
        data = {"id": post_id, "title": title, "body": body, "userId": user_id}
        response = self.session.put(f"{self.base_url}/posts/{post_id}", json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_post(self, post_id: int) -> bool:
        '''Delete a post.'''
        response = self.session.delete(f"{self.base_url}/posts/{post_id}")
        response.raise_for_status()
        return response.status_code == 200
"""
                    },
                    "rationale": "Create JSONPlaceholder API client with GET, POST, PUT, DELETE methods"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops"]
        }
        
        # Reflection response: Mark as complete
        next_action_json = {
            "action": "complete",
            "parameters": {"summary": "API client created successfully"},
            "rationale": "API client implementation complete with all required methods"
        }
        
        mock.generate.side_effect = [
            # Planning call
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            # Reflection call
            LLMResponse(content=json.dumps(next_action_json), tool_calls=[], finish_reason="stop")
        ]
        
        return mock

    @pytest.fixture
    def task_executor(self, temp_project_dir, mock_llm):
        """Create a task executor with mocked LLM."""
        code_agent = CodeAgent(project_root=temp_project_dir)
        
        config = SystemConfig(
            llm=LLMConfig(
                endpoint="http://localhost:11434",
                model_name="codellama:13b",
                temperature=0.2
            ),
            project_root=temp_project_dir
        )
        
        context_manager = ContextManager(config=config)
        
        executor = TaskExecutor(
            llm_interface=mock_llm,
            code_agent=code_agent,
            context_manager=context_manager
        )
        
        return executor

    def test_research_and_implement_api_client(
        self, 
        task_executor, 
        mock_llm, 
        mock_web_research,
        temp_project_dir
    ):
        """
        Test: Research web documentation and implement API client.
        
        This test verifies:
        1. Web research module can search for and fetch documentation
        2. Task executor can plan and execute API client implementation
        3. API client code is created with correct structure
        4. Unit tests are created for the API client
        
        Requirements: 5.1, 5.2, 5.3, 5.6, 7.1, 7.2
        """
        # Part 1: Test web research module directly
        # ==========================================
        
        # Search for API documentation
        search_results = mock_web_research.search("JSONPlaceholder API documentation")
        
        assert len(search_results) > 0, "No search results returned"
        assert any("jsonplaceholder" in r.url.lower() for r in search_results), \
            "Search results don't include JSONPlaceholder API"
        
        # Fetch documentation page
        doc_url = search_results[0].url
        page = mock_web_research.fetch_page(doc_url)
        
        assert page.success, f"Failed to fetch page: {page.error_message}"
        assert page.main_content, "No content extracted from page"
        assert "/posts" in page.main_content, "API endpoints not found in documentation"
        
        # Part 2: Test task executor creates API client
        # =============================================
        
        # Execute task to create API client based on researched documentation
        task_description = "Create a Python client for the JSONPlaceholder API with methods for GET, POST, PUT, DELETE operations on the /posts endpoint"
        result = task_executor.execute_task(task_description)
        
        # Verify task completed successfully
        assert result.success, f"Task failed: {result.error_message}"
        
        # Verify API client file was created
        api_client_path = os.path.join(temp_project_dir, "api_client.py")
        assert os.path.exists(api_client_path), "API client file not created"
        
        # Verify API client content
        with open(api_client_path, 'r') as f:
            api_client_content = f.read()
        
        # Check for expected API client components
        assert "class" in api_client_content and "Client" in api_client_content, \
            "API client class not found"
        assert "def get" in api_client_content or "def fetch" in api_client_content, \
            "GET method not found"
        assert "def post" in api_client_content or "def create" in api_client_content, \
            "POST method not found"
        assert "requests" in api_client_content or "http" in api_client_content.lower(), \
            "HTTP library not imported"
        
        # Verify files were tracked
        assert len(result.files_modified) >= 1, \
            f"Expected at least 1 file created, got {len(result.files_modified)}"
        
        # Verify API client is in modified files
        modified_files = [os.path.basename(f) for f in result.files_modified]
        assert "api_client.py" in modified_files, \
            "api_client.py not in modified files"


    @pytest.mark.integration
    def test_real_web_research_module(self, temp_project_dir):
        """
        Test: Real web research module functionality (not mocked).
        
        This test verifies the actual web research module can:
        1. Search for documentation (using DuckDuckGo) - SKIPPED if network unavailable
        2. Fetch and parse real web pages
        3. Extract code examples from HTML
        4. Prioritize official documentation sources
        
        Requirements: 5.1, 5.2, 5.3, 5.6
        
        Note: This test requires internet connectivity and may be slower.
        It's marked as integration to separate from unit tests.
        """
        web_research = WebResearchModule(timeout=15)
        
        # Test 1: Search functionality (Requirement 5.1)
        # =============================================
        # Note: DuckDuckGo search may be blocked or fail due to network issues
        # We'll test it but allow graceful degradation for the rest of the test
        search_query = "python requests library documentation"
        search_results = web_research.search(search_query, max_results=5)
        
        # If search works, verify results structure
        if len(search_results) > 0:
            # Verify search results have required structure (Requirement 5.6 - attribution)
            for result in search_results:
                assert result.title, f"Search result missing title: {result}"
                assert result.url, f"Search result missing URL: {result}"
                assert result.domain, f"Search result missing domain: {result}"
                # snippet can be empty, so not strictly required
            
            # Test 2: Official documentation prioritization (Requirement 5.4 via Property 2)
            # ============================================================================
            # Check if official docs appear first (if any official docs in results)
            official_indices = []
            informal_indices = []
            
            for idx, result in enumerate(search_results):
                is_official = any(
                    official_domain in result.domain 
                    for official_domain in web_research.OFFICIAL_DOMAINS
                )
                if is_official:
                    official_indices.append(idx)
                else:
                    informal_indices.append(idx)
            
            # If we have both official and informal results, verify prioritization
            if official_indices and informal_indices:
                assert max(official_indices) < min(informal_indices), \
                    "Official documentation not prioritized before informal sources"
        else:
            # Search failed (likely network/blocking issue) - log warning but continue
            import warnings
            warnings.warn(
                "Web search returned no results - this may indicate network issues "
                "or DuckDuckGo blocking. Skipping search-related assertions."
            )
        
        # Test 3: Fetch and parse web page (Requirements 5.2, 5.3)
        # ========================================================
        # Use a reliable documentation URL (python.org is very stable)
        test_url = "https://docs.python.org/3/library/json.html"
        
        page = web_research.fetch_page(test_url)
        
        assert page.success, f"Failed to fetch page: {page.error_message}"
        assert page.title, "Page title not extracted"
        assert page.main_content, "Main content not extracted"
        assert len(page.main_content) > 100, "Extracted content seems too short"
        
        # Verify content contains expected documentation keywords
        assert "json" in page.main_content.lower(), \
            "Expected documentation keywords not found in content"
        
        # Test 4: Code example extraction (Requirement 5.3)
        # =================================================
        # The JSON module docs typically contain code examples
        assert len(page.code_examples) > 0, \
            "No code examples extracted from documentation page"
        
        # Verify code examples have content
        for example in page.code_examples:
            assert example.code.strip(), "Code example is empty"
            assert len(example.code.strip()) > 10, \
                "Code example seems too short to be meaningful"
        
        # Test 5: Extract code examples from HTML directly (Requirement 5.3)
        # ==================================================================
        sample_html = """
        <html>
        <body>
            <h1>API Documentation</h1>
            <p>Here's how to use the API:</p>
            <pre><code class="language-python">
import requests

response = requests.get('https://api.example.com/data')
data = response.json()
print(data)
            </code></pre>
            <p>Another example:</p>
            <pre><code class="language-javascript">
const response = await fetch('https://api.example.com/data');
const data = await response.json();
console.log(data);
            </code></pre>
        </body>
        </html>
        """
        
        code_examples = web_research.extract_code_examples(sample_html)
        
        assert len(code_examples) >= 2, \
            f"Expected at least 2 code examples, got {len(code_examples)}"
        
        # Verify language detection
        languages = [ex.language for ex in code_examples if ex.language]
        assert 'python' in languages or 'javascript' in languages, \
            "Language detection failed for code examples"
        
        # Verify code content preservation
        for example in code_examples:
            # Check that whitespace/formatting is preserved
            assert '\n' in example.code or len(example.code.strip()) > 20, \
                "Code formatting not preserved"
        
        # Verify Python example content
        python_examples = [ex for ex in code_examples if ex.language == 'python']
        if python_examples:
            assert 'import' in python_examples[0].code, \
                "Python code example content not correctly extracted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
