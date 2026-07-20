"""LangChain-compatible wrapper for OpenAI's Responses API.

This module provides ChatOpenAIResponses, a drop-in replacement for ChatOpenAI
that uses the /v1/responses endpoint instead of /v1/chat/completions.

This is required for newer models like gpt-5.1-codex-mini that only support
the Responses API.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence, Union

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from openai import OpenAI
from pydantic import Field

logger = logging.getLogger(__name__)


class ChatOpenAIResponses(BaseChatModel):
    """LangChain-compatible chat model using OpenAI's Responses API.

    This class provides the same interface as ChatOpenAI but uses the
    /v1/responses endpoint, which is required for certain newer models.

    Example:
        >>> llm = ChatOpenAIResponses(model="gpt-5.1-codex-mini")
        >>> llm_with_tools = llm.bind_tools([my_tool])
        >>> result = llm_with_tools.invoke([HumanMessage(content="Hello")])
    """

    model: str = Field(default="gpt-5.1-codex-mini")
    base_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    temperature: float = Field(default=1.0)
    max_output_tokens: int = Field(default=4096)
    top_p: float = Field(default=1.0)

    # Retry settings for rate limit handling
    max_retries: int = Field(default=5)
    initial_retry_delay: float = Field(default=1.0)
    max_retry_delay: float = Field(default=60.0)
    retry_multiplier: float = Field(default=2.0)

    # Internal state for tool binding
    _bound_tools: List[Dict[str, Any]] = []
    _client: Optional[OpenAI] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bound_tools = []
        self._client = None

    @property
    def _llm_type(self) -> str:
        return "openai-responses"

    @property
    def client(self) -> OpenAI:
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if self.base_url:
                self._client = OpenAI(api_key=api_key, base_url=self.base_url)
            else:
                self._client = OpenAI(api_key=api_key)
        return self._client

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], BaseTool]],
        **kwargs: Any,
    ) -> "ChatOpenAIResponses":
        """Bind tools to this model instance.

        Args:
            tools: A sequence of tools to bind. Can be LangChain tools or dicts.

        Returns:
            A new ChatOpenAIResponses instance with the tools bound.
        """
        new_instance = ChatOpenAIResponses(
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            top_p=self.top_p,
            max_retries=self.max_retries,
            initial_retry_delay=self.initial_retry_delay,
            max_retry_delay=self.max_retry_delay,
            retry_multiplier=self.retry_multiplier,
        )
        new_instance._bound_tools = self._convert_tools(tools)
        return new_instance

    def _convert_tools(
        self, tools: Sequence[Union[Dict[str, Any], BaseTool]]
    ) -> List[Dict[str, Any]]:
        """Convert LangChain tools to OpenAI Responses API function format.

        The Responses API uses a flat structure for function tools:
        {
            "type": "function",
            "name": "function_name",
            "description": "...",
            "parameters": {...}
        }

        This differs from Chat Completions which nests under "function" key.
        """
        converted = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                # Get the JSON schema for parameters
                if tool.args_schema:
                    params = tool.args_schema.model_json_schema()
                    # Remove title field that OpenAI doesn't expect at schema level
                    params.pop("title", None)
                else:
                    params = {"type": "object", "properties": {}}

                # Responses API uses flat structure - name at top level, not nested
                tool_schema = {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": params,
                }
                converted.append(tool_schema)
            elif isinstance(tool, dict):
                # Handle dict format - convert from Chat Completions format if needed
                if "function" in tool:
                    # Chat Completions format - flatten it
                    func = tool["function"]
                    tool_schema = {
                        "type": "function",
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {"type": "object", "properties": {}}),
                    }
                    converted.append(tool_schema)
                elif "name" in tool:
                    # Already in Responses API format
                    converted.append(tool)
                else:
                    # Unknown format, try to use as-is
                    converted.append(tool)
        return converted

    def _convert_messages(
        self, messages: List[BaseMessage]
    ) -> List[Dict[str, Any]]:
        """Convert LangChain messages to OpenAI Responses API format.

        The Responses API uses a different message format than Chat Completions:
        - System/user messages use 'input_text' content type
        - Assistant messages use 'output_text' content type (no function_call in content)
        - Tool calls from assistant are represented as separate 'function_call' items
        - Tool results use 'function_call_output' content type
        """
        converted = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                converted.append({
                    "role": "system",
                    "content": [{"type": "input_text", "text": content}],
                })
            elif isinstance(msg, HumanMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                converted.append({
                    "role": "user",
                    "content": [{"type": "input_text", "text": content}],
                })
            elif isinstance(msg, AIMessage):
                # Handle AI messages (assistant responses)
                # First add text content if present
                if msg.content:
                    content = msg.content if isinstance(msg.content, str) else str(msg.content)
                    converted.append({
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": content}],
                    })

                # Tool calls need to be added as separate items in the Responses API
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        # Convert args to JSON string for the API
                        args = tc.get("args", {})
                        if isinstance(args, dict):
                            args_str = json.dumps(args)
                        else:
                            args_str = str(args)

                        # Add tool call as a separate item (not inside assistant content)
                        converted.append({
                            "type": "function_call",
                            "call_id": tc.get("id", str(uuid.uuid4())),
                            "name": tc["name"],
                            "arguments": args_str,
                        })
                elif not msg.content:
                    # Empty assistant message - add placeholder
                    converted.append({
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": ""}],
                    })
            elif isinstance(msg, ToolMessage):
                # Tool results need to be formatted as function call outputs
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                converted.append({
                    "type": "function_call_output",
                    "call_id": msg.tool_call_id,
                    "output": content,
                })
        return converted

    def _parse_response(self, response: Any) -> AIMessage:
        """Parse OpenAI Responses API response into LangChain AIMessage."""
        text_content = ""
        tool_calls = []

        if not response.output:
            return AIMessage(content="")

        for item in response.output:
            # Handle text output
            if hasattr(item, 'content') and item.content:
                for block in item.content:
                    if hasattr(block, 'text') and block.text:
                        text_content += block.text

            # Handle function/tool calls
            if hasattr(item, 'type') and item.type == 'function_call':
                args = item.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                tool_calls.append({
                    "id": getattr(item, 'id', None) or getattr(item, 'call_id', None) or str(uuid.uuid4()),
                    "name": item.name,
                    "args": args,
                })

        if tool_calls:
            return AIMessage(content=text_content, tool_calls=tool_calls)
        return AIMessage(content=text_content)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using the OpenAI Responses API.

        Includes exponential backoff retry logic for rate limit errors (429).

        Args:
            messages: List of LangChain messages to send.
            stop: Optional stop sequences (not used by Responses API).
            run_manager: Optional callback manager.

        Returns:
            ChatResult containing the model's response.
        """
        # Convert messages to Responses API format
        converted_messages = self._convert_messages(messages)

        # Build request parameters
        request_params = {
            "model": self.model,
            "input": converted_messages,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "top_p": self.top_p,
        }

        # Debug: log which model is being called
        logger.info(f"ChatOpenAIResponses: Calling model '{self.model}' with {len(converted_messages)} messages")

        # Add tools if bound
        if self._bound_tools:
            request_params["tools"] = self._bound_tools

        # Make the API call with exponential backoff retry
        response = self._call_with_retry(request_params)

        # Parse the response
        ai_message = self._parse_response(response)

        return ChatResult(
            generations=[ChatGeneration(message=ai_message)],
        )

    def _call_with_retry(self, request_params: Dict[str, Any]) -> Any:
        """Make API call with exponential backoff retry for rate limits.

        Args:
            request_params: Parameters for the API call.

        Returns:
            API response object.

        Raises:
            Exception: If all retries are exhausted or non-retryable error occurs.
        """
        last_exception = None
        delay = self.initial_retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                return self.client.responses.create(**request_params)
            except Exception as e:
                error_str = str(e)
                last_exception = e

                # Check if this is a rate limit error (429)
                is_rate_limit = (
                    "429" in error_str
                    or "rate_limit" in error_str.lower()
                    or "rate limit" in error_str.lower()
                )

                if not is_rate_limit:
                    # Non-retryable error, raise immediately
                    raise

                if attempt == self.max_retries:
                    # Exhausted all retries
                    logger.error(
                        f"Rate limit: exhausted {self.max_retries} retries for {self.model}"
                    )
                    raise

                # Extract suggested wait time from error if available
                wait_time = delay
                if "Please try again in" in error_str:
                    try:
                        # Parse "Please try again in 6.045s"
                        import re
                        match = re.search(r"try again in ([\d.]+)s", error_str)
                        if match:
                            wait_time = max(float(match.group(1)), delay)
                    except (ValueError, AttributeError):
                        pass

                logger.warning(
                    f"Rate limit hit for {self.model}, attempt {attempt + 1}/{self.max_retries + 1}. "
                    f"Waiting {wait_time:.1f}s before retry..."
                )

                time.sleep(wait_time)

                # Exponential backoff for next attempt
                delay = min(delay * self.retry_multiplier, self.max_retry_delay)

        # Should not reach here, but just in case
        raise last_exception

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters for this LLM."""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "max_retries": self.max_retries,
        }
