
---

# CODEFIX-CLI — Local AI-Assisted Python Debugger

CODEFIX-CLI is a lightweight, local-first Python debugging assistant. It helps analyze Python code, detect syntax and runtime issues, and generate meaningful fix suggestions using deterministic analysis and optional local language models. The tool is designed to run entirely on your machine, with no cloud dependency unless explicitly configured.

---

## Features

* Local AST-based static analysis
* Sandboxed execution for safe runtime testing
* Optional LLM-assisted fixes using local models
* Clear, human-readable explanations of issues
* Interactive terminal-based user interface
* Clipboard integration for faster workflows
* Local-first by default, privacy-preserving design

---

## What This Tool Is

CODEFIX-CLI launches an interactive **terminal user interface (TUI)**.
It is not a traditional argument-based CLI.

You start the tool with:

```bash
codefix
```

All interactions such as pasting code, analyzing, and fixing are done inside the interface.

---

## System Requirements

* Python 3.8 or newer
* pip
* Linux, macOS, or Windows

No internet access is required for core functionality.

---

## Dependencies

The following third-party libraries are required:

```txt
textual>=0.50.0
rich>=13.0.0
pyperclip>=1.8.0
requests>=2.28.0
tomli>=2.0.0
```

Standard Python libraries such as `ast`, `os`, `sys`, `subprocess`, and `tempfile` are not listed.

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/praxhub/Codefix-CLI.git
cd Codefix-CLI
```

---

### Create a Virtual Environment (Recommended)

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

---

### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Linux / macOS Global Setup

### Make the Script Executable

```bash
chmod +x codefix.py
```

### Rename the Script (Recommended)

```bash
mv codefix.py codefix
```

### Add to PATH

```bash
mkdir -p ~/bin
ln -sf "$(pwd)/codefix" ~/bin/codefix
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.profile
source ~/.profile
```

### Verify

```bash
which codefix
codefix
```

---

## Windows Setup

Windows requires a small launcher file.

### Create a Launcher

Create `codefix.bat` in the project directory:

```bat
@echo off
python "%~dp0codefix.py"
```

---

### Add Project Folder to PATH

* Press `Win + R`, type `sysdm.cpl`, press Enter
* Open **Advanced → Environment Variables**
* Under **User variables**, edit **Path**
* Add the full path to the CODEFIX-CLI directory
* Restart the terminal

---

### Verify

```cmd
codefix
```

---

## Usage

Launch the tool:

```bash
codefix
```

Inside the interface you can:

* Paste Python code
* Analyze it using AST and sandbox execution
* Generate corrected versions of the code
* Copy results back to your editor

---

## Optional: Install Qwen 2.5 Coder (0.5B) with Ollama

CODEFIX-CLI supports optional **local LLM-assisted debugging** using **Ollama**.
This allows the tool to generate fixes using **Qwen 2.5 Coder (0.5B)** entirely offline.

This step is optional.
If skipped, CODEFIX-CLI will still function using AST and sandbox analysis only.

---

## What Is Ollama

Ollama is a local LLM runtime that allows you to run language models on your own machine.

* No cloud usage
* No API keys
* Models run locally
* Works offline after download

CODEFIX-CLI communicates with Ollama through a local HTTP endpoint.

---

## Installing Ollama

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify installation:

```bash
ollama --version
```

Start the Ollama service:

```bash
ollama serve
```

Leave this running in the background.

---

### Windows

1. Download the installer from
   [https://ollama.com/download](https://ollama.com/download)

2. Install Ollama using the installer.

3. Verify installation:

```powershell
ollama --version
```

Ollama runs automatically as a background service on Windows.

---

## Downloading Qwen 2.5 Coder (0.5B)

Pull the model using Ollama:

```bash
ollama pull qwen2.5-coder:0.5b
```

Verify:

```bash
ollama list
```

You should see:

```text
qwen2.5-coder:0.5b
```

---

## Testing the Model (Optional)

```bash
ollama run qwen2.5-coder:0.5b
```

Exit with `Ctrl + D`.

---

## How CODEFIX-CLI Uses the Model

When enabled, CODEFIX-CLI:

* Sends analyzed code and error context to Ollama
* Requests corrected Python code
* Extracts only the fixed output
* Displays results inside the TUI

No data leaves your system.

---

## Configuration

Optional configuration can be placed in `settings.toml`.

Example:

```toml
[general]
log_level = "INFO"
```

LLM-related behavior is handled internally in the `debugger` module.

---

## Privacy and Design Philosophy

* No telemetry
* No forced network access
* No external API usage by default
* All analysis runs locally

CODEFIX-CLI is designed for developers who want control, transparency, and predictable behavior.

---

## Uninstallation

### Linux / macOS

```bash
rm ~/bin/codefix
rm -rf Codefix-CLI
```

### Windows

* Delete the project directory
* Remove it from PATH

---

## License

MIT License

Copyright (c) 2025 Prabhu Balaji

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Contributing

Bug reports and pull requests are welcome.

* [https://github.com/praxhub/Codefix-CLI/issues](https://github.com/praxhub/Codefix-CLI/issues)

---
