"""Unit tests for LocalLLMInterface."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import ConnectionError, Timeout, HTTPError

from src.core.llm_interface import (
    LocalLLMInterface,
    ModelUnavailableError,
    LLMTimeoutError,
    InvalidResponseError,
    LLMError,
)
from src.core.models import LLMConfig, Tool, LLMResponse, ToolCall


class TestLocalLLMInterfaceInit:
    """Tests for LocalLLMInterface initialization."""
    
    def test_init_with_ollama_config(self):
        """Test initialization with Ollama configuration."""
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            temperature=0.2,
            max_tokens=4096,
            context_length=16384,
            backend_type="ollama"
        )
        
        interface = LocalLLMInterface(config)
        
        assert interface.endpoint == "http://localhost:11434"
        assert interface.model_name == "codellama:13b"
        assert interface.temperature == 0.2
        assert interface.max_tokens == 4096
        assert interface.backend_type == "ollama"
    
    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from endpoint."""
        config = LLMConfig(
            endpoint="http://localhost:11434/",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        
        interface = LocalLLMInterface(config)
        
        assert interface.endpoint == "http://localhost:11434"
    
    def test_init_with_openai_compatible_config(self):
        """Test initialization with OpenAI-compatible configuration."""
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="llama-2-13b",
            backend_type="openai-compatible"
        )
        
        interface = LocalLLMInterface(config)
        
        assert interface.backend_type == "openai-compatible"


class TestOllamaGenerate:
    """Tests for Ollama generate method."""
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_success(self, mock_post):
        """Test successful generation with Ollama."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Hello, world!",
            "done": True
        }
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        result = interface.generate("Test prompt")
        
        assert isinstance(result, LLMResponse)
        assert result.content == "Hello, world!"
        assert result.finish_reason == "stop"
        assert result.tool_calls == []
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['model'] == "codellama:13b"
        assert call_args[1]['json']['prompt'] == "Test prompt"
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_with_tools(self, mock_post):
        """Test generation with tool definitions."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Using tool",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_code",
                        "arguments": {"query": "test"}
                    }
                }
            ],
            "done": True
        }
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        tools = [
            Tool(
                name="search_code",
                description="Search for code",
                parameters={"type": "object", "properties": {"query": {"type": "string"}}}
            )
        ]
        
        result = interface.generate("Test prompt", tools)
        
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "search_code"
        assert result.tool_calls[0].arguments == {"query": "test"}
        assert result.finish_reason == "tool_calls"
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_model_not_found(self, mock_post):
        """Test handling of model not found error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status.side_effect = HTTPError(response=mock_response)
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="nonexistent:model",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(ModelUnavailableError) as exc_info:
            interface.generate("Test prompt")
        
        assert "not found" in str(exc_info.value).lower()
        assert "nonexistent:model" in str(exc_info.value)
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_connection_error(self, mock_post):
        """Test handling of connection error."""
        mock_post.side_effect = ConnectionError("Connection refused")
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(ModelUnavailableError) as exc_info:
            interface.generate("Test prompt")
        
        assert "cannot connect" in str(exc_info.value).lower()
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_timeout(self, mock_post):
        """Test handling of timeout error."""
        mock_post.side_effect = Timeout("Request timed out")
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(LLMTimeoutError) as exc_info:
            interface.generate("Test prompt")
        
        assert "timed out" in str(exc_info.value).lower()
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_invalid_json(self, mock_post):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(InvalidResponseError) as exc_info:
            interface.generate("Test prompt")
        
        assert "invalid json" in str(exc_info.value).lower()


class TestOpenAICompatibleGenerate:
    """Tests for OpenAI-compatible generate method."""
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_success(self, mock_post):
        """Test successful generation with OpenAI-compatible API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello from OpenAI API!"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="llama-2-13b",
            backend_type="openai-compatible"
        )
        interface = LocalLLMInterface(config)
        
        result = interface.generate("Test prompt")
        
        assert result.content == "Hello from OpenAI API!"
        assert result.finish_reason == "stop"
        assert result.usage is not None
        assert result.usage["total_tokens"] == 30
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_with_tools(self, mock_post):
        """Test generation with tool calls in OpenAI format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "create_file",
                                    "arguments": '{"path": "test.py", "content": "print()"}'
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="llama-2-13b",
            backend_type="openai-compatible"
        )
        interface = LocalLLMInterface(config)
        
        tools = [
            Tool(
                name="create_file",
                description="Create a file",
                parameters={"type": "object"}
            )
        ]
        
        result = interface.generate("Test prompt", tools)
        
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create_file"
        assert result.tool_calls[0].arguments["path"] == "test.py"
    
    @patch('src.core.llm_interface.requests.post')
    def test_generate_missing_choices(self, mock_post):
        """Test handling of response missing choices field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="llama-2-13b",
            backend_type="openai-compatible"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(InvalidResponseError) as exc_info:
            interface.generate("Test prompt")
        
        assert "missing 'choices'" in str(exc_info.value).lower()


class TestStreamGenerate:
    """Tests for stream_generate method."""
    
    @patch('src.core.llm_interface.requests.post')
    def test_stream_ollama(self, mock_post):
        """Test streaming with Ollama."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"response": "Hello", "done": false}',
            b'{"response": " world", "done": false}',
            b'{"response": "!", "done": true}'
        ]
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        tokens = list(interface.stream_generate("Test prompt"))
        
        assert tokens == ["Hello", " world", "!"]
    
    @patch('src.core.llm_interface.requests.post')
    def test_stream_openai_compatible(self, mock_post):
        """Test streaming with OpenAI-compatible API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            b'data: {"choices": [{"delta": {"content": " world"}}]}',
            b'data: [DONE]'
        ]
        mock_post.return_value = mock_response
        
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="llama-2-13b",
            backend_type="openai-compatible"
        )
        interface = LocalLLMInterface(config)
        
        tokens = list(interface.stream_generate("Test prompt"))
        
        assert tokens == ["Hello", " world"]
    
    @patch('src.core.llm_interface.requests.post')
    def test_stream_connection_error(self, mock_post):
        """Test stream handling of connection error."""
        mock_post.side_effect = ConnectionError("Connection refused")
        
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(ModelUnavailableError):
            list(interface.stream_generate("Test prompt"))


class TestEncode:
    """Tests for encode method."""
    
    def test_encode_approximate(self):
        """Test approximate encoding."""
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="llama-2-13b",
            backend_type="openai-compatible"
        )
        interface = LocalLLMInterface(config)
        
        # Test with a string (4 chars per token approximation)
        text = "a" * 100
        tokens = interface.encode(text)
        
        assert len(tokens) == 25  # 100 / 4 = 25
    
    def test_encode_short_text(self):
        """Test encoding short text."""
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        tokens = interface.encode("Hi")
        
        assert len(tokens) == 0  # 2 chars / 4 = 0


class TestToolTranslation:
    """Tests for tool definition translation."""
    
    def test_translate_tools_to_ollama(self):
        """Test tool translation to Ollama format."""
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="ollama"
        )
        interface = LocalLLMInterface(config)
        
        tools = [
            Tool(
                name="search_code",
                description="Search code",
                parameters={"type": "object", "properties": {"query": {"type": "string"}}}
            )
        ]
        
        translated = interface._translate_tools_to_ollama(tools)
        
        assert len(translated) == 1
        assert translated[0]["type"] == "function"
        assert translated[0]["function"]["name"] == "search_code"
        assert translated[0]["function"]["description"] == "Search code"
    
    def test_translate_tools_to_openai(self):
        """Test tool translation to OpenAI format."""
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="llama-2-13b",
            backend_type="openai-compatible"
        )
        interface = LocalLLMInterface(config)
        
        tools = [
            Tool(
                name="create_file",
                description="Create file",
                parameters={"type": "object"}
            )
        ]
        
        translated = interface._translate_tools_to_openai(tools)
        
        assert len(translated) == 1
        assert translated[0]["type"] == "function"
        assert translated[0]["function"]["name"] == "create_file"


class TestUnsupportedBackend:
    """Tests for unsupported backend handling."""
    
    def test_generate_unsupported_backend(self):
        """Test error on unsupported backend type."""
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="test-model",
            backend_type="unsupported"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(LLMError) as exc_info:
            interface.generate("Test prompt")
        
        assert "unsupported backend" in str(exc_info.value).lower()
    
    def test_stream_unsupported_backend(self):
        """Test stream error on unsupported backend type."""
        config = LLMConfig(
            endpoint="http://localhost:8080",
            model_name="test-model",
            backend_type="unsupported"
        )
        interface = LocalLLMInterface(config)
        
        with pytest.raises(LLMError) as exc_info:
            list(interface.stream_generate("Test prompt"))
        
        assert "unsupported backend" in str(exc_info.value).lower()
