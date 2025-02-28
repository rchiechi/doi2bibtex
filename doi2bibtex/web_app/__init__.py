import asyncio
from . import doi2bibtex

try:
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    from quart import Quart, render_template, request, send_from_directory, jsonify, send_file
    import magic
    OK_TO_RUN=True
except ImportError as e:
    print(f"Error importing package, you will not be able to run the web_server: {e}")
    OK_TO_RUN=False

async def web_server(addr, port):
    if not OK_TO_RUN:
        return None
    config = Config()
    config.bind = [f"{addr}:{port}"]
    config.worker_class = "asyncio"
    config.trusted_proxy = '*'
    config.forwarded_allow_ips = '*'
    await serve(doi2bibtex.app, config)