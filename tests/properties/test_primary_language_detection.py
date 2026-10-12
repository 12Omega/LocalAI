"""Property-based tests for primary language detection.

This module tests Property 11: Primary Language Detection
**Validates: Requirements 11.4**

The property ensures that the primary language is correctly identified as the
programming language with the most source files in the project.
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, List, Tuple

from src.context.context_manager import ContextManager
from src.core.models import SystemConfig, LLMConfig, FileTree, LanguageStack


# Language extension mappings from ASTParser
LANGUAGE_EXTENSIONS = {
    'Python': ['.py'],
    'JavaScript': ['.js'],
    'TypeScript': ['.ts'],
    'Java': ['.java'],
    'Go': ['.go'],
    'Rust': ['.rs'],
    'C++': ['.cpp', '.cc', '.cxx'],
}

# All supported languages
SUPPORTED_LANGUAGES = list(LANGUAGE_EXTENSIONS.keys())


@st.composite
def language_file_distribution(draw):
    """Generate a distribution of files across multiple languages.
    
    Returns:
        Dict mapping language names to number of files to create
    """
    # Select 1-5 languages to include in the project
    num_languages = draw(st.integers(min_value=1, max_value=min(5, len(SUPPORTED_LANGUAGES))))
    selected_languages = draw(st.lists(
        st.sampled_from(SUPPORTED_LANGUAGES),
        min_size=num_languages,
        max_size=num_languages,
        unique=True
    ))
    
    # Assign file counts to each language (1-15 files per language)
    distribution = {}
    for language in selected_languages:
        num_files = draw(st.integers(min_value=1, max_value=15))
        distribution[language] = num_files
    
    return distribution


@st.composite
def balanced_language_distribution(draw):
    """Generate a distribution where two or more languages have the same count (tie scenario).
    
    Returns:
        Dict mapping language names to number of files to create
    """
    # Select 2-4 languages
    num_languages = draw(st.integers(min_value=2, max_value=4))
    selected_languages = draw(st.lists(
        st.sampled_from(SUPPORTED_LANGUAGES),
        min_size=num_languages,
        max_size=num_languages,
        unique=True
    ))
    
    # Create a tie - assign the same count to at least 2 languages
    tie_count = draw(st.integers(min_value=3, max_value=10))
    
    distribution = {}
    # First two languages get the same count (creating a tie)
    distribution[selected_languages[0]] = tie_count
    distribution[selected_languages[1]] = tie_count
    
    # Remaining languages get smaller counts
    for i in range(2, len(selected_languages)):
        distribution[selected_languages[i]] = draw(st.integers(min_value=1, max_value=tie_count - 1))
    
    return distribution


@st.composite
def single_language_distribution(draw):
    """Generate a project with only one language.
    
    Returns:
        Dict mapping language name to number of files to create
    """
    language = draw(st.sampled_from(SUPPORTED_LANGUAGES))
    num_files = draw(st.integers(min_value=1, max_value=20))
    return {language: num_files}


@st.composite
def filename_strategy(draw, language: str, index: int):
    """Generate a valid filename for a given language.
    
    Args:
        language: Programming language name
        index: File index for uniqueness
        
    Returns:
        Filename with appropriate extension
    """
    # Base name patterns
    prefixes = ['module', 'service', 'handler', 'utils', 'helper', 'model', 'controller', 'test']
    prefix = draw(st.sampled_from(prefixes))
    
    # Get appropriate extension for the language
    extensions = LANGUAGE_EXTENSIONS[language]
    extension = draw(st.sampled_from(extensions))
    
    # Create unique filename
    return f"{prefix}_{index}{extension}"


def generate_file_content(language: str, filename: str) -> str:
    """Generate minimal valid code content for a file.
    
    Args:
        language: Programming language name
        filename: Name of the file
        
    Returns:
        String containing valid code for the language
    """
    if language == 'Python':
        return f'''"""Module: {filename}"""

def sample_function():
    """A sample function."""
    pass

class SampleClass:
    """A sample class."""
    def __init__(self):
        pass
'''
    elif language == 'JavaScript':
        return f'''// Module: {filename}

function sampleFunction() {{
    return true;
}}

class SampleClass {{
    constructor() {{}}
}}

module.exports = {{ sampleFunction, SampleClass }};
'''
    elif language == 'TypeScript':
        return f'''// Module: {filename}

function sampleFunction(): boolean {{
    return true;
}}

class SampleClass {{
    constructor() {{}}
}}

export {{ sampleFunction, SampleClass }};
'''
    elif language == 'Java':
        class_name = Path(filename).stem.capitalize()
        return f'''// Module: {filename}

public class {class_name} {{
    public void sampleMethod() {{
        // Implementation
    }}
    
    public static void main(String[] args) {{
        System.out.println("Sample");
    }}
}}
'''
    elif language == 'Go':
        return f'''// Module: {filename}
package main

func sampleFunction() bool {{
    return true
}}

type SampleStruct struct {{
    field string
}}
'''
    elif language == 'Rust':
        return f'''// Module: {filename}

fn sample_function() -> bool {{
    true
}}

struct SampleStruct {{
    field: String,
}}

impl SampleStruct {{
    fn new() -> Self {{
        SampleStruct {{ field: String::new() }}
    }}
}}
'''
    elif language == 'C++':
        return f'''// Module: {filename}

#include <iostream>

class SampleClass {{
public:
    void sampleMethod() {{
        // Implementation
    }}
}};

int main() {{
    return 0;
}}
'''
    else:
        return f'// Default content for {filename}\n'


@pytest.mark.property
class TestPrimaryLanguageDetection:
    """Property-based tests for primary language detection.
    
    Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
    """
    
    def setup_method(self):
        """Create a temporary directory for test projects."""
        self.test_dir = tempfile.mkdtemp(prefix='primary_lang_test_')
        
        # Create system config
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model"
        )
        self.config = SystemConfig(
            llm=llm_config,
            project_root=self.test_dir,
            log_level="info"
        )
        
        self.context_manager = ContextManager(self.config)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _clean_test_directory(self):
        """Clean the test directory before writing new files."""
        for item in os.listdir(self.test_dir):
            item_path = os.path.join(self.test_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    
    def _create_project_files(self, distribution: Dict[str, int]) -> Dict[str, int]:
        """Create project files based on language distribution.
        
        Args:
            distribution: Dict mapping language names to file counts
            
        Returns:
            Dict mapping language names to actual file counts created
        """
        self._clean_test_directory()
        
        actual_counts = {}
        
        for language, count in distribution.items():
            actual_counts[language] = 0
            
            for i in range(count):
                # Generate filename
                filename = f"{language.lower()}_{i}_{uuid.uuid4().hex[:6]}"
                extensions = LANGUAGE_EXTENSIONS[language]
                extension = extensions[0]  # Use first extension as default
                filename = f"{filename}{extension}"
                
                # Generate file content
                content = generate_file_content(language, filename)
                
                # Write file
                file_path = Path(self.test_dir) / filename
                file_path.write_text(content, encoding='utf-8')
                
                actual_counts[language] += 1
        
        return actual_counts
    
    def _get_expected_primary_language(self, distribution: Dict[str, int]) -> str:
        """Determine expected primary language from distribution.
        
        Args:
            distribution: Dict mapping language names to file counts
            
        Returns:
            Expected primary language (most common, first alphabetically on tie)
        """
        if not distribution:
            return None
        
        # Find maximum count
        max_count = max(distribution.values())
        
        # Get all languages with max count
        max_languages = [lang for lang, count in distribution.items() if count == max_count]
        
        # Sort alphabetically and return first (tie-breaking rule)
        return sorted(max_languages)[0]
    
    @given(distribution=language_file_distribution())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_primary_language_is_most_common(self, distribution):
        """Test that primary language is the one with most source files.
        
        **Validates: Requirements 11.4**
        
        Property: The primary_language field in LanguageStack should be set to
        the programming language that has the most source files in the project.
        When there's a tie, any of the tied languages is acceptable.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # Find the maximum file count
        max_count = max(actual_counts.values())
        
        # Get all languages with the maximum count
        languages_with_max_count = [lang for lang, count in actual_counts.items() if count == max_count]
        
        # Primary language must be one of the languages with max count
        assert language_stack.primary_language in languages_with_max_count, (
            f"Primary language not among languages with max count:\n"
            f"Primary: {language_stack.primary_language}\n"
            f"Languages with max count ({max_count} files): {languages_with_max_count}\n"
            f"File distribution: {actual_counts}"
        )
    
    @given(distribution=language_file_distribution())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_detected_languages_match_files(self, distribution):
        """Test that all languages with files are detected.
        
        **Validates: Requirements 11.4**
        
        Property: The languages list should include all languages that have
        at least one source file in the project.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # Get expected languages (all with count > 0)
        expected_languages = set(lang for lang, count in actual_counts.items() if count > 0)
        detected_languages = set(language_stack.languages)
        
        # Verify all expected languages are detected
        missing = expected_languages - detected_languages
        assert len(missing) == 0, (
            f"Languages missing from detection: {missing}\n"
            f"Expected: {expected_languages}\n"
            f"Detected: {detected_languages}\n"
            f"File distribution: {actual_counts}"
        )
    
    @given(distribution=language_file_distribution())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_languages_sorted_by_frequency(self, distribution):
        """Test that languages list is sorted by file count (most common first).
        
        **Validates: Requirements 11.4**
        
        Property: The languages list should be ordered from most common to
        least common based on file counts.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # Verify languages are sorted by frequency
        detected_languages = language_stack.languages
        
        # Check that each language has count >= next language
        for i in range(len(detected_languages) - 1):
            current_lang = detected_languages[i]
            next_lang = detected_languages[i + 1]
            
            current_count = actual_counts.get(current_lang, 0)
            next_count = actual_counts.get(next_lang, 0)
            
            assert current_count >= next_count, (
                f"Languages not sorted by frequency:\n"
                f"{current_lang} ({current_count} files) appears before "
                f"{next_lang} ({next_count} files)\n"
                f"Full order: {detected_languages}\n"
                f"File distribution: {actual_counts}"
            )
    
    @given(distribution=single_language_distribution())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_single_language_project(self, distribution):
        """Test primary language detection with only one language.
        
        **Validates: Requirements 11.4**
        
        Property: For a project with only one language, that language should
        be detected as the primary language.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Verify we have exactly one language
        assume(len(actual_counts) == 1)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # The only language should be primary
        expected_language = list(actual_counts.keys())[0]
        
        assert language_stack.primary_language == expected_language, (
            f"Single language not detected as primary:\n"
            f"Expected: {expected_language}\n"
            f"Actual: {language_stack.primary_language}"
        )
        
        # Languages list should contain exactly one language
        assert len(language_stack.languages) == 1, (
            f"Expected 1 language, found {len(language_stack.languages)}: {language_stack.languages}"
        )
        
        assert language_stack.languages[0] == expected_language
    
    @given(distribution=balanced_language_distribution())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_tie_breaking_behavior(self, distribution):
        """Test primary language selection when multiple languages have same count.
        
        **Validates: Requirements 11.4**
        
        Property: When multiple languages have the same file count (tied for most common),
        one of them is selected as primary (implementation-defined tie-breaking).
        The primary language must be one of the tied languages.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Find languages with maximum count
        max_count = max(actual_counts.values())
        tied_languages = [lang for lang, count in actual_counts.items() if count == max_count]
        
        # Verify we have a tie scenario
        assume(len(tied_languages) >= 2)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # Primary language must be one of the tied languages
        assert language_stack.primary_language in tied_languages, (
            f"Primary language not among tied languages:\n"
            f"Tied languages: {tied_languages} (all with {max_count} files)\n"
            f"Actual primary: {language_stack.primary_language}\n"
            f"File distribution: {actual_counts}"
        )
        
        # All tied languages should appear at the beginning of the languages list
        # (in some order, as they all have the same count)
        for tied_lang in tied_languages:
            assert tied_lang in language_stack.languages[:len(tied_languages)], (
                f"Tied language {tied_lang} not at beginning of languages list:\n"
                f"Languages list: {language_stack.languages}\n"
                f"Tied languages: {tied_languages}"
            )
    
    def test_empty_project_no_primary_language(self):
        """Test that empty project has no primary language.
        
        **Validates: Requirements 11.4**
        
        Property: A project with no source files should have primary_language set to None.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Clean directory (no files)
        self._clean_test_directory()
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # Should have no primary language
        assert language_stack.primary_language is None, (
            f"Empty project should have no primary language, "
            f"but got: {language_stack.primary_language}"
        )
        
        # Languages list should be empty
        assert len(language_stack.languages) == 0, (
            f"Empty project should have no languages, "
            f"but got: {language_stack.languages}"
        )
    
    @given(
        dominant_language=st.sampled_from(SUPPORTED_LANGUAGES),
        dominant_count=st.integers(min_value=10, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_dominant_language_with_minority_files(self, dominant_language, dominant_count):
        """Test detection when one language dominates with a few minority language files.
        
        **Validates: Requirements 11.4**
        
        Property: When one language has significantly more files than others,
        it should be detected as the primary language.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create distribution with dominant language and 1-2 minority languages
        distribution = {dominant_language: dominant_count}
        
        # Add 1-2 minority languages with fewer files
        other_languages = [lang for lang in SUPPORTED_LANGUAGES if lang != dominant_language]
        if other_languages:
            minority_lang1 = other_languages[0]
            distribution[minority_lang1] = max(1, dominant_count // 4)
            
            if len(other_languages) > 1:
                minority_lang2 = other_languages[1]
                distribution[minority_lang2] = max(1, dominant_count // 5)
        
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # Dominant language should be primary
        assert language_stack.primary_language == dominant_language, (
            f"Dominant language not detected as primary:\n"
            f"Expected: {dominant_language} ({actual_counts[dominant_language]} files)\n"
            f"Actual: {language_stack.primary_language}\n"
            f"File distribution: {actual_counts}"
        )
        
        # Dominant language should be first in languages list
        assert language_stack.languages[0] == dominant_language, (
            f"Dominant language not first in list:\n"
            f"Languages: {language_stack.languages}\n"
            f"File distribution: {actual_counts}"
        )
    
    @given(distribution=language_file_distribution())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_primary_language_in_languages_list(self, distribution):
        """Test that primary language always appears in the languages list.
        
        **Validates: Requirements 11.4**
        
        Property: The primary_language should always be present in the languages list.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # If there's a primary language, it must be in the languages list
        if language_stack.primary_language:
            assert language_stack.primary_language in language_stack.languages, (
                f"Primary language not in languages list:\n"
                f"Primary: {language_stack.primary_language}\n"
                f"Languages: {language_stack.languages}\n"
                f"File distribution: {actual_counts}"
            )
            
            # Primary language should be the first in the list
            assert language_stack.languages[0] == language_stack.primary_language, (
                f"Primary language not first in languages list:\n"
                f"Primary: {language_stack.primary_language}\n"
                f"Languages: {language_stack.languages}\n"
                f"File distribution: {actual_counts}"
            )
    
    @given(
        lang1=st.sampled_from(SUPPORTED_LANGUAGES),
        lang2=st.sampled_from(SUPPORTED_LANGUAGES),
        count1=st.integers(min_value=5, max_value=10),
        count2=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_two_language_project(self, lang1, lang2, count1, count2):
        """Test primary language detection with exactly two languages.
        
        **Validates: Requirements 11.4**
        
        Property: In a two-language project, the language with more files
        should be the primary language.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Ensure languages are different
        assume(lang1 != lang2)
        
        # Ensure counts are different (no tie)
        assume(count1 != count2)
        
        # Create distribution
        distribution = {lang1: count1, lang2: count2}
        
        # Create project files
        actual_counts = self._create_project_files(distribution)
        
        # Scan project
        context = self.context_manager.scan_project(self.test_dir)
        language_stack = context.language_stack
        
        # Determine which should be primary (most files)
        expected_primary = lang1 if count1 > count2 else lang2
        
        assert language_stack.primary_language == expected_primary, (
            f"Primary language incorrect in two-language project:\n"
            f"Expected: {expected_primary}\n"
            f"Actual: {language_stack.primary_language}\n"
            f"File distribution: {actual_counts}"
        )
        
        # Both languages should be in the list
        assert len(language_stack.languages) == 2, (
            f"Expected 2 languages, found {len(language_stack.languages)}: {language_stack.languages}"
        )
