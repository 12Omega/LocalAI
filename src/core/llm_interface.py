"""Local LLM Interface for AI Development Environment.

This module provides abstraction over different local LLM backends
(Ollama, llama.cpp, OpenAI-compatible servers) and handles request
formatting, response parsing, tool calling translation, and error handling.
"""

import json
import requests
import logging
from typing import List, Iterator, Optional, Dict, Any
from requests.exceptions import RequestException, Timeout, ConnectionError

from src.core.models import LLMConfig, Tool, LLMResponse, ToolCall
from src.core.error_handler import ErrorHandler, RetryStrategy, with_retry

# Configure logger
logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class ModelUnavailableError(LLMError):
    """Raised when the LLM model is not available."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class InvalidResponseError(LLMError):
    """Raised when LLM returns an invalid response format."""
    pass


class LocalLLMInterface:
    """Interface for interacting with local language models.
    
    Supports multiple backends:
    - Ollama: REST API on http://localhost:11434
    - llama.cpp: OpenAI-compatible API
    - Generic OpenAI-compatible backends
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize the LLM interface with configuration.
        
        Args:
            config: LLMConfig containing endpoint, model, and parameters
        """
        self.config = config
        self.endpoint = config.endpoint.rstrip('/')
        self.model_name = config.model_name
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.context_length = config.context_length
        self.backend_type = config.backend_type.lower()
        
        # Set timeout for requests (in seconds)
        self.timeout = 120
        
        # Initialize error handler with retry strategy for transient failures
        self.error_handler = ErrorHandler(logger=logger)
        self.retry_strategy = RetryStrategy(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        logger.info(
            f"LocalLLMInterface initialized: backend={self.backend_type}, "
            f"model={self.model_name}, endpoint={self.endpoint}"
        )
        
    def generate(self, prompt: str, tools: Optional[List[Tool]] = None) -> LLMResponse:
        """Generate a response from the LLM with optional tool calling support.
        
        Uses automatic retry with exponential backoff for transient failures.
        
        Args:
            prompt: The input prompt/message for the LLM
            tools: Optional list of tool definitions for function calling
            
        Returns:
            LLMResponse containing the generated text and any tool calls
            
        Raises:
            ModelUnavailableError: If the model cannot be reached
            LLMTimeoutError: If the request times out after retries
            InvalidResponseError: If the response format is invalid
        """
        try:
            # Use retry logic for the actual generation
            return self.error_handler.retry_with_backoff(
                self._generate_internal,
                prompt,
                tools,
                strategy=self.retry_strategy,
                operation_name="LLM generation"
            )
                
        except ConnectionError as e:
            error_msg = (
                f"Cannot connect to LLM at {self.endpoint}. "
                f"Ensure the model server is running. Error: {str(e)}"
            )
            logger.error(error_msg)
            raise ModelUnavailableError(error_msg)
        except Timeout as e:
            error_msg = (
                f"Request to LLM timed out after {self.timeout} seconds and {self.retry_strategy.max_retries} retries. "
                f"The model may be overloaded or the prompt too complex. Error: {str(e)}"
            )
            logger.error(error_msg)
            raise LLMTimeoutError(error_msg)
        except RequestException as e:
            error_msg = f"Failed to communicate with LLM: {str(e)}"
            logger.error(error_msg)
            raise ModelUnavailableError(error_msg)
    
    def _generate_internal(self, prompt: str, tools: Optional[List[Tool]] = None) -> LLMResponse:
        """Internal generation method that can be retried.
        
        Args:
            prompt: The input prompt/message for the LLM
            tools: Optional list of tool definitions for function calling
            
        Returns:
            LLMResponse containing the generated text and any tool calls
        """
        if self.backend_type == "ollama":
            return self._generate_ollama(prompt, tools)
        elif self.backend_type in ["llamacpp", "openai-compatible"]:
            return self._generate_openai_compatible(prompt, tools)
        else:
            raise LLMError(f"Unsupported backend type: {self.backend_type}")
    
    def stream_generate(self, prompt: str) -> Iterator[str]:
        """Stream response tokens as they are generated.
        
        Args:
            prompt: The input prompt/message for the LLM
            
        Yields:
            String tokens as they are generated
            
        Raises:
            ModelUnavailableError: If the model cannot be reached
            LLMTimeoutError: If the request times out
        """
        try:
            if self.backend_type == "ollama":
                yield from self._stream_ollama(prompt)
            elif self.backend_type in ["llamacpp", "openai-compatible"]:
                yield from self._stream_openai_compatible(prompt)
            else:
                raise LLMError(f"Unsupported backend type: {self.backend_type}")
                
        except ConnectionError as e:
            raise ModelUnavailableError(
                f"Cannot connect to LLM at {self.endpoint}. "
                f"Ensure the model server is running. Error: {str(e)}"
            )
        except Timeout as e:
            raise LLMTimeoutError(
                f"Streaming request timed out. Error: {str(e)}"
            )
        except RequestException as e:
            raise ModelUnavailableError(
                f"Failed to communicate with LLM: {str(e)}"
            )
    
    def encode(self, text: str) -> List[int]:
        """Tokenize text for context length calculation.
        
        Args:
            text: The text to tokenize
            
        Returns:
            List of token IDs
            
        Raises:
            ModelUnavailableError: If the tokenization endpoint is unavailable
        """
        try:
            if self.backend_type == "ollama":
                return self._encode_ollama(text)
            elif self.backend_type in ["llamacpp", "openai-compatible"]:
                # For OpenAI-compatible APIs, use a rough approximation
                # Most models use ~4 chars per token
                return self._encode_approximate(text)
            else:
                raise LLMError(f"Unsupported backend type: {self.backend_type}")
                
        except ConnectionError as e:
            raise ModelUnavailableError(
                f"Cannot connect to LLM for tokenization: {str(e)}"
            )
        except RequestException as e:
            raise ModelUnavailableError(
                f"Failed to tokenize text: {str(e)}"
            )
    
    # Ollama-specific implementations
    
    def _generate_ollama(self, prompt: str, tools: Optional[List[Tool]] = None) -> LLMResponse:
        """Generate response using Ollama API."""
        url = f"{self.endpoint}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
            }
        }
        
        # Add tool definitions if provided
        if tools:
            payload["tools"] = self._translate_tools_to_ollama(tools)
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_ollama_response(data)
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelUnavailableError(
                    f"Model '{self.model_name}' not found. "
                    f"Pull the model with: ollama pull {self.model_name}"
                )
            raise InvalidResponseError(f"HTTP error from Ollama: {str(e)}")
        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Invalid JSON response from Ollama: {str(e)}")
    
    def _stream_ollama(self, prompt: str) -> Iterator[str]:
        """Stream response using Ollama API."""
        url = f"{self.endpoint}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": True,
            "options": {
                "num_predict": self.max_tokens,
            }
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelUnavailableError(
                    f"Model '{self.model_name}' not found. "
                    f"Pull the model with: ollama pull {self.model_name}"
                )
            raise InvalidResponseError(f"HTTP error from Ollama: {str(e)}")
    
    def _encode_ollama(self, text: str) -> List[int]:
        """Tokenize text using Ollama API."""
        url = f"{self.endpoint}/api/embeddings"
        
        # Ollama doesn't have a dedicated tokenize endpoint,
        # so we use embeddings endpoint and extract token count
        # or fall back to approximation
        
        # For now, use approximation (4 chars per token is common)
        return self._encode_approximate(text)
    
    # OpenAI-compatible implementations
    
    def _generate_openai_compatible(self, prompt: str, tools: Optional[List[Tool]] = None) -> LLMResponse:
        """Generate response using OpenAI-compatible API."""
        url = f"{self.endpoint}/v1/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # Add tool definitions if provided
        if tools:
            payload["tools"] = self._translate_tools_to_openai(tools)
            payload["tool_choice"] = "auto"
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_openai_response(data)
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelUnavailableError(
                    f"Model '{self.model_name}' not found or endpoint incorrect."
                )
            raise InvalidResponseError(f"HTTP error from OpenAI-compatible API: {str(e)}")
        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Invalid JSON response: {str(e)}")
    
    def _stream_openai_compatible(self, prompt: str) -> Iterator[str]:
        """Stream response using OpenAI-compatible API."""
        url = f"{self.endpoint}/v1/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelUnavailableError(
                    f"Model '{self.model_name}' not found or endpoint incorrect."
                )
            raise InvalidResponseError(f"HTTP error from OpenAI-compatible API: {str(e)}")
    
    def _encode_approximate(self, text: str) -> List[int]:
        """Approximate tokenization (4 chars per token)."""
        # This is a rough approximation used when actual tokenization is unavailable
        # Most LLM tokenizers use approximately 4 characters per token
        estimated_tokens = len(text) // 4
        # Return a list of dummy token IDs
        return list(range(estimated_tokens))
    
    # Tool translation methods
    
    def _translate_tools_to_ollama(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Translate tool definitions to Ollama format."""
        ollama_tools = []
        for tool in tools:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return ollama_tools
    
    def _translate_tools_to_openai(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Translate tool definitions to OpenAI format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return openai_tools
    
    # Response parsing methods
    
    def _parse_ollama_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse Ollama API response."""
        content = data.get("response", "")
        tool_calls = []
        
        # Check if response contains tool calls
        if "tool_calls" in data:
            for tc in data["tool_calls"]:
                tool_calls.append(ToolCall(
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                ))
        
        # Determine finish reason
        finish_reason = None
        if data.get("done", False):
            finish_reason = "stop"
            if tool_calls:
                finish_reason = "tool_calls"
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=None  # Ollama doesn't always provide token usage
        )
    
    def _parse_openai_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse OpenAI-compatible API response."""
        if "choices" not in data or len(data["choices"]) == 0:
            raise InvalidResponseError("Response missing 'choices' field")
        
        choice = data["choices"][0]
        message = choice.get("message", {})
        
        content = message.get("content", "")
        tool_calls = []
        
        # Parse tool calls if present
        if "tool_calls" in message:
            for tc in message["tool_calls"]:
                arguments = tc["function"]["arguments"]
                # Arguments might be a JSON string
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                
                tool_calls.append(ToolCall(
                    name=tc["function"]["name"],
                    arguments=arguments
                ))
        
        finish_reason = choice.get("finish_reason")
        
        # Extract token usage if available
        usage = None
        if "usage" in data:
            usage = {
                "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                "completion_tokens": data["usage"].get("completion_tokens", 0),
                "total_tokens": data["usage"].get("total_tokens", 0),
            }
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage
        )
