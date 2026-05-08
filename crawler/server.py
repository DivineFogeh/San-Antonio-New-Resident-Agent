"""
server.py

Entry point — starts the FastAPI server with uvicorn.

Usage:
    python server.py                  # default: localhost:8000
    python server.py --port 8080
    python server.py --host 0.0.0.0   # expose on all interfaces (for Docker)
    python server.py --reload         # auto-reload on code changes (dev mode)
"""

import argparse
import sys

import uvicorn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SA Resident Agent — API Server")
    parser.add_argument("--host",   default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port",   default=8000, type=int, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true",   help="Enable auto-reload (dev mode)")
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"\n{'='*55}")
    print(f"  SA Resident Agent API")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Swagger UI → http://{args.host}:{args.port}/docs")
    print(f"{'='*55}\n")

    uvicorn.run(
        "sa_resident_agent.api.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="warning",   # uvicorn's own logs — our app logs handle the rest
    )


if __name__ == "__main__":
    main()
