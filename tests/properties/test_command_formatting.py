"""Property-based tests for command argument formatting.

This module tests Property 10: Command Argument Formatting
**Validates: Requirements 10.5**

The property ensures that command argument lists are properly formatted with
escaping so that shell parsing recovers the original argument list.
"""

import shlex
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.agents.command_executor import CommandExecutor


# Strategy for generating command names (first argument)
command_name_strategy = st.sampled_from([
    'python', 'pip', 'git', 'npm', 'node', 'java', 'gcc', 'make', 
    'ls', 'cat', 'echo', 'grep', 'find', 'curl', 'wget'
])


# Strategy for generating flag arguments (like -v, --verbose, -rf)
flag_strategy = st.one_of(
    # Short flags
    st.from_regex(r'-[a-zA-Z]', fullmatch=True),
    # Long flags
    st.from_regex(r'--[a-z][a-z-]*', fullmatch=True),
    # Combined short flags
    st.from_regex(r'-[a-zA-Z]{2,4}', fullmatch=True)
)


# Strategy for generating regular arguments with various special characters
argument_strategy = st.one_of(
    # Simple alphanumeric arguments
    st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=20),
    
    # Arguments with spaces (need quoting)
    st.from_regex(r'[a-zA-Z0-9]+ [a-zA-Z0-9 ]+', fullmatch=True),
    
    # File paths with spaces
    st.from_regex(r'[a-zA-Z0-9]+(/[a-zA-Z0-9 ]+)+', fullmatch=True),
    
    # Arguments with special shell characters
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+{}[]', min_size=1, max_size=15),
    
    # Arguments with quotes
    st.from_regex(r'[a-zA-Z0-9]+["\'][a-zA-Z0-9 ]+["\']', fullmatch=True),
    
    # Key-value style arguments
    st.from_regex(r'--[a-z-]+=[a-zA-Z0-9_/.-]+', fullmatch=True),
)


# Strategy for generating mixed argument lists
@st.composite
def command_with_args(draw):
    """Generate a command string with mixed arguments and flags."""
    # Draw command name
    cmd = draw(command_name_strategy)
    
    # Draw number of arguments (0 to 10)
    num_args = draw(st.integers(min_value=0, max_value=10))
    
    args = []
    for _ in range(num_args):
        # Randomly choose between flag or regular argument
        if draw(st.booleans()):
            args.append(draw(flag_strategy))
        else:
            args.append(draw(argument_strategy))
    
    # Join with spaces - this is the user input format
    return cmd + (' ' if args else '') + ' '.join(args)


@pytest.mark.property
class TestCommandArgumentFormatting:
    """Property-based tests for command argument formatting.
    
    Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
    """
    
    def setup_method(self):
        """Create CommandExecutor instance for each test method."""
        self.executor = CommandExecutor()
    
    @given(command=command_name_strategy)
    @settings(max_examples=100, deadline=None)
    def test_simple_command_formatting(self, command):
        """Test formatting of simple commands without arguments.
        
        **Validates: Requirements 10.5**
        
        Property: Simple command names should be correctly parsed into
        a single-element list.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        formatted = self.executor._format_command(command)
        
        # Should return a list with single element
        assert isinstance(formatted, list)
        assert len(formatted) == 1
        assert formatted[0] == command
    
    @given(command=command_name_strategy, flags=st.lists(flag_strategy, min_size=1, max_size=5))
    @settings(max_examples=100, deadline=None)
    def test_command_with_flags_formatting(self, command, flags):
        """Test formatting of commands with flags.
        
        **Validates: Requirements 10.5**
        
        Property: Commands with flags should preserve all flags in order.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Create command string
        command_str = command + ' ' + ' '.join(flags)
        
        # Format the command
        formatted = self.executor._format_command(command_str)
        
        # Verify structure
        assert isinstance(formatted, list)
        assert len(formatted) == 1 + len(flags)
        assert formatted[0] == command
        
        # Verify all flags are present in order
        for i, flag in enumerate(flags):
            assert formatted[i + 1] == flag
    
    @given(
        command=command_name_strategy,
        args=st.lists(
            st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P'), blacklist_characters='"\''), 
                   min_size=1, max_size=20),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_command_argument_count_preservation(self, command, args):
        """Test that the number of arguments is preserved.
        
        **Validates: Requirements 10.5**
        
        Property: The formatted command should have the correct number of arguments.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Create command string by properly quoting arguments
        # Quote if argument contains space or special shell characters
        def needs_quoting(arg):
            special_chars = ' \\$`"\'!*?[](){};<>|&~'
            return any(c in arg for c in special_chars)
        
        quoted_args = [f'"{arg}"' if needs_quoting(arg) else arg for arg in args]
        command_str = command + ' ' + ' '.join(quoted_args)
        
        # Format the command
        formatted = self.executor._format_command(command_str)
        
        # Verify count: command + all arguments
        assert len(formatted) == 1 + len(args)
        assert formatted[0] == command
    
    @given(
        command=command_name_strategy,
        arg_with_spaces=st.from_regex(r'[a-zA-Z0-9]+ [a-zA-Z0-9 ]+', fullmatch=True)
    )
    @settings(max_examples=100, deadline=None)
    def test_arguments_with_spaces_formatting(self, command, arg_with_spaces):
        """Test formatting of arguments containing spaces.
        
        **Validates: Requirements 10.5**
        
        Property: Arguments with spaces should be treated as single arguments
        when properly quoted, and the formatting should preserve them.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Create command with quoted argument
        command_str = f'{command} "{arg_with_spaces}"'
        
        # Format the command
        formatted = self.executor._format_command(command_str)
        
        # Should have exactly 2 elements: command and the argument
        assert len(formatted) == 2
        assert formatted[0] == command
        assert formatted[1] == arg_with_spaces  # Should be unquoted but intact
    
    @given(
        command=command_name_strategy,
        args=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_./=', min_size=1, max_size=20),
            min_size=1,
            max_size=8
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_shell_parsing_roundtrip(self, command, args):
        """Test that shell parsing recovers original argument list.
        
        **Validates: Requirements 10.5**
        
        Property: For any list of command arguments, the formatted command string
        SHALL preserve all arguments in the correct order so that shell parsing
        recovers the original argument list.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Create the original argument list
        original_args = [command] + args
        
        # Create a properly formatted command string using shlex.join
        # (simulating what a user might provide)
        try:
            command_str = shlex.join(original_args)
        except AttributeError:
            # Python < 3.8 doesn't have shlex.join
            command_str = ' '.join(shlex.quote(arg) for arg in original_args)
        
        # Format using our method
        formatted = self.executor._format_command(command_str)
        
        # Verify the formatted list matches the original
        assert formatted == original_args
        assert len(formatted) == len(original_args)
        
        # Verify order is preserved
        for i, arg in enumerate(original_args):
            assert formatted[i] == arg
    
    @given(
        command=command_name_strategy,
        args=st.lists(
            st.one_of(
                st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=15),
                st.from_regex(r'[a-zA-Z0-9]+ [a-zA-Z0-9]+', fullmatch=True),  # Args with spaces
                flag_strategy
            ),
            min_size=1,
            max_size=8
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_mixed_arguments_and_flags(self, command, args):
        """Test formatting with mixed regular arguments and flags.
        
        **Validates: Requirements 10.5**
        
        Property: Commands with mixed argument types should preserve all
        arguments in correct order and with correct formatting.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Build command string with proper quoting for args with spaces
        parts = [command]
        for arg in args:
            if ' ' in arg and not arg.startswith('-'):
                parts.append(f'"{arg}"')
            else:
                parts.append(arg)
        
        command_str = ' '.join(parts)
        
        # Format the command
        formatted = self.executor._format_command(command_str)
        
        # Verify structure
        assert len(formatted) == 1 + len(args)
        assert formatted[0] == command
        
        # Verify each argument is present (quotes removed)
        expected_args = [command] + args
        assert formatted == expected_args
    
    @given(
        command=command_name_strategy,
        special_chars_arg=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789$&|;<>(){}[]',
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_special_characters_escaping(self, command, special_chars_arg):
        """Test proper handling of special shell characters.
        
        **Validates: Requirements 10.5**
        
        Property: Arguments with special shell characters should be properly
        escaped/quoted so they are treated as literals.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Assume we don't have only special characters (need some content)
        assume(any(c.isalnum() for c in special_chars_arg))
        
        # Quote the argument to treat special chars as literals
        command_str = f'{command} {shlex.quote(special_chars_arg)}'
        
        # Format the command
        formatted = self.executor._format_command(command_str)
        
        # Should have exactly 2 elements
        assert len(formatted) == 2
        assert formatted[0] == command
        # The special chars argument should be preserved
        assert formatted[1] == special_chars_arg
    
    @given(
        command=command_name_strategy,
        key=st.text(alphabet=st.characters(whitelist_categories=('Ll',)), min_size=1, max_size=10),
        value=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_./', min_size=1, max_size=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_key_value_arguments(self, command, key, value):
        """Test formatting of key=value style arguments.
        
        **Validates: Requirements 10.5**
        
        Property: Key=value arguments should be preserved as single arguments.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Create key=value argument
        kv_arg = f'--{key}={value}'
        command_str = f'{command} {kv_arg}'
        
        # Format the command
        formatted = self.executor._format_command(command_str)
        
        # Should have exactly 2 elements
        assert len(formatted) == 2
        assert formatted[0] == command
        assert formatted[1] == kv_arg
    
    @given(command_str=st.from_regex(r'[a-z]+( +-[a-z]+)*( +[a-zA-Z0-9_-]+)*', fullmatch=True))
    @settings(max_examples=100, deadline=None)
    def test_formatting_idempotence(self, command_str):
        """Test that formatting is idempotent when applied to valid command strings.
        
        **Validates: Requirements 10.5**
        
        Property: Formatting a command string should produce consistent results.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        assume(len(command_str.strip()) > 0)
        
        # Format the command twice
        formatted1 = self.executor._format_command(command_str)
        
        # Reconstruct and format again
        reconstructed = ' '.join(formatted1)
        formatted2 = self.executor._format_command(reconstructed)
        
        # Should produce the same result
        assert formatted1 == formatted2
    
    @given(
        command=command_name_strategy,
        num_args=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=100, deadline=None)
    def test_argument_order_preservation(self, command, num_args):
        """Test that argument order is strictly preserved.
        
        **Validates: Requirements 10.5**
        
        Property: Arguments must appear in the formatted list in the same
        order as they appear in the command string.
        
        Tag: Feature: local-ai-dev-environment, Property 10: Command Argument Formatting
        """
        # Create numbered arguments to verify order
        args = [f'arg{i}' for i in range(num_args)]
        command_str = command + ' ' + ' '.join(args)
        
        # Format the command
        formatted = self.executor._format_command(command_str)
        
        # Verify order
        assert len(formatted) == 1 + num_args
        assert formatted[0] == command
        
        for i, arg in enumerate(args):
            assert formatted[i + 1] == arg, f"Argument {i} order not preserved"
