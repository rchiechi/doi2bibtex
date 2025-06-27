from .base import load_llm_config, save_llm_config
from colorama import Fore, Style
import sys

def list_models():
    """List all configured LLM models."""
    config = load_llm_config()
    if not config:
        sys.exit(1)
    default_model = config.get('default_model')
    print(f"{Style.BRIGHT}Available LLM Models:{Style.RESET_ALL}")
    for name, model_config in config.get('models', {}).items():
        if name == default_model:
            print(f"  - {Style.BRIGHT}{Fore.GREEN}{name} (default){Style.RESET_ALL}")
        else:
            print(f"  - {name}")
        print(f"    - Provider: {model_config.get('provider')}")
        print(f"    - URL: {model_config.get('url')}")
        print(f"    - Model: {model_config.get('model_name')}")

def add_model():
    """Interactively add a new LLM model configuration."""
    config = load_llm_config()
    if not config:
        sys.exit(1)
    print("Enter new model details (leave blank to cancel):")
    
    name = input("Configuration Name (e.g., 'ollama_mistral'): ")
    if not name:
        return
    
    provider = input("Provider (e.g., 'ollama'): ").lower()
    if not provider:
        return
        
    url = input("URL (e.g., 'http://localhost:11434/api/generate'): ")
    if not url:
        return

    model_name = input("Model Name (e.g., 'mistral'): ")
    if not model_name:
        return

    new_model = {
        "provider": provider,
        "url": url,
        "model_name": model_name,
        "timeout": 60
    }
    
    if 'models' not in config:
        config['models'] = {}
    config['models'][name] = new_model
    save_llm_config(config)
    print(f"{Style.BRIGHT}{Fore.GREEN}Model '{name}' added successfully.{Style.RESET_ALL}")

def remove_model():
    """Interactively remove an LLM model configuration."""
    config = load_llm_config()
    if not config:
        sys.exit(1)
    list_models()
    name = input("Enter the name of the model to remove: ")
    
    if name in config.get('models', {}):
        if name == config.get('default_model'):
            print(f"{Fore.RED}Cannot remove the default model. Please set a new default first.{Style.RESET_ALL}")
            return
        del config['models'][name]
        save_llm_config(config)
        print(f"{Style.BRIGHT}{Fore.GREEN}Model '{name}' removed.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Model '{name}' not found.{Style.RESET_ALL}")

def set_default_model():
    """Interactively set the default LLM model."""
    config = load_llm_config()
    if not config:
        sys.exit(1)
    list_models()
    name = input("Enter the name of the model to set as default: ")
    
    if name in config.get('models', {}):
        config['default_model'] = name
        save_llm_config(config)
        print(f"{Style.BRIGHT}{Fore.GREEN}'{name}' is now the default model.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Model '{name}' not found.{Style.RESET_ALL}")

def llm_config_main(args):
    """Main function for the llm-config command."""
    if args.llm_action == 'list':
        list_models()
    elif args.llm_action == 'add':
        add_model()
    elif args.llm_action == 'rm':
        remove_model()
    elif args.llm_action == 'default':
        set_default_model()
    else:
        print(f"Unknown action: {args.llm_action}")
