#!/usr/bin/env python3
"""
Simple script to run the AI Voice Agent System
Provides easy command-line options for different run modes
"""

import sys
import subprocess
import argparse
from pathlib import Path


def get_python_executable():
  """Get the Python executable path"""
  venv_path = Path(__file__).parent / ".venv" / "bin" / "python"
  if venv_path.exists():
    return str(venv_path)
  return sys.executable


def run_with_python():
  """Run using python main.py"""
  python_exe = get_python_executable()
  cmd = [python_exe, "main.py"]
  print(f"Running: {' '.join(cmd)}")
  subprocess.run(cmd)


def run_with_uvicorn(host="0.0.0.0", port=8001, reload=True, workers=None, log_level="info"):
  """Run using uvicorn"""
  python_exe = get_python_executable()
  cmd = [python_exe, "-m", "uvicorn", "main:app",
         f"--host={host}", f"--port={port}", f"--log-level={log_level}"]

  if reload and not workers:
    cmd.append("--reload")

  if workers and workers > 1:
    cmd.extend(["--workers", str(workers)])

  print(f"Running: {' '.join(cmd)}")
  subprocess.run(cmd)


def main():
  parser = argparse.ArgumentParser(description="Run AI Voice Agent System")
  parser.add_argument("--mode", choices=["python", "uvicorn"], default="uvicorn",
                      help="Run mode (default: uvicorn)")
  parser.add_argument("--host", default="0.0.0.0", help="Host address")
  parser.add_argument("--port", type=int, default=8001, help="Port number")
  parser.add_argument("--no-reload", action="store_true",
                      help="Disable auto-reload")
  parser.add_argument("--workers", type=int,
                      help="Number of workers (production)")
  parser.add_argument("--log-level", default="info",
                      choices=["critical", "error",
                               "warning", "info", "debug"],
                      help="Log level")

  args = parser.parse_args()

  print("🚀 Starting AI Voice Agent System...")
  print(f"Mode: {args.mode}")
  print(f"URL: http://{args.host}:{args.port}")
  print("-" * 50)

  if args.mode == "python":
    run_with_python()
  else:
    run_with_uvicorn(
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        workers=args.workers,
        log_level=args.log_level
    )


if __name__ == "__main__":
  main()
