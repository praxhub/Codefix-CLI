import ast
import sys

def scan(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"ok": False, "syntax_error": {"msg": e.msg, "lineno": e.lineno}, "issues": []}

    issues = []

    # Detect unreachable code
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            returned = False
            for n in node.body:
                if isinstance(n, ast.Return):
                    returned = True
                elif returned:
                    issues.append({
                        "kind": "unreachable",
                        "message": f"Unreachable code after return in {node.name}",
                        "lineno": getattr(n, "lineno", None),
                    })
                    break

    # Detect unused imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                if not _is_used_in_tree(name, tree):
                    issues.append({
                        "kind": "unused_import",
                        "message": f"Unused import: {name}",
                        "lineno": node.lineno,
                    })
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":  # Skip wildcard imports
                    name = alias.asname or alias.name
                    if not _is_used_in_tree(name, tree):
                        issues.append({
                            "kind": "unused_import",
                            "message": f"Unused import: {name}",
                            "lineno": node.lineno,
                        })

    # Detect undefined variables
    try:
        # Use ast NodeVisitor to find undefined variables
        class UndefinedVarVisitor(ast.NodeVisitor):
            def __init__(self):
                self.defined_vars = set()
                self.undefined_vars = []
                self.current_scope = set()
            
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.defined_vars.add(target.id)
                        self.current_scope.add(target.id)
                self.generic_visit(node)
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load) and node.id not in self.defined_vars:
                    self.undefined_vars.append({
                        "kind": "undefined_var",
                        "message": f"Undefined variable: {node.id}",
                        "lineno": node.lineno,
                    })
                self.generic_visit(node)
        
        visitor = UndefinedVarVisitor()
        visitor.visit(tree)
        issues.extend(visitor.undefined_vars)
    except:
        pass  # If analysis fails, continue without undefined var detection

    return {"ok": True, "issues": issues}

def _is_used_in_tree(name, tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load):
            return True
    return False
