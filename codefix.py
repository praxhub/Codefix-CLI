#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual.widgets import Static, Button, TextArea, Footer
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual import work
from rich.text import Text
import pyperclip
import traceback
import re
import tempfile
import os

from debugger import (
    scan,
    run_in_sandbox,
    build_prompt,
    ask_ollama,
    extract_unified_diff,
    apply_patch,
)

# Logo ASCII art
LOGO = [
"██████╗ ██████╗ ██████╗ ███████╗███████╗██╗██╗  ██╗     ██████╗██╗     ██╗",
"██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██║╚██╗██╔╝    ██╔════╝██║     ██║",
"██║     ██║   ██║██║  ██║█████╗  █████╗  ██║ ╚███╔╝     ██║     ██║     ██║",
"██║     ██║   ██║██║  ██║██╔══╝  ██╔══╝  ██║ ██╔██╗     ██║     ██║     ██║",
"╚██████╗╚██████╔╝██████╔╝███████╗██║     ██║██╔╝ ██╗    ╚██████╗███████╗██║",
" ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝     ╚═════╝╚══════╝╚═╝",
]

# Widget to render the logo
class LogoWidget(Static):
    def render(self):
        t = Text()
        for i, line in enumerate(LOGO):
            for char in line:
                if char != ' ':
                    # Use only ONE valid light purple color for the entire logo - NO COLOR VARIATIONS WHATSOEVER
                    t.append(char, style="bold #9370db")  # Light purple
                else:
                    t.append(char)
            t.append("\n")
        return t

# Main application class
class CodeFixApp(App):
    # CSS styling for the application
    CSS = """
    Screen {
        layout: vertical;
        background: #2f2f2f;  /* Dark gray background */
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
        color: #a9a9a9; 
        margin-bottom: 1; 
        height: auto;
    }
    #info { 
        text-align: center; 
        color: #a9a9a9; 
        margin-bottom: 1; 
        height: auto;
    }
    #main_container {
        layout: horizontal;
        height: 1fr;
    }
    #input_box { 
        border: solid #9370db; 
        width: 50%;
        padding: 1; 
        height: 1fr;
        background: #404040;  /* Darker gray */
        color: #f0f0f0;
    }
    #output_box { 
        border: solid #9370db; 
        width: 50%;
        padding: 1; 
        height: 1fr;
        margin-left: 1;
        background: #404040;  /* Darker gray */
        color: #f0f0f0;
    }
    #buttons { 
        height: auto;
        content-align: center middle; 
        margin-top: 1; 
        margin-bottom: 1;
    }
    Button {
        background: #9370db;  /* Light purple */
        color: #ffffff;  /* White */
        border: none;
    }
    Button:hover {
        background: #7b68ee;  /* Different purple on hover */
        color: #ffffff;
    }
    Button.-primary {
        background: #9370db;  /* Same purple */
    }
    Button.-success {
        background: #9370db;  /* Same purple */
    }
    Button.-warning {
        background: #9370db;  /* Same purple */
    }
    Button.-error {
        background: #9370db;  /* Same purple */
    }
    """

    # Define the layout of the application
    def compose(self) -> ComposeResult:
        yield LogoWidget(id="logo")
        yield Static("CODEFIX CLI", id="subtitle")
        yield Static("Paste code and press Analyze / Fix.", id="info")

        with Horizontal(id="main_container"):
            with ScrollableContainer(id="input_box"):
                yield TextArea(id="input", language="python")
            with ScrollableContainer(id="output_box"):
                yield Static("", id="output")

        with Horizontal(id="buttons"):
            yield Button("Analyze", id="analyze", variant="primary")
            yield Button("Fix", id="fix", variant="success")
            yield Button("Paste", id="paste", variant="default")
            yield Button("Clear", id="clear", variant="warning")
            yield Button("Quit", id="quit", variant="error")

        yield Footer()

    # Handle button press events
    def on_button_pressed(self, event: Button.Pressed):
        bid = event.button.id

        if bid == "quit":
            self.exit()

        elif bid == "paste":
            try:
                self.query_one("#input", TextArea).text = pyperclip.paste()
            except:
                self.query_one("#output", Static).update("[red]Could not paste from clipboard[/red]")

        elif bid == "clear":
            self.query_one("#input", TextArea).text = ""
            self.query_one("#output", Static).update("")

        elif bid == "analyze":
            self.run_analyze()

        elif bid == "fix":
            self.run_fix()

    # Run the analyze functionality in a separate thread
    @work(thread=True)
    def run_analyze(self):
        self.call_from_thread(self.query_one("#output", Static).update, "[#9370db]Analyzing code with Qwen2.5...[/#9370db]")
        
        try:
            code = self.query_one("#input", TextArea).text
            
            # Perform analysis
            ast_res = scan(code)
            run_res = run_in_sandbox(code)

            # Create analysis output
            output_parts = []
            
            output_parts.append("[bold #9370db]=== CODE ANALYSIS ===[/bold #9370db]")
            
            # AST Analysis
            output_parts.append("\n[bold #9370db]AST ANALYSIS:[/bold #9370db]")
            if ast_res.get("ok"):
                if ast_res.get("issues"):
                    output_parts.append("Issues found:")
                    for issue in ast_res["issues"]:
                        output_parts.append(f"  • {issue['message']} (Line {issue.get('lineno', 'N/A')})")
                else:
                    output_parts.append("  ✓ No AST issues found")
            else:
                output_parts.append(f"  [red]✗ Syntax Error: {ast_res.get('syntax_error', {}).get('msg', 'Unknown error')}[/red]")
            
            # Runtime Analysis
            output_parts.append("\n[bold #9370db]RUNTIME ANALYSIS:[/bold #9370db]")
            if run_res.get("ok"):
                output_parts.append(f"  ✓ Return code: {run_res.get('returncode', 0)}")
                if run_res.get("stdout"):
                    output_parts.append(f"  Output:\n{run_res['stdout']}")
                if run_res.get("stderr"):
                    output_parts.append(f"  [red]Errors:\n{run_res['stderr']}[/red]")
            else:
                if run_res.get("timeout"):
                    output_parts.append("  [red]✗ Timeout occurred during execution[/red]")
                else:
                    output_parts.append(f"  [red]✗ Execution failed: {run_res.get('error', 'Unknown error')}[/red]")
            
            output_text = "\n".join(output_parts)
            self.call_from_thread(self.query_one("#output", Static).update, output_text)

        except Exception as e:
            error_text = f"[red]Error:[/red]\n{e}\n\n{traceback.format_exc()}"
            self.call_from_thread(self.query_one("#output", Static).update, error_text)

    # Run the fix functionality in a separate thread
    @work(thread=True)
    def run_fix(self):
        self.call_from_thread(self.query_one("#output", Static).update, "[#9370db]Fixing code with Qwen2.5...[/#9370db]")
        
        try:
            code = self.query_one("#input", TextArea).text
            
            # Perform analysis
            ast_res = scan(code)
            run_res = run_in_sandbox(code)
            
            # Build a specific prompt for Qwen2.5 debugging
            prompt = (
                "You are an expert Python debugger. Analyze the provided code and fix any bugs.\n"
                "Return only the corrected Python code, nothing else.\n\n"
                f"CODE:\n{code}\n\n"
                f"AST ANALYSIS:\n{ast_res}\n\n"
                f"RUNTIME ANALYSIS:\n{run_res}\n\n"
                "FIX THE CODE AND RETURN ONLY THE CORRECTED PYTHON CODE:"
            )
            
            llm_out = ask_ollama(prompt)

            # Extract fixed code from the LLM response
            fixed_code = llm_out
            
            # Try to extract Python code from the response
            python_pattern = r'```python\s*(.*?)```'
            matches = re.findall(python_pattern, llm_out, re.DOTALL)
            
            if matches:
                # Take the first Python block found
                fixed_code = matches[0]
            else:
                # If no Python block, look for any code block
                code_pattern = r'```\s*(.*?)```'
                matches = re.findall(code_pattern, llm_out, re.DOTALL)
                if matches:
                    fixed_code = matches[0]
                else:
                    # If no code blocks, return the full response as code
                    fixed_code = llm_out

            # Clean up the fixed code
            fixed_code = fixed_code.strip()
            
            # Create fix output - show only the final fixed code
            output_parts = []
            
            output_parts.append("[bold #9370db]=== FIXED CODE ===[/bold #9370db]")
            output_parts.append(fixed_code)
            
            output_text = "\n".join(output_parts)
            self.call_from_thread(self.query_one("#output", Static).update, output_text)

        except Exception as e:
            error_text = f"[red]Error:[/red]\n{e}\n\n{traceback.format_exc()}"
            self.call_from_thread(self.query_one("#output", Static).update, error_text)

if __name__ == "__main__":
    app = CodeFixApp()
    app.run()
