"""
LLM Configuration Module
Handles API keys and LLM function calls for Claude, OpenAI, and Ollama.
"""

import os
import anthropic
import openai
import ollama
import html
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class InsufficientQuotaError(Exception):
    pass


class LLMConfig:
    """Configuration class for managing LLM API keys and clients."""
    
    def __init__(self):
        """Initialize API keys from environment variables."""
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize clients if keys are available
        self.anthropic_client = None
        self.openai_client = None
        
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
    
    def call_claude(
        self, 
        prompt: str, 
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str = None
    ) -> str:
        """
        Call Claude API to generate a response.
        
        Args:
            prompt: The input prompt
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system: Optional system message
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If API key is not configured
        """
        if not self.anthropic_client:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
            )
        
        try:
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            if system:
                kwargs["system"] = system
                
            message = self.anthropic_client.messages.create(**kwargs)
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def call_openai(
        self, 
        prompt: str, 
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str = None,
        timeout_seconds: int = 180,
        return_usage: bool = False
    ):
        """
        Call OpenAI API to generate a response.
        
        Args:
            prompt: The input prompt
            model: OpenAI model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system: Optional system message
            timeout_seconds: Request timeout in seconds
            return_usage: If True, returns (content, usage) tuple
            
        Returns:
            Generated text response, or (content, usage) if return_usage=True
            
        Raises:
            ValueError: If API key is not configured
        """
        if not self.openai_client:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )
        
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout_seconds
            )
            
            if return_usage:
                return response.choices[0].message.content, response.usage
            else:
                return response.choices[0].message.content
        except Exception as e:
            msg = str(e)
            if "insufficient_quota" in msg or "Error code: 429" in msg:
                raise InsufficientQuotaError(f"OpenAI quota exceeded: {msg}")
            raise Exception(f"OpenAI API error: {html.escape(msg)}")
    
    def call_ollama(
        self, 
        prompt: str, 
        model: str = "qwen3:8b",
        temperature: float = 0.7,
        system: str = None
    ) -> str:
        """
        Call Ollama (local) to generate a response.
        
        Args:
            prompt: The input prompt
            model: Ollama model to use
            temperature: Sampling temperature
            system: Optional system message
            
        Returns:
            Generated text response
        """
        import subprocess
        import json
        
        try:
            # Build the request
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            # Use curl to call Ollama API directly
            cmd = ["curl", "http://localhost:11434/api/generate", 
                   "-H", "Content-Type: application/json",
                   "-d", json.dumps({
                       "model": model,
                       "prompt": prompt,
                       "system": system or "",
                       "stream": False,
                       "options": {
                           "temperature": temperature
                       }
                   })]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                raise Exception(f"Ollama API call failed: {result.stderr}")
            
            response = json.loads(result.stdout)
            return response.get("response", "")
            
        except subprocess.TimeoutExpired:
            raise Exception("Ollama API call timed out after 180 seconds")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")


# Global instance for easy import
llm_config = LLMConfig()


def call_claude(prompt: str, **kwargs) -> str:
    """Convenience function to call Claude."""
    return llm_config.call_claude(prompt, **kwargs)


def call_openai(prompt: str, return_usage: bool = False, **kwargs) -> str:
    """Convenience function to call OpenAI."""
    return llm_config.call_openai(prompt, return_usage=return_usage, **kwargs)


def call_ollama(prompt: str, **kwargs) -> str:
    """Convenience function to call Ollama."""
    return llm_config.call_ollama(prompt, **kwargs)


def get_llm_response(
    prompt: str,
    llm_type: str = "openai",
    system_message: str = None,
    max_tokens: int = 16000,
    temperature: float = 0.7,
    timeout_seconds: int = 180,
    model: str = None
) -> str:
    """
    Unified LLM response function supporting Claude, OpenAI, and Ollama.
    
    Args:
        prompt: The input prompt
        llm_type: "claude", "openai", or "ollama"
        system_message: Optional system message
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        timeout_seconds: Timeout for API calls
        model: Optional model override (e.g., "gpt-4o", "gpt-4-turbo")
        
    Returns:
        Generated text response
    """
    llm_type = llm_type.lower()
    
    if llm_type == "claude":
        return llm_config.call_claude(
            prompt=prompt,
            system=system_message,
            max_tokens=max_tokens,
            temperature=temperature
        )
    elif llm_type == "openai":
        kwargs = {
            "prompt": prompt,
            "system": system_message,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "timeout_seconds": timeout_seconds
        }
        if model:
            kwargs["model"] = model
        return llm_config.call_openai(**kwargs)
    elif llm_type == "ollama":
        return llm_config.call_ollama(
            prompt=prompt,
            system=system_message,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unknown LLM type: {llm_type}. Use 'claude', 'openai', or 'ollama'.")
