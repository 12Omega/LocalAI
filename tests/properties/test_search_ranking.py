"""Property-based tests for documentation source prioritization.

This module tests Property 2: Documentation Source Prioritization
**Validates: Requirements 5.4**

The property ensures that official documentation sources are ranked before
informal sources while preserving relative order within each category.
"""

import pytest
from hypothesis import given, strategies as st, settings
from typing import List

from src.web.web_research import WebResearchModule, SearchResult


# Strategy for generating official documentation domains
@st.composite
def official_domain(draw):
    """Generate domains that should be recognized as official documentation."""
    # Use actual official domains from WebResearchModule.OFFICIAL_DOMAINS
    official_domains = [
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
    ]
    return draw(st.sampled_from(official_domains))


# Strategy for generating informal/non-official domains
@st.composite
def informal_domain(draw):
    """Generate domains that should be recognized as informal sources."""
    # Common informal sources
    informal_domains = [
        'stackoverflow.com',
        'github.com',
        'medium.com',
        'dev.to',
        'reddit.com',
        'blog.example.com',
        'tutorialspoint.com',
        'geeksforgeeks.org',
        'w3schools.com',
        'codepen.io',
        'jsfiddle.net',
        'codesandbox.io',
    ]
    return draw(st.sampled_from(informal_domains))


# Strategy for generating a single search result
@st.composite
def search_result(draw, domain_strategy):
    """Generate a SearchResult with specified domain strategy."""
    domain = draw(domain_strategy)
    
    # Generate title
    title = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'), max_codepoint=127),
        min_size=10,
        max_size=100
    ))
    
    # Generate URL with the domain
    path = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), max_codepoint=127),
        min_size=5,
        max_size=30
    ))
    url = f"https://{domain}/{path}"
    
    # Generate snippet
    snippet = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'), max_codepoint=127),
        min_size=20,
        max_size=200
    ))
    
    return SearchResult(
        title=title.strip() or "Untitled",
        url=url,
        snippet=snippet.strip() or "No description",
        domain=domain
    )


# Strategy for generating mixed search results
@st.composite
def mixed_search_results(draw):
    """Generate a list of search results with mixed official and informal domains.
    
    Returns a tuple of (results_list, num_official, num_informal)
    """
    # Generate 1-10 official results
    num_official = draw(st.integers(min_value=1, max_value=10))
    official_results = [
        draw(search_result(official_domain())) 
        for _ in range(num_official)
    ]
    
    # Generate 1-10 informal results
    num_informal = draw(st.integers(min_value=1, max_value=10))
    informal_results = [
        draw(search_result(informal_domain())) 
        for _ in range(num_informal)
    ]
    
    # Shuffle them together to create mixed list
    all_results = official_results + informal_results
    shuffled_results = draw(st.permutations(all_results))
    
    return list(shuffled_results), num_official, num_informal


class TestDocumentationSourcePrioritization:
    """
    Test suite for Property 2: Documentation Source Prioritization
    
    **Feature: local-ai-dev-environment**
    **Property 2: Documentation Source Prioritization**
    **Validates: Requirements 5.4**
    """
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.web_research = WebResearchModule()
    
    @given(mixed_search_results())
    @settings(max_examples=100)
    def test_official_docs_ranked_before_informal(self, search_data):
        """
        Test that official documentation domains are ranked before informal sources.
        
        **Feature: local-ai-dev-environment**
        **Property 2: Documentation Source Prioritization**
        **Validates: Requirements 5.4**
        
        Given: A list of search results with mixed official and informal domains
        When: The prioritization algorithm is applied
        Then: All official documentation results appear before all informal results
        """
        results, expected_official_count, expected_informal_count = search_data
        
        # Apply prioritization
        prioritized = self.web_research._prioritize_official_docs(results)
        
        # Verify we have the same number of results
        assert len(prioritized) == len(results), \
            "Prioritization should not change the number of results"
        
        # Verify all results are present (no duplicates or losses)
        assert set(r.url for r in prioritized) == set(r.url for r in results), \
            "Prioritization should not add or remove results"
        
        # Find the index where official docs end and informal docs begin
        official_count = 0
        informal_count = 0
        
        # Count official results from the start
        for result in prioritized:
            if self._is_official_domain(result.domain):
                official_count += 1
            else:
                break
        
        # All remaining results should be informal
        for i in range(official_count, len(prioritized)):
            assert not self._is_official_domain(prioritized[i].domain), \
                f"Found official domain at index {i} after informal sources started at {official_count}"
            informal_count += 1
        
        # Verify counts match expected
        assert official_count == expected_official_count, \
            f"Expected {expected_official_count} official results, got {official_count}"
        assert informal_count == expected_informal_count, \
            f"Expected {expected_informal_count} informal results, got {informal_count}"
    
    @given(mixed_search_results())
    @settings(max_examples=100)
    def test_relative_order_preserved_within_categories(self, search_data):
        """
        Test that relative order is preserved within official and informal categories.
        
        **Feature: local-ai-dev-environment**
        **Property 2: Documentation Source Prioritization**
        **Validates: Requirements 5.4**
        
        Given: A list of search results
        When: The prioritization algorithm is applied
        Then: The relative order of official results is preserved
        And: The relative order of informal results is preserved
        """
        results, _, _ = search_data
        
        # Track original order of official and informal results
        original_official = [r for r in results if self._is_official_domain(r.domain)]
        original_informal = [r for r in results if not self._is_official_domain(r.domain)]
        
        # Apply prioritization
        prioritized = self.web_research._prioritize_official_docs(results)
        
        # Extract official and informal from prioritized list
        prioritized_official = [r for r in prioritized if self._is_official_domain(r.domain)]
        prioritized_informal = [r for r in prioritized if not self._is_official_domain(r.domain)]
        
        # Verify relative order preserved (compare URLs as identifiers)
        original_official_urls = [r.url for r in original_official]
        prioritized_official_urls = [r.url for r in prioritized_official]
        assert original_official_urls == prioritized_official_urls, \
            "Relative order of official documentation results should be preserved"
        
        original_informal_urls = [r.url for r in original_informal]
        prioritized_informal_urls = [r.url for r in prioritized_informal]
        assert original_informal_urls == prioritized_informal_urls, \
            "Relative order of informal results should be preserved"
    
    @given(st.lists(search_result(official_domain()), min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_all_official_results_unchanged_when_no_informal(self, results):
        """
        Test that prioritization doesn't change order when all results are official.
        
        **Feature: local-ai-dev-environment**
        **Property 2: Documentation Source Prioritization**
        **Validates: Requirements 5.4**
        
        Given: A list of search results that are all from official documentation
        When: The prioritization algorithm is applied
        Then: The order remains unchanged
        """
        # Apply prioritization
        prioritized = self.web_research._prioritize_official_docs(results)
        
        # Verify order unchanged
        original_urls = [r.url for r in results]
        prioritized_urls = [r.url for r in prioritized]
        assert original_urls == prioritized_urls, \
            "Order should not change when all results are official"
    
    @given(st.lists(search_result(informal_domain()), min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_all_informal_results_unchanged_when_no_official(self, results):
        """
        Test that prioritization doesn't change order when all results are informal.
        
        **Feature: local-ai-dev-environment**
        **Property 2: Documentation Source Prioritization**
        **Validates: Requirements 5.4**
        
        Given: A list of search results that are all from informal sources
        When: The prioritization algorithm is applied
        Then: The order remains unchanged
        """
        # Apply prioritization
        prioritized = self.web_research._prioritize_official_docs(results)
        
        # Verify order unchanged
        original_urls = [r.url for r in results]
        prioritized_urls = [r.url for r in prioritized]
        assert original_urls == prioritized_urls, \
            "Order should not change when all results are informal"
    
    @given(mixed_search_results())
    @settings(max_examples=100)
    def test_prioritization_idempotent(self, search_data):
        """
        Test that applying prioritization multiple times produces the same result.
        
        **Feature: local-ai-dev-environment**
        **Property 2: Documentation Source Prioritization**
        **Validates: Requirements 5.4**
        
        Given: A list of search results
        When: Prioritization is applied multiple times
        Then: Each application produces the same result
        """
        results, _, _ = search_data
        
        # Apply prioritization twice
        prioritized_once = self.web_research._prioritize_official_docs(results)
        prioritized_twice = self.web_research._prioritize_official_docs(prioritized_once)
        
        # Verify idempotence
        urls_once = [r.url for r in prioritized_once]
        urls_twice = [r.url for r in prioritized_twice]
        assert urls_once == urls_twice, \
            "Applying prioritization multiple times should produce the same result"
    
    def _is_official_domain(self, domain: str) -> bool:
        """
        Helper method to check if a domain is official documentation.
        Matches the logic in WebResearchModule._prioritize_official_docs.
        """
        official_domains = self.web_research.OFFICIAL_DOMAINS
        
        # Check full domain and parent domains
        domain_parts = domain.split('.')
        for i in range(len(domain_parts)):
            partial_domain = '.'.join(domain_parts[i:])
            if partial_domain in official_domains:
                return True
        
        # Check if domain ends with any official domain
        for official_domain in official_domains:
            if domain.endswith(official_domain):
                return True
        
        return False


class TestDocumentationSourcePrioritizationEdgeCases:
    """
    Additional edge case tests for documentation source prioritization.
    
    **Feature: local-ai-dev-environment**
    **Property 2: Documentation Source Prioritization**
    """
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.web_research = WebResearchModule()
    
    def test_empty_list_returns_empty(self):
        """Test that prioritization of empty list returns empty list."""
        results = []
        prioritized = self.web_research._prioritize_official_docs(results)
        assert prioritized == [], "Empty list should remain empty"
    
    def test_single_official_result(self):
        """Test single official result remains unchanged."""
        results = [SearchResult(
            title="Python Documentation",
            url="https://docs.python.org/3/",
            snippet="Official Python docs",
            domain="docs.python.org"
        )]
        prioritized = self.web_research._prioritize_official_docs(results)
        assert len(prioritized) == 1
        assert prioritized[0].url == results[0].url
    
    def test_single_informal_result(self):
        """Test single informal result remains unchanged."""
        results = [SearchResult(
            title="Stack Overflow Answer",
            url="https://stackoverflow.com/questions/123",
            snippet="Some answer",
            domain="stackoverflow.com"
        )]
        prioritized = self.web_research._prioritize_official_docs(results)
        assert len(prioritized) == 1
        assert prioritized[0].url == results[0].url
    
    def test_subdomain_of_official_recognized(self):
        """Test that subdomains of official domains are recognized as official."""
        results = [
            SearchResult(
                title="Informal",
                url="https://stackoverflow.com/q/1",
                snippet="SO",
                domain="stackoverflow.com"
            ),
            SearchResult(
                title="Official Subdomain",
                url="https://guides.python.org/tutorial",
                snippet="Python guide",
                domain="guides.python.org"
            )
        ]
        prioritized = self.web_research._prioritize_official_docs(results)
        
        # The python.org subdomain should come first
        assert prioritized[0].domain == "guides.python.org"
        assert prioritized[1].domain == "stackoverflow.com"
    
    def test_similar_domain_names_handled_correctly(self):
        """Test that similar but non-official domains are not mistakenly classified."""
        results = [
            SearchResult(
                title="Fake Python",
                url="https://python.example.com/docs",
                snippet="Fake docs",
                domain="python.example.com"
            ),
            SearchResult(
                title="Real Python Docs",
                url="https://docs.python.org/3/",
                snippet="Real docs",
                domain="docs.python.org"
            )
        ]
        prioritized = self.web_research._prioritize_official_docs(results)
        
        # Real python.org should come first
        assert prioritized[0].domain == "docs.python.org"
        assert prioritized[1].domain == "python.example.com"
