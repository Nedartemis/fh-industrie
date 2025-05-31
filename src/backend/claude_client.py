from typing import Any, Dict, List, Optional

import requests


class ClaudeClient:
    """A simple client for the Anthropic Claude API."""

    def __init__(self, api_key: str):
        """Initialize the Claude client with your API key."""
        self.api_key = api_key

        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def create_message(
        self,
        model: str = "claude-3-7-sonnet-20250219",
        messages: List[Dict[str, str]] = None,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a message using the Claude API.

        Args:
            model: The Claude model to use
            messages: List of message objects with role and content
            system: Optional system prompt to guide Claude's behavior
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0-1)
            stream: Whether to stream the response

        Returns:
            API response as a dictionary
        """
        if not messages:
            raise ValueError("Messages are required")

        url = f"{self.base_url}/messages"

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        if system:
            payload["system"] = system

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code != 200:
            raise Exception(
                f"API request failed with status {response.status_code}: {response.text}"
            )

        return response.json()
