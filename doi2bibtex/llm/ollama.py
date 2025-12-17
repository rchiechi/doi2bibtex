import httpx
import json
from .base import LLMProvider

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