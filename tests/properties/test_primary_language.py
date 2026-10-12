"""Property-based tests for primary language detection.

This module tests Property 11: Primary Language Detection
**Validates: Requirements 11.4**

The property ensures that the detected primary language is the one with the most
source files in the project, based on standard file extensions.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.context.context_manager import ContextManager
from src.core.models import SystemConfig, LLMConfig, FileTree


# Language to extension mapping (matches what AST parser uses)
LANGUAGE_EXTENSIONS = {
    'Python': ['.py'],
    'JavaScript': ['.js'],
    'TypeScript': ['.ts'],
    'Java': ['.java'],
    'Go': ['.go'],
    'Rust': ['.rs'],
    'C++': ['.cpp', '.hpp', '.h', '.cxx'],
}


@st.composite
def valid_filename_for_language(draw, language):
    """Generate valid file names for a specific language.
    
    Args:
        language: Programming language name (e.g., 'Python', 'JavaScript')
        
    Returns:
        A filename with appropriate extension for the language
    """
    # Generate base filename
    length = draw(st.integers(min_value=3, max_value=20))
    chars = st.sampled_from('abcdefghijklmnopqrstuvwxyz0123456789_')
    name = ''.join(draw(st.lists(chars, min_size=3, max_size=length)))
    
    # Get appropriate extension for language
    extensions = LANGUAGE_EXTENSIONS.get(language, ['.txt'])
    extension = draw(st.sampled_from(extensions))
    
    return name + extension


@st.composite
def language_distribution(draw):
    """Generate a distribution of file counts across multiple languages.
    
    Returns:
        Dictionary mapping language names to file counts, where one language
        has more files than all others (the expected primary language).
    """
    # Choose 2-4 languages to include
    num_languages = draw(st.integers(min_value=2, max_value=4))
    available_languages = list(LANGUAGE_EXTENSIONS.keys())
    selected_languages = draw(st.lists(
        st.sampled_from(available_languages),
        min_size=num_languages,
        max_size=num_languages,
        unique=True
    ))
    
    # Determine which language should be primary (most files)
    primary_language = draw(st.sampled_from(selected_languages))
    
    # Generate file counts ensuring primary has the most
    distribution = {}
    primary_count = draw(st.integers(min_value=3, max_value=15))
    
    for lang in selected_languages:
        if lang == primary_language:
            distribution[lang] = primary_count
        else:
            # Other languages have fewer files than primary
            distribution[lang] = draw(st.integers(min_value=1, max_value=primary_count - 1))
    
    return {
        'distribution': distribution,
        'expected_primary': primary_language
    }


@st.composite
def project_structure(draw):
    """Generate a complete project structure with various language files.
    
    Returns:
        Dictionary with:
        - 'files': List of file info dicts with 'path', 'language', 'content'
        - 'expected_primary': The language that should be detected as primary
        - 'distribution': Count of files per language
    """
    # Generate language distribution
    lang_dist = draw(language_distribution())
    distribution = lang_dist['distribution']
    expected_primary = lang_dist['expected_primary']
    
    # Generate directories (0-3)
    num_dirs = draw(st.integers(min_value=0, max_value=3))
    directories = []
    if num_dirs > 0:
        for i in range(num_dirs):
            dir_name = draw(st.sampled_from([
                'src', 'lib', 'app', 'core', 'utils', 'services', 'modules'
            ]))
            directories.append(f"{dir_name}_{i}")
    
    # Generate files according to distribution
    files = []
    used_paths = set()  # Track used file paths to ensure uniqueness
    
    for language, count in distribution.items():
        for i in range(count):
            # Generate unique file path
            max_attempts = 10
            for attempt in range(max_attempts):
                # Randomly place in root or subdirectory
                if directories and draw(st.booleans()):
                    dir_name = draw(st.sampled_from(directories))
                    file_path = f"{dir_name}/{draw(valid_filename_for_language(language))}"
                else:
                    file_path = draw(valid_filename_for_language(language))
                
                # Ensure uniqueness by adding index if needed
                if file_path in used_paths:
                    # Add language-specific counter to make unique
                    base_name = os.path.splitext(file_path)[0]
                    ext = os.path.splitext(file_path)[1]
                    file_path = f"{base_name}_{i}{ext}"
                
                # If still not unique after attempts, force uniqueness
                if file_path not in used_paths:
                    used_paths.add(file_path)
                    break
                else:
                    # Last resort: use UUID
                    import uuid
                    base_name = os.path.splitext(file_path)[0]
                    ext = os.path.splitext(file_path)[1]
                    file_path = f"{base_name}_{uuid.uuid4().hex[:6]}{ext}"
                    used_paths.add(file_path)
                    break
            
            # Generate minimal content (not important for this property)
            content = draw(st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'),
                    max_codepoint=127
                ),
                min_size=0,
                max_size=100
            ))
            
            files.append({
                'path': file_path,
                'language': language,
                'content': content
            })
    
    return {
        'files': files,
        'expected_primary': expected_primary,
        'distribution': distribution
    }


@pytest.mark.property
class TestPrimaryLanguageDetection:
    """Property-based tests for primary language detection.
    
    Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
    """
    
    def _create_project(self, structure):
        """Create a project structure in a fresh temp directory.
        
        Args:
            structure: Dictionary with 'files' list
            
        Returns:
            Tuple of (temp_dir, created_files, config)
        """
        temp_dir = tempfile.mkdtemp(prefix="test_primary_lang_")
        created_files = []
        
        try:
            for file_info in structure['files']:
                file_path = os.path.join(temp_dir, file_info['path'])
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info['content'])
                
                created_files.append(file_path)
            
            # Create config for this temp directory
            config = SystemConfig(
                llm=LLMConfig(
                    endpoint="http://localhost:11434",
                    model_name="codellama:13b"
                ),
                project_root=temp_dir,
                excluded_directories=['node_modules', '.git', '__pycache__', 'venv']
            )
            
            return temp_dir, created_files, config
        except:
            # Cleanup on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise
    
    def _cleanup_project(self, temp_dir):
        """Clean up a temporary project directory.
        
        Args:
            temp_dir: Path to temporary directory to remove
        """
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                # On Windows, sometimes files are still in use
                import time
                time.sleep(0.1)
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass  # Best effort cleanup
    
    @given(structure=project_structure())
    @settings(max_examples=100, deadline=None)
    def test_primary_language_is_most_common(self, structure):
        """Test that primary language is the one with most source files.
        
        **Validates: Requirements 11.4**
        
        Property: For any project directory, the detected primary language SHALL be
        the language with the most source files in the project, where source files
        are identified by standard file extensions (.py, .js, .ts, .java, .go, .rs,
        .cpp, etc.).
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create the project structure
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Create ContextManager and detect language stack
            context_manager = ContextManager(config)
            language_stack = context_manager.detect_language_stack(temp_dir)
            
            # Verify primary language matches expected
            expected_primary = structure['expected_primary']
            actual_primary = language_stack.primary_language
            
            assert actual_primary == expected_primary, (
                f"Expected primary language '{expected_primary}' but got '{actual_primary}'.\n"
                f"Distribution: {structure['distribution']}\n"
                f"Detected languages: {language_stack.languages}"
            )
        finally:
            self._cleanup_project(temp_dir)
    
    @given(structure=project_structure())
    @settings(max_examples=100, deadline=None)
    def test_primary_language_in_detected_languages(self, structure):
        """Test that primary language is included in the list of detected languages.
        
        **Validates: Requirements 11.4**
        
        Property: The primary language must be present in the languages list.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create the project structure
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Create ContextManager and detect language stack
            context_manager = ContextManager(config)
            language_stack = context_manager.detect_language_stack(temp_dir)
            
            # Verify primary language is in languages list
            assert language_stack.primary_language is not None, (
                "Primary language should not be None when files are present"
            )
            
            assert language_stack.primary_language in language_stack.languages, (
                f"Primary language '{language_stack.primary_language}' not in languages list: "
                f"{language_stack.languages}"
            )
        finally:
            self._cleanup_project(temp_dir)
    
    @given(structure=project_structure())
    @settings(max_examples=100, deadline=None)
    def test_primary_language_is_first_in_list(self, structure):
        """Test that primary language is first in the languages list (sorted by frequency).
        
        **Validates: Requirements 11.4**
        
        Property: The languages list should be sorted by frequency, with primary
        language (most files) appearing first.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create the project structure
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Create ContextManager and detect language stack
            context_manager = ContextManager(config)
            language_stack = context_manager.detect_language_stack(temp_dir)
            
            # Verify languages list is not empty
            assume(len(language_stack.languages) > 0)
            
            # Verify primary language is the first in the list
            assert language_stack.languages[0] == language_stack.primary_language, (
                f"First language in list '{language_stack.languages[0]}' should match "
                f"primary language '{language_stack.primary_language}'"
            )
        finally:
            self._cleanup_project(temp_dir)
    
    @given(structure=project_structure())
    @settings(max_examples=100, deadline=None)
    def test_all_languages_detected(self, structure):
        """Test that all languages present in the project are detected.
        
        **Validates: Requirements 11.4, 11.5**
        
        Property: All languages with source files in the project should be detected
        and included in the languages list.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create the project structure
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Create ContextManager and detect language stack
            context_manager = ContextManager(config)
            language_stack = context_manager.detect_language_stack(temp_dir)
            
            # Get expected languages from distribution
            expected_languages = set(structure['distribution'].keys())
            detected_languages = set(language_stack.languages)
            
            # Verify all expected languages are detected
            assert expected_languages.issubset(detected_languages), (
                f"Not all languages detected.\n"
                f"Expected: {expected_languages}\n"
                f"Detected: {detected_languages}\n"
                f"Missing: {expected_languages - detected_languages}"
            )
        finally:
            self._cleanup_project(temp_dir)
    
    @given(structure=project_structure())
    @settings(max_examples=100, deadline=None)
    def test_language_count_consistency(self, structure):
        """Test that detected languages match the actual file distribution.
        
        **Validates: Requirements 11.4**
        
        Property: The number of detected languages should match the number of
        unique languages in the file distribution.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create the project structure
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Create ContextManager and detect language stack
            context_manager = ContextManager(config)
            language_stack = context_manager.detect_language_stack(temp_dir)
            
            # Get expected language count
            expected_count = len(structure['distribution'])
            actual_count = len(language_stack.languages)
            
            assert actual_count == expected_count, (
                f"Expected {expected_count} languages but detected {actual_count}.\n"
                f"Expected languages: {list(structure['distribution'].keys())}\n"
                f"Detected languages: {language_stack.languages}"
            )
        finally:
            self._cleanup_project(temp_dir)
    
    @given(
        primary_lang=st.sampled_from(['Python', 'JavaScript', 'TypeScript', 'Java']),
        primary_count=st.integers(min_value=5, max_value=20),
        secondary_count=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=100, deadline=None)
    def test_clear_primary_language_dominance(self, primary_lang, primary_count, secondary_count):
        """Test detection when one language clearly dominates with more files.
        
        **Validates: Requirements 11.4**
        
        Property: When one language has significantly more files than others,
        it should always be detected as the primary language.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Ensure primary has more files
        assume(primary_count > secondary_count)
        
        # Create files for primary language
        files = []
        for i in range(primary_count):
            ext = LANGUAGE_EXTENSIONS[primary_lang][0]
            files.append({
                'path': f'file_{i}{ext}',
                'language': primary_lang,
                'content': f'// Content {i}'
            })
        
        # Add secondary language (Python if primary is not Python, else JavaScript)
        secondary_lang = 'JavaScript' if primary_lang == 'Python' else 'Python'
        for i in range(secondary_count):
            ext = LANGUAGE_EXTENSIONS[secondary_lang][0]
            files.append({
                'path': f'secondary_{i}{ext}',
                'language': secondary_lang,
                'content': f'// Secondary content {i}'
            })
        
        structure = {
            'files': files,
            'expected_primary': primary_lang,
            'distribution': {primary_lang: primary_count, secondary_lang: secondary_count}
        }
        
        # Create the project
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Detect language stack
            context_manager = ContextManager(config)
            language_stack = context_manager.detect_language_stack(temp_dir)
            
            # Verify primary language is detected correctly
            assert language_stack.primary_language == primary_lang, (
                f"Expected primary language '{primary_lang}' (count: {primary_count}) "
                f"but got '{language_stack.primary_language}'. "
                f"Secondary language: '{secondary_lang}' (count: {secondary_count})"
            )
        finally:
            self._cleanup_project(temp_dir)
    
    @given(structure=project_structure())
    @settings(max_examples=100, deadline=None)
    def test_file_tree_consistency(self, structure):
        """Test that file tree and language detection are consistent.
        
        **Validates: Requirements 11.4**
        
        Property: The files counted for language detection should match the files
        present in the file tree.
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create the project structure
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Build file tree
            context_manager = ContextManager(config)
            file_tree = context_manager._build_file_tree(temp_dir)
            
            # Detect language stack using the same file tree
            language_stack = context_manager.detect_language_stack(temp_dir, file_tree)
            
            # Count source files in file tree
            source_files = []
            for file_path in file_tree.files:
                ext = Path(file_path).suffix.lower()
                # Check if this is a recognized source file extension
                for lang, exts in LANGUAGE_EXTENSIONS.items():
                    if ext in exts:
                        source_files.append(file_path)
                        break
            
            # Count expected files from structure
            expected_source_count = len(structure['files'])
            
            assert len(source_files) == expected_source_count, (
                f"File tree has {len(source_files)} source files but expected {expected_source_count}.\n"
                f"File tree files: {file_tree.files}\n"
                f"Source files: {source_files}"
            )
        finally:
            self._cleanup_project(temp_dir)
    
    @given(
        lang1=st.sampled_from(['Python', 'JavaScript', 'TypeScript']),
        lang2=st.sampled_from(['Java', 'Go', 'Rust']),
        count=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_tie_breaking_alphabetical(self, lang1, lang2, count):
        """Test behavior when two languages have equal file counts.
        
        **Validates: Requirements 11.4**
        
        Property: When multiple languages have the same maximum file count,
        the primary language should be consistently determined (implementation
        may use alphabetical order or first-seen order).
        
        Tag: Feature: local-ai-dev-environment, Property 11: Primary Language Detection
        """
        # Create equal number of files for both languages
        files = []
        
        for i in range(count):
            ext1 = LANGUAGE_EXTENSIONS[lang1][0]
            files.append({
                'path': f'file1_{i}{ext1}',
                'language': lang1,
                'content': f'// Content {i}'
            })
            
            ext2 = LANGUAGE_EXTENSIONS[lang2][0]
            files.append({
                'path': f'file2_{i}{ext2}',
                'language': lang2,
                'content': f'// Content {i}'
            })
        
        structure = {
            'files': files,
            'expected_primary': None,  # Tie case
            'distribution': {lang1: count, lang2: count}
        }
        
        # Create the project
        temp_dir, _, config = self._create_project(structure)
        
        try:
            # Detect language stack
            context_manager = ContextManager(config)
            language_stack = context_manager.detect_language_stack(temp_dir)
            
            # Verify a primary language is selected (even in tie case)
            assert language_stack.primary_language is not None, (
                "Primary language should be selected even when counts are tied"
            )
            
            # Verify the primary language is one of the tied languages
            assert language_stack.primary_language in [lang1, lang2], (
                f"Primary language '{language_stack.primary_language}' should be one of "
                f"the tied languages: {lang1} or {lang2}"
            )
            
            # Verify both languages are detected
            assert lang1 in language_stack.languages, f"{lang1} should be detected"
            assert lang2 in language_stack.languages, f"{lang2} should be detected"
        finally:
            self._cleanup_project(temp_dir)
