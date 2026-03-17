"""
LLM Integration Module - Codefix CLI
-----------------------------------
Handles interaction with the Ollama local API for code fixing and explanation.
"""
import subprocess
import tomli as _tomli
import os
import requests
import json

import sys

def _load_settings():
    """Load settings from package resources or local file."""
    if sys.version_info >= (3, 9):
        from importlib.resources import files
        try:
            path = files('codefixcli').joinpath('settings.toml')
            with path.open("rb") as f:
                return _tomli.load(f)
        except Exception:
            pass

    # Fallback to local file
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.toml"))
    try:
        with open(path, "rb") as f:
            return _tomli.load(f)
    except Exception:
        # If all else fails, return defaults or empty
        return {}

def ask_ollama(prompt: str) -> str:
    """Send a prompt to the local Ollama instance and return the response text."""
    cfg = _load_settings()
    model = cfg.get("model", "qwen2.5Coder:0.5b")
    timeout = int(cfg.get("timeout_sec", 40))
    host = cfg.get("ollama_host", "http://localhost:11434")
    
    # Try API method first (more reliable)
    try:
        response = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": cfg.get("temperature", 0.0),
                    "num_predict": cfg.get("max_tokens", 512)
                }
            },
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.RequestException:
        # Fallback to subprocess method
        cmd = ["ollama", "run", model]

        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )

        if proc.returncode != 0:
            raise RuntimeError(f"Ollama error: {proc.stderr}")

        out = proc.stdout or ""
        out = out.replace("```python", "").replace("```diff", "")
        out = out.replace("```", "")
        return out.strip()

def build_prompt(code: str, ast_data: dict, runtime_data: dict) -> str:
    """Build a detailed prompt for the LLM based on the code and mode."""
    return (
        "You are CODEFIX. Generate ONLY a unified diff patch.\n"
        "No explanations. No comments. No markdown.\n\n"
        "CODE:\n"
        f"{code}\n\n"
        "AST ANALYSIS:\n"
        f"{ast_data}\n\n"
        "RUNTIME ANALYSIS:\n"
        f"{runtime_data}\n\n"
        "Return ONLY unified diff patch:"
    )
