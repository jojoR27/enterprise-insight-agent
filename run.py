import asyncio
import sys

import uvicorn


def main() -> None:
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        loop="asyncio",
    )

    server = uvicorn.Server(config)

    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(server.serve())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    else:
        try:
            asyncio.run(server.serve())
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()