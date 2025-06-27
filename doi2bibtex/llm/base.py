import httpx
import json
import sys
from pathlib import Path

class LLMProvider:
    """Base class for LLM providers."""
    def __init__(self, config):
        self.config = config

    def get_completion(self, prompt, **kwargs):
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    """Provider for Ollama."""
    def get_completion(self, prompt, model="llama3", **kwargs):
        try:
            with httpx.Client(timeout=self.config.get('timeout', 60)) as client:
                response = client.post(
                    self.config.get('url', 'http://localhost:11434/api/generate'),
                    json={
                        "model": self.config.get('model', model),
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                # The actual response content is a JSON string on a single line
                return json.loads(response.text)['response']
        except httpx.RequestError as e:
            print(f"Error contacting Ollama: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding Ollama response: {e}")
            return None

def get_llm_provider(config):
    """Factory function to get an LLM provider."""
    provider_name = config.get('provider', 'ollama').lower()
    if provider_name == 'ollama':
        return OllamaProvider(config.get('ollama', {}))
    # Add other providers here
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")

def get_config_dir():
    """Returns the platform-specific config directory."""
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'doi2bibtex'
    # Assume Linux for everything else
    return Path.home() / '.config' / 'doi2bibtex'

def get_llm_config():
    """
    Load LLM configuration from the user's config directory.
    Creates a default config if one doesn't exist.
    """
    config_dir = get_config_dir()
    config_file = config_dir / 'config.json'
    
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found. Creating a default at '{config_file}'.")
        default_config = {
            "llm": {
                "provider": "ollama",
                "ollama": {
                    "url": "http://localhost:11434/api/generate",
                    "model": "llama3",
                    "timeout": 60
                }
            }
        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    except json.JSONDecodeError:
        print(f"Error decoding {config_file}. Please check its format.")
        return None
