from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
console = Console()

def build_llm_payload(file_path, code, ast_result, runtime_data):
    return {
        "file": file_path,
        "ast_result": ast_result,
        "runtime_result": runtime_data
    }

def print_report(ast_result, runtime_result):
    console.print(Panel("[bold magenta]AST Analysis Results[/bold magenta]", title="AST"))
    console.print(ast_result)
    
    console.print(Panel("[bold cyan]Runtime Analysis Results[/bold cyan]", title="Runtime"))
    console.print(runtime_result)
    
    # Create a summary table
    table = Table(title="Analysis Summary")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    
    table.add_row("AST Analysis", "✓" if ast_result.get("ok", False) else "✗")
    table.add_row("Runtime Test", "✓" if runtime_result.get("ok", False) else "✗")
    
    console.print(table)
