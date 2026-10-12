"""Property-based tests for framework detection consistency.

This module tests Property 4: Framework Detection Consistency
**Validates: Requirements 6.3**

The property ensures that detected frameworks match the marker files present
in the project structure.
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
import sys

# Add src to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from hypothesis import given, strategies as st, settings, assume

from context.context_manager import ContextManager
from core.models import SystemConfig, LLMConfig, FileTree


# Strategy for generating framework marker file configurations
@st.composite
def framework_marker_config(draw):
    """Generate a configuration of framework markers to create.
    
    Returns a dictionary mapping framework names to whether they should
    be present in the test project.
    """
    # Available frameworks from ContextManager.FRAMEWORK_MARKERS
    frameworks = {
        'Flask': ['flask'],
        'Django': ['django', 'manage.py'],
        'FastAPI': ['fastapi'],
        'React': ['react', 'package.json'],
        'Vue': ['vue', 'package.json'],
        'Angular': ['@angular/core', 'angular.json'],
        'Express': ['express', 'package.json'],
        'Spring': ['pom.xml', 'spring'],
        'Gin': ['gin-gonic/gin'],
        'Actix': ['actix-web'],
    }
    
    # Randomly select which frameworks to include
    selected = {}
    for framework in frameworks.keys():
        include = draw(st.booleans())
        selected[framework] = include
    
    # Ensure at least one framework is selected
    if not any(selected.values()):
        # Select at least one framework randomly
        random_framework = draw(st.sampled_from(list(frameworks.keys())))
        selected[random_framework] = True
    
    return selected


# Strategy for generating project directory names
@st.composite
def project_dir_name(draw):
    """Generate valid directory names for test projects."""
    prefix = draw(st.sampled_from(['project', 'test', 'app', 'src', 'demo']))
    suffix = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=4, max_size=8))
    return f"{prefix}_{suffix}"


@pytest.mark.property
class TestFrameworkDetectionConsistency:
    """Property-based tests for framework detection consistency.
    
    Tag: Feature: local-ai-dev-environment, Property 4: Framework Detection Consistency
    """
    
    def setup_method(self):
        """Create a temporary directory for each test method."""
        # This will be created fresh for each hypothesis example
        self.temp_base_dir = tempfile.mkdtemp()
        # Initialize temp_dir for tests that use it directly
        self.temp_dir = tempfile.mkdtemp(dir=self.temp_base_dir)
        
        # Create a minimal SystemConfig for ContextManager
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root=self.temp_dir,
            excluded_directories=[]
        )
        self.context_manager = ContextManager(config)
    
    def teardown_method(self):
        """Clean up temporary directory after each test method."""
        if os.path.exists(self.temp_base_dir):
            shutil.rmtree(self.temp_base_dir)
    
    def _create_fresh_test_dir(self):
        """Create a fresh temporary directory for each hypothesis example."""
        # Create a unique subdirectory for this example
        example_dir = os.path.join(self.temp_base_dir, str(uuid.uuid4()))
        os.makedirs(example_dir, exist_ok=True)
        
        # Create a minimal SystemConfig for ContextManager
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root=example_dir,
            excluded_directories=[]
        )
        context_manager = ContextManager(config)
        
        return example_dir, context_manager
    
    def _create_marker_files(self, temp_dir: str, framework_config: dict) -> set:
        """Create marker files based on framework configuration.
        
        Args:
            temp_dir: Temporary directory to create files in
            framework_config: Dict mapping framework names to whether they should be included
            
        Returns:
            Set of framework names that should be detected
        """
        expected_frameworks = set()
        
        # Framework marker definitions from ContextManager
        marker_definitions = {
            'Flask': ['flask'],
            'Django': ['django', 'manage.py'],
            'FastAPI': ['fastapi'],
            'React': ['react', 'package.json'],
            'Vue': ['vue', 'package.json'],
            'Angular': ['@angular/core', 'angular.json'],
            'Express': ['express', 'package.json'],
            'Spring': ['pom.xml', 'spring'],
            'Gin': ['gin-gonic/gin'],
            'Actix': ['actix-web'],
        }
        
        for framework, should_include in framework_config.items():
            if should_include:
                expected_frameworks.add(framework)
                markers = marker_definitions[framework]
                
                for marker in markers:
                    # Handle different marker types
                    if marker == 'manage.py':
                        # Create Django manage.py file
                        filepath = os.path.join(temp_dir, 'manage.py')
                        with open(filepath, 'w') as f:
                            f.write('#!/usr/bin/env python\n# Django manage.py\n')
                    
                    elif marker == 'package.json':
                        # Create or update package.json with dependencies
                        pkg_path = os.path.join(temp_dir, 'package.json')
                        if os.path.exists(pkg_path):
                            # Read existing content and add to it
                            with open(pkg_path, 'r') as f:
                                import json
                                try:
                                    pkg_data = json.load(f)
                                except:
                                    pkg_data = {"dependencies": {}}
                        else:
                            pkg_data = {"dependencies": {}}
                        
                        # Add framework-specific dependency
                        if framework == 'React':
                            pkg_data['dependencies']['react'] = '^18.0.0'
                        elif framework == 'Vue':
                            pkg_data['dependencies']['vue'] = '^3.0.0'
                        elif framework == 'Express':
                            pkg_data['dependencies']['express'] = '^4.18.0'
                        
                        with open(pkg_path, 'w') as f:
                            import json
                            json.dump(pkg_data, f)
                    
                    elif marker == 'angular.json':
                        # Create Angular configuration file
                        filepath = os.path.join(temp_dir, 'angular.json')
                        with open(filepath, 'w') as f:
                            f.write('{\n  "version": 1,\n  "projects": {}\n}\n')
                    
                    elif marker == 'pom.xml':
                        # Create Maven POM file
                        filepath = os.path.join(temp_dir, 'pom.xml')
                        with open(filepath, 'w') as f:
                            f.write('<?xml version="1.0"?>\n<project>\n  <modelVersion>4.0.0</modelVersion>\n</project>\n')
                    
                    elif marker == 'requirements.txt':
                        # Create Python requirements file
                        filepath = os.path.join(temp_dir, 'requirements.txt')
                        with open(filepath, 'w') as f:
                            f.write(f'{marker}\n')
                    
                    elif marker in ['flask', 'django', 'fastapi']:
                        # Python framework - add to requirements.txt
                        req_path = os.path.join(temp_dir, 'requirements.txt')
                        with open(req_path, 'a') as f:
                            f.write(f'{marker}\n')
                    
                    elif marker in ['react', 'vue', 'express', '@angular/core']:
                        # Node framework - already handled in package.json
                        pass
                    
                    elif marker == 'spring':
                        # Add spring to pom.xml if it exists
                        pom_path = os.path.join(temp_dir, 'pom.xml')
                        if os.path.exists(pom_path):
                            with open(pom_path, 'a') as f:
                                f.write('  <!-- spring dependency -->\n')
                    
                    elif marker in ['gin-gonic/gin', 'actix-web']:
                        # Create a go.mod or Cargo.toml to indicate framework usage
                        if 'gin' in marker:
                            go_mod_path = os.path.join(temp_dir, 'go.mod')
                            with open(go_mod_path, 'w') as f:
                                f.write('module example.com/myapp\n\n')
                                f.write('require github.com/gin-gonic/gin v1.9.0\n')
                        elif 'actix' in marker:
                            cargo_path = os.path.join(temp_dir, 'Cargo.toml')
                            with open(cargo_path, 'w') as f:
                                f.write('[package]\nname = "myapp"\nversion = "0.1.0"\n\n')
                                f.write('[dependencies]\nactix-web = "4"\n')
        
        return expected_frameworks
    
    @given(config=framework_marker_config())
    @settings(max_examples=100, deadline=None)
    def test_framework_detection_matches_markers(self, config):
        """Test that detected frameworks exactly match marker files present.
        
        **Validates: Requirements 6.3**
        
        Property: For any project directory structure containing framework marker
        files, the detected framework list SHALL include the framework corresponding
        to each marker file found, and SHALL NOT include frameworks whose marker
        files are absent.
        
        Tag: Feature: local-ai-dev-environment, Property 4: Framework Detection Consistency
        """
        # Create fresh test directory for this hypothesis example
        temp_dir, context_manager = self._create_fresh_test_dir()
        
        # Create marker files based on configuration
        expected_frameworks = self._create_marker_files(temp_dir, config)
        
        # Build file tree manually since we're in a test
        file_tree = context_manager._build_file_tree(temp_dir)
        
        # Detect frameworks
        detected_language_stack = context_manager.detect_language_stack(
            root_path=temp_dir,
            file_tree=file_tree
        )
        
        detected_frameworks = set(detected_language_stack.frameworks)
        
        # Verify: All expected frameworks are detected
        for framework in expected_frameworks:
            assert framework in detected_frameworks, \
                f"Framework '{framework}' should be detected (marker files present) but was not found. " \
                f"Expected: {expected_frameworks}, Detected: {detected_frameworks}"
        
        # Verify: No unexpected frameworks are detected
        for framework in detected_frameworks:
            assert framework in expected_frameworks, \
                f"Framework '{framework}' was detected but should not be (no marker files present). " \
                f"Expected: {expected_frameworks}, Detected: {detected_frameworks}"
        
        # Verify: Sets are identical
        assert detected_frameworks == expected_frameworks, \
            f"Detected frameworks must exactly match expected frameworks. " \
            f"Expected: {expected_frameworks}, Detected: {detected_frameworks}"
    
    @given(
        include_flask=st.booleans(),
        include_django=st.booleans(),
        include_fastapi=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_python_framework_detection_via_requirements(self, include_flask, include_django, include_fastapi):
        """Test Python framework detection through requirements.txt.
        
        **Validates: Requirements 6.3**
        
        Property: Python frameworks should be detected when their names appear
        in requirements.txt file.
        
        Tag: Feature: local-ai-dev-environment, Property 4: Framework Detection Consistency
        """
        # Create fresh test directory for this hypothesis example
        temp_dir, context_manager = self._create_fresh_test_dir()
        
        expected_frameworks = set()
        requirements_content = []
        
        if include_flask:
            expected_frameworks.add('Flask')
            requirements_content.append('flask==2.3.0')
        
        if include_django:
            expected_frameworks.add('Django')
            requirements_content.append('django==4.2.0')
            # Also create manage.py for Django
            manage_py_path = os.path.join(temp_dir, 'manage.py')
            with open(manage_py_path, 'w') as f:
                f.write('#!/usr/bin/env python\n')
        
        if include_fastapi:
            expected_frameworks.add('FastAPI')
            requirements_content.append('fastapi==0.104.0')
        
        # Create requirements.txt if any framework is included
        if requirements_content:
            req_path = os.path.join(temp_dir, 'requirements.txt')
            with open(req_path, 'w') as f:
                f.write('\n'.join(requirements_content))
        
        # Build file tree and detect frameworks
        file_tree = context_manager._build_file_tree(temp_dir)
        detected_language_stack = context_manager.detect_language_stack(
            root_path=temp_dir,
            file_tree=file_tree
        )
        
        detected_frameworks = set(detected_language_stack.frameworks)
        
        # Verify detection matches expectations
        assert detected_frameworks == expected_frameworks, \
            f"Python framework detection mismatch. Expected: {expected_frameworks}, Detected: {detected_frameworks}"
    
    @given(
        include_react=st.booleans(),
        include_vue=st.booleans(),
        include_angular=st.booleans(),
        include_express=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_node_framework_detection_via_packagejson(self, include_react, include_vue, include_angular, include_express):
        """Test Node.js framework detection through package.json.
        
        **Validates: Requirements 6.3**
        
        Property: Node.js frameworks should be detected when their packages
        appear in package.json dependencies.
        
        Tag: Feature: local-ai-dev-environment, Property 4: Framework Detection Consistency
        """
        # Create fresh test directory for this hypothesis example
        temp_dir, context_manager = self._create_fresh_test_dir()
        
        expected_frameworks = set()
        package_json = {"name": "test-project", "version": "1.0.0", "dependencies": {}}
        
        if include_react:
            expected_frameworks.add('React')
            package_json['dependencies']['react'] = '^18.0.0'
        
        if include_vue:
            expected_frameworks.add('Vue')
            package_json['dependencies']['vue'] = '^3.0.0'
        
        if include_angular:
            expected_frameworks.add('Angular')
            package_json['dependencies']['@angular/core'] = '^16.0.0'
            # Also create angular.json
            angular_json_path = os.path.join(temp_dir, 'angular.json')
            with open(angular_json_path, 'w') as f:
                f.write('{"version": 1}')
        
        if include_express:
            expected_frameworks.add('Express')
            package_json['dependencies']['express'] = '^4.18.0'
        
        # Create package.json
        pkg_path = os.path.join(temp_dir, 'package.json')
        import json
        with open(pkg_path, 'w') as f:
            json.dump(package_json, f)
        
        # Build file tree and detect frameworks
        file_tree = context_manager._build_file_tree(temp_dir)
        detected_language_stack = context_manager.detect_language_stack(
            root_path=temp_dir,
            file_tree=file_tree
        )
        
        detected_frameworks = set(detected_language_stack.frameworks)
        
        # Verify detection matches expectations
        assert detected_frameworks == expected_frameworks, \
            f"Node.js framework detection mismatch. Expected: {expected_frameworks}, Detected: {detected_frameworks}"
    
    @given(include_spring=st.booleans())
    @settings(max_examples=100, deadline=None)
    def test_spring_framework_detection_via_pom(self, include_spring):
        """Test Spring framework detection through pom.xml.
        
        **Validates: Requirements 6.3**
        
        Property: Spring framework should be detected when pom.xml exists
        and contains spring references.
        
        Tag: Feature: local-ai-dev-environment, Property 4: Framework Detection Consistency
        """
        # Create fresh test directory for this hypothesis example
        temp_dir, context_manager = self._create_fresh_test_dir()
        
        expected_frameworks = set()
        
        # Create pom.xml
        pom_path = os.path.join(temp_dir, 'pom.xml')
        pom_content = '<?xml version="1.0"?>\n<project>\n  <modelVersion>4.0.0</modelVersion>\n'
        
        if include_spring:
            expected_frameworks.add('Spring')
            pom_content += '  <dependencies>\n    <dependency>\n      <groupId>org.springframework</groupId>\n      <artifactId>spring-core</artifactId>\n    </dependency>\n  </dependencies>\n'
        
        pom_content += '</project>\n'
        
        with open(pom_path, 'w') as f:
            f.write(pom_content)
        
        # Build file tree and detect frameworks
        file_tree = context_manager._build_file_tree(temp_dir)
        detected_language_stack = context_manager.detect_language_stack(
            root_path=temp_dir,
            file_tree=file_tree
        )
        
        detected_frameworks = set(detected_language_stack.frameworks)
        
        # Verify detection matches expectations
        assert detected_frameworks == expected_frameworks, \
            f"Spring framework detection mismatch. Expected: {expected_frameworks}, Detected: {detected_frameworks}"
    
    @given(dummy=st.just(None))
    @settings(max_examples=100, deadline=None)
    def test_no_frameworks_detected_for_empty_project(self, dummy):
        """Test that no frameworks are detected in an empty project.
        
        **Validates: Requirements 6.3**
        
        Property: When no framework marker files are present, no frameworks
        should be detected.
        
        Tag: Feature: local-ai-dev-environment, Property 4: Framework Detection Consistency
        """
        # Create fresh test directory for this hypothesis example
        temp_dir, context_manager = self._create_fresh_test_dir()
        
        # Create an empty project with just a simple source file
        src_file = os.path.join(temp_dir, 'main.py')
        with open(src_file, 'w') as f:
            f.write('print("Hello, World!")\n')
        
        # Build file tree and detect frameworks
        file_tree = context_manager._build_file_tree(temp_dir)
        detected_language_stack = context_manager.detect_language_stack(
            root_path=temp_dir,
            file_tree=file_tree
        )
        
        detected_frameworks = detected_language_stack.frameworks
        
        # Verify no frameworks detected
        assert len(detected_frameworks) == 0, \
            f"Expected no frameworks for empty project, but detected: {detected_frameworks}"
    
    @given(
        frameworks=st.lists(
            st.sampled_from(['Flask', 'Django', 'React', 'Vue', 'Express', 'Spring']),
            min_size=1,
            max_size=4,
            unique=True
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_frameworks_coexistence(self, frameworks):
        """Test detection of multiple frameworks in the same project.
        
        **Validates: Requirements 6.3**
        
        Property: Multiple frameworks can coexist and should all be detected
        when their respective marker files are present.
        
        Tag: Feature: local-ai-dev-environment, Property 4: Framework Detection Consistency
        """
        # Create fresh test directory for this hypothesis example
        temp_dir, context_manager = self._create_fresh_test_dir()
        
        expected_frameworks = set(frameworks)
        
        # Create marker files for each selected framework
        for framework in frameworks:
            if framework == 'Flask':
                req_path = os.path.join(temp_dir, 'requirements.txt')
                with open(req_path, 'a') as f:
                    f.write('flask\n')
            
            elif framework == 'Django':
                req_path = os.path.join(temp_dir, 'requirements.txt')
                with open(req_path, 'a') as f:
                    f.write('django\n')
                manage_path = os.path.join(temp_dir, 'manage.py')
                with open(manage_path, 'w') as f:
                    f.write('#!/usr/bin/env python\n')
            
            elif framework in ['React', 'Vue', 'Express']:
                pkg_path = os.path.join(temp_dir, 'package.json')
                if os.path.exists(pkg_path):
                    with open(pkg_path, 'r') as f:
                        import json
                        pkg_data = json.load(f)
                else:
                    pkg_data = {"dependencies": {}}
                
                if framework == 'React':
                    pkg_data['dependencies']['react'] = '^18.0.0'
                elif framework == 'Vue':
                    pkg_data['dependencies']['vue'] = '^3.0.0'
                elif framework == 'Express':
                    pkg_data['dependencies']['express'] = '^4.18.0'
                
                with open(pkg_path, 'w') as f:
                    import json
                    json.dump(pkg_data, f)
            
            elif framework == 'Spring':
                pom_path = os.path.join(temp_dir, 'pom.xml')
                with open(pom_path, 'w') as f:
                    f.write('<?xml version="1.0"?>\n<project>\n  <modelVersion>4.0.0</modelVersion>\n  <dependencies><dependency><groupId>org.springframework</groupId></dependency></dependencies>\n</project>\n')
        
        # Build file tree and detect frameworks
        file_tree = context_manager._build_file_tree(temp_dir)
        detected_language_stack = context_manager.detect_language_stack(
            root_path=temp_dir,
            file_tree=file_tree
        )
        
        detected_frameworks = set(detected_language_stack.frameworks)
        
        # Verify all frameworks are detected
        assert detected_frameworks == expected_frameworks, \
            f"Multiple framework detection failed. Expected: {expected_frameworks}, Detected: {detected_frameworks}"
