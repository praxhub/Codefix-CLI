#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual.widgets import Static, Button, TextArea, Footer, Select, Label
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import work
from rich.text import Text
import pyperclip
import traceback
import re
import os
import datetime

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
def _load_cfg():
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
        yield Static("CODEFIX CLI  v2.0", id="subtitle")
        yield Static("Paste code → Analyze / Fix / Explain", id="info")

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
        yield Footer()

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
                # Strip rich markup tags for clipboard
                clean = re.sub(r"\[/?[a-zA-Z0-9_ #/=]+\]", "", self._last_output)
                try:
                    pyperclip.copy(clean)
                    self._set_status("Output copied to clipboard ✓")
                except Exception:
                    self._set_status("Could not copy — clipboard unavailable")
            else:
                self._set_status("Nothing to copy yet")

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

    # ── History navigation ────────────────────────────────────────────────────
    def _history_navigate(self, direction: int):
        if not self._history:
            self._set_status("History is empty")
            return
        self._hist_idx = max(0, min(len(self._history) - 1, self._hist_idx + direction))
        self.query_one("#input", TextArea).text = self._history[self._hist_idx]
        self._set_status(f"History [{self._hist_idx + 1}/{len(self._history)}]")

    # ── Save output ───────────────────────────────────────────────────────────
    def _save_output(self):
        if not self._last_output:
            self._set_status("Nothing to save yet")
            return
        clean = re.sub(r"\[/?[a-zA-Z0-9_ #/=]+\]", "", self._last_output)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desktop, exist_ok=True)
        path = os.path.join(desktop, f"codefix_output_{stamp}.py")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(clean)
            self._set_status(f"Saved → {path}")
        except Exception as e:
            self._set_status(f"Save failed: {e}")

    # ── Analyze ───────────────────────────────────────────────────────────────
    @work(thread=True)
    def run_analyze(self):
        self.call_from_thread(self._set_status, "Analyzing…")
        self.call_from_thread(
            self.query_one("#output", Static).update,
            "[#9370db]Analyzing code…[/#9370db]"
        )
        try:
            code = self.query_one("#input", TextArea).text
            ast_res  = scan(code)
            run_res  = run_in_sandbox(code)

            parts = ["[bold #9370db]=== CODE ANALYSIS ===[/bold #9370db]"]

            # ── AST section ───────────────────────────────────────────────────
            parts.append("\n[bold #cba6f7]▸ AST ANALYSIS[/bold #cba6f7]")
            if ast_res.get("ok"):
                issues = ast_res.get("issues", [])
                if issues:
                    for iss in issues:
                        ln = iss.get("lineno", "?")
                        parts.append(f"  [yellow]⚠[/yellow] {iss['message']}  [dim](line {ln})[/dim]")
                else:
                    parts.append("  [green]✓ No issues found[/green]")
            else:
                err = ast_res.get("syntax_error", {})
                parts.append(f"  [red]✗ Syntax Error: {err.get('msg', 'Unknown')} (line {err.get('lineno', '?')})[/red]")

            # ── Complexity section ─────────────────────────────────────────────
            complexity = ast_res.get("complexity", {})
            if complexity:
                parts.append("\n[bold #cba6f7]▸ COMPLEXITY[/bold #cba6f7]")
                for fn, score in complexity.items():
                    bar = "█" * min(score, 20)
                    colour = "green" if score < 5 else ("yellow" if score < 10 else "red")
                    parts.append(f"  {fn}(): [{colour}]{bar}[/{colour}] [{colour}]{score}[/{colour}]")

            # ── Runtime section ───────────────────────────────────────────────
            parts.append("\n[bold #cba6f7]▸ RUNTIME ANALYSIS[/bold #cba6f7]")
            if run_res.get("ok"):
                elapsed = run_res.get("elapsed", 0)
                parts.append(f"  [green]✓ Return code: {run_res.get('returncode', 0)}[/green]  [dim]⏱ {elapsed}s[/dim]")
                if run_res.get("stdout"):
                    parts.append(f"  [dim]stdout:[/dim]\n{run_res['stdout'].strip()}")
                if run_res.get("stderr"):
                    parts.append(f"  [red]stderr:\n{run_res['stderr'].strip()}[/red]")
            else:
                if run_res.get("timeout"):
                    parts.append("  [red]✗ Timeout during execution[/red]")
                else:
                    parts.append(f"  [red]✗ {run_res.get('error', 'Unknown error')}[/red]")

            out = "\n".join(parts)
            self.call_from_thread(self._set_output, out)
            self.call_from_thread(self._set_status, "Analysis complete ✓")

        except Exception as e:
            err_text = f"[red]Error:[/red]\n{e}\n\n{traceback.format_exc()}"
            self.call_from_thread(self._set_output, err_text)
            self.call_from_thread(self._set_status, "Analysis failed")

    # ── Fix ───────────────────────────────────────────────────────────────────
    @work(thread=True)
    def run_fix(self):
        self.call_from_thread(self._set_status, "Fixing with LLM…")
        self.call_from_thread(
            self.query_one("#output", Static).update,
            "[#9370db]Fixing code with Qwen2.5…[/#9370db]"
        )
        try:
            code    = self.query_one("#input", TextArea).text
            ast_res = scan(code)
            run_res = run_in_sandbox(code)

            prompt = (
                "You are an expert Python debugger. Fix all bugs in the code below.\n"
                "Return ONLY the corrected Python code, nothing else.\n\n"
                f"CODE:\n{code}\n\n"
                f"AST ANALYSIS:\n{ast_res}\n\n"
                f"RUNTIME ANALYSIS:\n{run_res}\n\n"
                "RETURN ONLY THE FIXED CODE:"
            )
            llm_out = ask_ollama(prompt)

            # Extract code block
            fixed = llm_out
            for pattern in [r'```python\s*(.*?)```', r'```\s*(.*?)```']:
                m = re.findall(pattern, llm_out, re.DOTALL)
                if m:
                    fixed = m[0]
                    break
            fixed = fixed.strip()

            parts = [
                "[bold #9370db]=== FIXED CODE ===[/bold #9370db]",
                "",
                fixed,
            ]
            out = "\n".join(parts)
            self.call_from_thread(self._set_output, out)
            self.call_from_thread(self._set_status, "Fix complete ✓")

        except Exception as e:
            err_text = f"[red]Error:[/red]\n{e}\n\n{traceback.format_exc()}"
            self.call_from_thread(self._set_output, err_text)
            self.call_from_thread(self._set_status, "Fix failed")

    # ── Explain ───────────────────────────────────────────────────────────────
    @work(thread=True)
    def run_explain(self):
        self.call_from_thread(self._set_status, "Explaining with LLM…")
        self.call_from_thread(
            self.query_one("#output", Static).update,
            "[#9370db]Explaining code with Qwen2.5…[/#9370db]"
        )
        try:
            code = self.query_one("#input", TextArea).text
            if not code.strip():
                self.call_from_thread(self._set_output, "[yellow]No code to explain.[/yellow]")
                self.call_from_thread(self._set_status, "Nothing to explain")
                return

            prompt = (
                "You are a helpful coding assistant. Explain the following code in plain English.\n"
                "Be concise. Use bullet points for each major section or function.\n"
                "Do NOT output any code, only a clear explanation.\n\n"
                f"CODE:\n{code}\n\n"
                "EXPLANATION:"
            )
            explanation = ask_ollama(prompt)

            parts = [
                "[bold #9370db]=== CODE EXPLANATION ===[/bold #9370db]",
                "",
                explanation.strip(),
            ]
            out = "\n".join(parts)
            self.call_from_thread(self._set_output, out)
            self.call_from_thread(self._set_status, "Explanation complete ✓")

        except Exception as e:
            err_text = f"[red]Error:[/red]\n{e}\n\n{traceback.format_exc()}"
            self.call_from_thread(self._set_output, err_text)
            self.call_from_thread(self._set_status, "Explain failed")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CodeFixApp()
    app.run()
