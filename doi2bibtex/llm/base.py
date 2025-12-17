# --- Base Provider Classes ---

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

