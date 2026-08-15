#!/usr/bin/env python3
"""
Codefix CLI - Main Application Entry Point
------------------------------------------
This module provides the Textual-based TUI for analyzing and fixing Python code.
"""

from textual.app import App, ComposeResult
from textual.widgets import Static, Button, TextArea, Footer, Select, Label
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import work
from rich.text import Text
from rich.markup import escape
import pyperclip
import traceback
import re
import os
import datetime

try:
    from .debugger import (
        scan,
        run_in_sandbox,
        build_prompt,
        ask_ollama,
        extract_unified_diff,
        apply_patch,
    )
except ImportError:
    from debugger import (
        scan,
        run_in_sandbox,
        build_prompt,
        ask_ollama,
        extract_unified_diff,
        apply_patch,
    )

# ── Settings ──────────────────────────────────────────────────────────────────
import tomli as _tomli
import sys

def _load_cfg():
    """Load configuration from package resources or local file."""
    if sys.version_info >= (3, 9):
        from importlib.resources import files
        try:
            path = files('codefixcli').joinpath('settings.toml')
            with path.open("rb") as f:
                return _tomli.load(f)
        except Exception:
            pass
    
    # Fallback to local file
    path = os.path.join(os.path.dirname(__file__), "settings.toml")
    try:
        with open(path, "rb") as f:
            return _tomli.load(f)
    except Exception:
        return {}

# ── Logo ──────────────────────────────────────────────────────────────────────
LOGO = [
    "██████╗ ██████╗ ██████╗ ███████╗███████╗██╗██╗  ██╗     ██████╗██╗     ██╗",
    "██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██║╚██╗██╔╝    ██╔════╝██║     ██║",
    "██║     ██║   ██║██║  ██║█████╗  █████╗  ██║ ╚███╔╝     ██║     ██║     ██║",
    "██║     ██║   ██║██║  ██║██╔══╝  ██╔══╝  ██║ ██╔██╗     ██║     ██║     ██║",
    "╚██████╗╚██████╔╝██████╔╝███████╗██║     ██║██╔╝ ██╗    ╚██████╗███████╗██║",
    " ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝     ╚═════╝╚══════╝╚═╝",
]

LANGUAGES = [
    ("Python",     "python"),
    ("JavaScript", "javascript"),
    ("C++",        "cpp"),
    ("Bash",       "bash"),
    ("Plain text", ""),
]

MAX_HISTORY = 5

# ── Logo widget ───────────────────────────────────────────────────────────────
class LogoWidget(Static):
    """Widget for displaying the application logo."""
    def render(self):
        t = Text()
        for line in LOGO:
            for char in line:
                if char != ' ':
                    t.append(char, style="bold #9370db")
                else:
                    t.append(char)
            t.append("\n")
        return t


# ── Main app ──────────────────────────────────────────────────────────────────
class CodeFixApp(App):
    """The main Codefix TUI Application."""
    CSS = """
    Screen {
        layout: vertical;
        background: #1e1e2e;
    }
    #logo {
        text-align: center;
        margin-top: 1;
        margin-bottom: 0;
        height: auto;
        color: #9370db;
    }
    #subtitle {
        text-align: center;
        color: #cba6f7;
        margin-bottom: 0;
        height: auto;
    }
    #info {
        text-align: center;
        color: #6c7086;
        margin-bottom: 1;
        height: auto;
    }
    #toolbar {
        height: auto;
        margin-bottom: 0;
        padding: 0 1;
        align: left middle;
    }
    #lang_label {
        color: #a9a9a9;
        padding: 0 1;
        height: 3;
        content-align: center middle;
    }
    Select {
        width: 20;
        height: 3;
        background: #313244;
        border: solid #9370db;
        color: #f0f0f0;
    }
    Select:focus {
        border: solid #cba6f7;
    }
    #main_container {
        layout: horizontal;
        height: 1fr;
    }
    #input_box {
        border: solid #9370db;
        width: 50%;
        padding: 0;
        height: 1fr;
        background: #313244;
    }
    #output_box {
        border: solid #9370db;
        width: 50%;
        padding: 1;
        height: 1fr;
        margin-left: 1;
        background: #313244;
        color: #f0f0f0;
    }
    #buttons {
        height: auto;
        content-align: center middle;
        margin-top: 1;
        margin-bottom: 0;
        padding: 0 1;
    }
    Button {
        background: #9370db;
        color: #ffffff;
        border: none;
        margin: 0 1;
        min-width: 10;
    }
    Button:hover {
        background: #cba6f7;
        color: #1e1e2e;
    }
    Button.-history {
        background: #45475a;
        min-width: 4;
        margin: 0;
    }
    Button.-history:hover {
        background: #585b70;
    }
    #status_bar {
        height: 1;
        background: #181825;
        color: #6c7086;
        padding: 0 1;
    }
    """

    # ── State ─────────────────────────────────────────────────────────────────
    _history: list[str] = []
    _hist_idx: int = -1
    _last_output: str = ""
    _current_lang: str = "python"

    def compose(self) -> ComposeResult:
        cfg = _load_cfg()
        model = cfg.get("model", "qwen2.5-coder:0.5b")

        yield LogoWidget(id="logo")
        yield Static("✨ CODEFIX CLI v2.0 ✨", id="subtitle")
        yield Static("━━━━━ Paste code → Analyze / Fix / Explain ━━━━━", id="info")

        # Language picker toolbar
        with Horizontal(id="toolbar"):
            yield Label("  Lang:", id="lang_label")
            yield Select(
                [(lang, val) for lang, val in LANGUAGES],
                value="python",
                id="lang_select",
            )

        # Main panels
        with Horizontal(id="main_container"):
            with ScrollableContainer(id="input_box"):
                yield TextArea(id="input", language="python")
            with ScrollableContainer(id="output_box"):
                yield Static("", id="output")

        # Button bar
        with Horizontal(id="buttons"):
            yield Button("Analyze",      id="analyze",      variant="primary")
            yield Button("Fix",          id="fix",          variant="success")
            yield Button("Explain",      id="explain",      variant="default")
            yield Button("Copy Output",  id="copy_output",  variant="default")
            yield Button("Save",         id="save",         variant="default")
            yield Button("Paste",        id="paste",        variant="default")
            yield Button("Clear",        id="clear",        variant="warning")
            yield Button("◀",            id="hist_prev",    classes="history")
            yield Button("▶",            id="hist_next",    classes="history")
            yield Button("Quit",         id="quit",         variant="error")

        yield Static(f"  Model: {model}  │  Ready", id="status_bar")
        footer = Footer()
        yield footer

    def on_mount(self) -> None:
        self.bind("ctrl+q", "quit", description="Quit")
        self.bind("ctrl+a", "analyze", description="Analyze")
        self.bind("ctrl+f", "fix", description="Fix")
        self.bind("ctrl+e", "explain", description="Explain")
        self.bind("ctrl+c", "copy_output", description="Copy Output")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _set_status(self, msg: str):
        cfg = _load_cfg()
        model = cfg.get("model", "qwen2.5-coder:0.5b")
        self.query_one("#status_bar", Static).update(f"  Model: {model}  │  {msg}")

    def _set_output(self, text: str):
        self._last_output = text
        self.query_one("#output", Static).update(text)

    def _push_history(self, code: str):
        if not code.strip():
            return
        if self._history and self._history[-1] == code:
            return
        self._history.append(code)
        if len(self._history) > MAX_HISTORY:
            self._history.pop(0)
        self._hist_idx = len(self._history) - 1

    # ── Language selector ─────────────────────────────────────────────────────
    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "lang_select":
            lang = event.value
            self._current_lang = lang
            ta = self.query_one("#input", TextArea)
            try:
                if lang:
                    ta.language = lang
                else:
                    ta.language = None
            except Exception:
                pass

    # ── Button dispatcher ─────────────────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses in the TUI."""
        bid = event.button.id

        if bid == "quit":
            self.exit()

        elif bid == "paste":
            try:
                text = pyperclip.paste()
                self.query_one("#input", TextArea).text = text
                self._set_status("Pasted from clipboard")
            except Exception:
                self._set_output("[red]Could not paste from clipboard[/red]")

        elif bid == "clear":
            self.query_one("#input", TextArea).text = ""
            self._set_output("")
            self._set_status("Cleared")

        elif bid == "copy_output":
            if self._last_output:
                clean = re.sub(r"\[/?[a-zA-Z0-9_ #/=]+\]", "", self._last_output)
                try:
                    pyperclip.copy(clean)
                    self._set_status("Output copied to clipboard ✓")
                except Exception:
                    self._set_status("Could not copy — clipboard unavailable")

        elif bid == "save":
            self._save_output()

        elif bid == "analyze":
            code = self.query_one("#input", TextArea).text
            self._push_history(code)
            self.run_analyze()

        elif bid == "fix":
            code = self.query_one("#input", TextArea).text
            self._push_history(code)
            self.run_fix()

        elif bid == "explain":
            code = self.query_one("#input", TextArea).text
            self._push_history(code)
            self.run_explain()

        elif bid == "hist_prev":
            self._history_navigate(-1)

        elif bid == "hist_next":
            self._history_navigate(+1)

    # ... (remaining methods implemented the same as before)
    def _history_navigate(self, direction: int):
        if not self._history:
            return
        self._hist_idx = max(0, min(len(self._history) - 1, self._hist_idx + direction))
        self.query_one("#input", TextArea).text = self._history[self._hist_idx]

    def _save_output(self):
        if not self._last_output: return
        clean = re.sub(r"\[/?[a-zA-Z0-9_ #/=]+\]", "", self._last_output)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"codefix_{stamp}.py")
        with open(path, "w") as f: f.write(clean)
        self._set_status(f"Saved to {path}")

    @work(thread=True)
    def run_analyze(self):
        self.call_from_thread(self._set_status, "Analyzing…")
        try:
            code = self.query_one("#input", TextArea).text
            ast_res  = scan(code)
            run_res  = run_in_sandbox(code)
            out = f"[bold]=== ANALYSIS ===[/bold]\n\nAST: {escape(str(ast_res))}\n\nRuntime: {escape(str(run_res))}"
            self.call_from_thread(self._set_output, out)
            self.call_from_thread(self._set_status, "Done ✓")
        except Exception as e:
            self.call_from_thread(self._set_output, escape(str(e)))

    @work(thread=True)
    def run_fix(self):
        self.call_from_thread(self._set_status, "Fixing…")
        try:
            code = self.query_one("#input", TextArea).text
            llm_out = ask_ollama(build_prompt(code, scan(code), run_in_sandbox(code)))
            self.call_from_thread(self._set_output, escape(llm_out))
            self.call_from_thread(self._set_status, "Fixed ✓")
        except Exception as e:
            self.call_from_thread(self._set_output, escape(str(e)))

    @work(thread=True)
    def run_explain(self):
        self.call_from_thread(self._set_status, "Explaining…")
        try:
            code = self.query_one("#input", TextArea).text
            llm_out = ask_ollama(f"Explain this code concisely:\n{code}")
            self.call_from_thread(self._set_output, escape(llm_out))
            self.call_from_thread(self._set_status, "Explained ✓")
        except Exception as e:
            self.call_from_thread(self._set_output, escape(str(e)))

def main():
    CodeFixApp().run()

if __name__ == "__main__":
    main()
