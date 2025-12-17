import httpx
import json
import os
from .base import LLMProvider

class GroqProvider(LLMProvider):
    """Provider for Groq."""
    def get_completion(self, prompt, **kwargs):
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                api_key = os.getenv('GROQ_API_KEY')

            if not api_key:
                print("LLM Error: API key not found in configuration or environment variable.")
                return None

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            with httpx.Client(timeout=self.config.get('timeout', 60)) as client:
                response = client.post(
                    f"https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": self.config.get('model_name', 'llama3-8b-8192'),
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.get('temperature', 0.7),
                        "max_tokens": self.config.get('max_tokens', 1024),
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print("LLM Error: Authentication failed. Please check your API key.")
            elif e.response.status_code == 429:
                print("LLM Error: Rate limit exceeded. Please try again later.")
            else:
                print(f"LLM Error: Received status {e.response.status_code} from Groq API.")
            return None
        except httpx.RequestError as e:
            print("LLM Error: Could not connect to Groq API.")
            return None
        except (json.JSONDecodeError, KeyError, IndexError):
            print("LLM Error: Failed to parse response from Groq API.")
            return None
        except Exception as e:
            print(f"An unexpected LLM error occurred: {e}")
            return None
