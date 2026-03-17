# 🛠️ Codefix-CLI

AI-powered CLI for professional code analysis, fixing, and explanation. Built for speed, security, and developer productivity.

---

### Key Features

- **⚡ Real-time Analysis**: Static code analysis powered by the Python `ast` module.
- **🤖 LLM-Powered Fixes**: Intelligent code correction using local Ollama models.
- **🛡️ Sandboxed Execution**: Test and verify code behaviors securely in a runtime sandbox.
- **🎨 Modern TUI**: Intuitive terminal interface built with the Textual framework.
- **📋 Clipboard Integration**: Seamlessly copy/paste code and output using `pyperclip`.
- **🕒 Action History**: Keep track of your last 5 code snippets and analysis results.
- **📂 Save to Desktop**: Export your corrected code to your Desktop with a single click.
- **🌍 Multi-Language Support**: Built-in syntax highlighting for Python, JavaScript, C++, and Bash.

---

## Installation

### Method 1: Local Installation (Recommended for now)

This is the standard `pip` way to install the package from the source folder.

```bash
pip install .
```

### Method 2: Git Installation (Remote)

Install directly from GitHub without cloning:

```bash
pip install git+https://github.com/praxhub/Codefix-CLI.git
```

---

## Global Installation (Publishing to PyPI)

To enable the command **`pip install codefixcli`** for everyone on any computer, the package must be uploaded to the official Python registry (PyPI). 

I have already verified that the name **`codefixcli`** is **available**. 

### How to publish:

1. **Install Build Tools**:
   ```bash
   pip install build twine
   ```

2. **Build the Package**:
   ```bash
   python -m build
   ```

3. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

Once you run these commands, you can install it anywhere using:
```bash
pip install codefixcli
```

---

## Verify Installation

After installation, the `codefixcli` command should be available in your terminal.

```bash
codefixcli
```

---

## Troubleshooting

### 'codefixcli' command not found
If you encounter this error on Windows, ensure your Python Scripts folder is in your **PATH**. 
Typical path: `%APPDATA%\Python\Python310\Scripts`.

### Ollama Connection Error
Ensure **Ollama** is running locally and that you have pulled the required model:
```bash
ollama run qwen2.5-coder:0.5b
```

---

## License

MIT License - see the [LICENSE](LICENSE) file for details.
