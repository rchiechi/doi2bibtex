import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from . import doi2bibtex

async def web_server(addr, port):
    config = Config()
    config.bind = [f"{addr}:{port}"]
    config.worker_class = "asyncio"
    config.trusted_proxy = '*'
    config.forwarded_allow_ips = '*'
    await serve(doi2bibtex.app, config)