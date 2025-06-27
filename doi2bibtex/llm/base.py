import httpx
import json
import sys
from pathlib import Path
import doi2bibtex.interact as interact

# --- Provider Classes ---

class LLMProvider:
    """Base class for LLM providers."""
    def __init__(self, model_config):
        self.config = model_config

    def get_completion(self, prompt, **kwargs):
        """Get completion from the LLM. Must be implemented by subclasses."""
        raise NotImplementedError

    def test_connection(self):
        """Test the connection to the LLM provider. Must be implemented by subclasses."""
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    """Provider for Ollama."""
    def get_completion(self, prompt, **kwargs):
        try:
            with httpx.Client(timeout=self.config.get('timeout', 60)) as client:
                response = client.post(
                    self.config.get('url'),
                    json={
                        "model": self.config.get('model_name'),
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                return json.loads(response.text)['response']
        except httpx.HTTPStatusError as e:
            print(f"LLM Error: Received status {e.response.status_code} from {e.request.url}.")
            print("Please check the URL and ensure the Ollama server is running and the model is available.")
            return None
        except httpx.RequestError as e:
            print(f"LLM Error: Could not connect to Ollama at {self.config.get('url')}.")
            print("Please ensure the server is running and accessible.")
            return None
        except json.JSONDecodeError:
            print("LLM Error: Failed to decode the response from Ollama.")
            return None
        except Exception as e:
            print(f"An unexpected LLM error occurred: {e}")
            return None

# --- Configuration Management ---

def get_config_dir():
    """Returns the platform-specific config directory."""
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'doi2bibtex'
    return Path.home() / '.config' / 'doi2bibtex'

def get_config_path():
    """Returns the full path to the config.json file."""
    return get_config_dir() / 'config.json'

def _create_default_config():
    """Creates and saves a default config file, returning the config object."""
    config_path = get_config_path()
    print(f"Creating a default config file at '{config_path}'.")
    default_config = {
        "default_model": "ollama_default",
        "models": {
            "ollama_default": {
                "provider": "ollama",
                "url": "http://localhost:11434/api/generate",
                "model_name": "llama3",
                "timeout": 60
            }
        }
    }
    save_llm_config(default_config)
    return default_config

def load_llm_config():
    """
    Loads the LLM configuration from the user's config directory.
    Handles file not found and malformed JSON errors.
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        return _create_default_config()

    try:
        with config_path.open('r') as f:
            config = json.load(f)
            # Basic validation
            if 'default_model' not in config or 'models' not in config:
                raise json.JSONDecodeError("Missing required keys: 'default_model' or 'models'", "", 0)
            return config
    except json.JSONDecodeError as e:
        print(f"Error: The configuration file at {config_path} is not valid: {e.msg}")
        if interact.ask("Do you want to replace it with a default configuration? (This will overwrite the existing file)"):
            return _create_default_config()
        else:
            print("Aborting. Please fix the configuration file manually.")
            return None

def save_llm_config(config):
    """Saves the configuration object to the config file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open('w') as f:
        json.dump(config, f, indent=4)

# --- Provider Factory ---

def get_llm_provider(model_name=None):
    """
    Factory function to get an LLM provider instance.
    If model_name is None, it uses the default model from the config.
    """
    config = load_llm_config()
    if not config:
        return None

    if not model_name:
        model_name = config.get('default_model')
        if not model_name:
            print("LLM Error: No default model specified in config.")
            return None
    
    model_config = config.get('models', {}).get(model_name)
    if not model_config:
        print(f"LLM Error: Model '{model_name}' not found in config.")
        return None

    provider_name = model_config.get('provider', '').lower()
    if provider_name == 'ollama':
        return OllamaProvider(model_config)
    else:
        print(f"LLM Error: Unknown provider '{provider_name}' for model '{model_name}'.")
        return None
