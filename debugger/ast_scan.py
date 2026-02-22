import ast
import sys

# ── Cyclomatic complexity counter ──────────────────────────────────────────────
_BRANCH_NODES = (
    ast.If, ast.For, ast.While, ast.ExceptHandler,
    ast.With, ast.Assert, ast.comprehension,
    ast.BoolOp,  # counts and/or chains
)

def _cyclomatic(func_node: ast.FunctionDef) -> int:
    """Estimate cyclomatic complexity (1 + branches) for a function."""
    count = 1
    for node in ast.walk(func_node):
        if isinstance(node, _BRANCH_NODES):
            if isinstance(node, ast.BoolOp):
                count += len(node.values) - 1
            else:
                count += 1
    return count

# ── Main scanner ───────────────────────────────────────────────────────────────
def scan(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"ok": False, "syntax_error": {"msg": e.msg, "lineno": e.lineno}, "issues": [], "complexity": {}}

    issues = []
    complexity = {}

    # ── 1. Unreachable code after return ──────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            returned = False
            for n in node.body:
                if isinstance(n, ast.Return):
                    returned = True
                elif returned:
                    issues.append({
                        "kind": "unreachable",
                        "message": f"Unreachable code after return in '{node.name}'",
                        "lineno": getattr(n, "lineno", None),
                    })
                    break

    # ── 2. Unused imports ─────────────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                if not _is_used_in_tree(name, tree):
                    issues.append({
                        "kind": "unused_import",
                        "message": f"Unused import: '{name}'",
                        "lineno": node.lineno,
                    })
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    name = alias.asname or alias.name
                    if not _is_used_in_tree(name, tree):
                        issues.append({
                            "kind": "unused_import",
                            "message": f"Unused import: '{name}'",
                            "lineno": node.lineno,
                        })

    # ── 3. Bare except clauses ────────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({
                "kind": "bare_except",
                "message": "Bare 'except:' catches all exceptions — use 'except Exception' or a specific type",
                "lineno": getattr(node, "lineno", None),
            })

    # ── 4. eval() / exec() usage ──────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in ("eval", "exec"):
                issues.append({
                    "kind": "dangerous_call",
                    "message": f"Use of '{name}()' is a security risk — avoid executing arbitrary strings",
                    "lineno": getattr(node, "lineno", None),
                })

    # ── 5. Mutable default arguments ─────────────────────────────────────────
    _MUTABLE = (ast.List, ast.Dict, ast.Set)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default is not None and isinstance(default, _MUTABLE):
                    issues.append({
                        "kind": "mutable_default",
                        "message": f"Mutable default argument in '{node.name}' — use None and assign inside the function",
                        "lineno": getattr(node, "lineno", None),
                    })

    # ── 6. Cyclomatic complexity ──────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cc = _cyclomatic(node)
            complexity[node.name] = cc
            if cc >= 10:
                issues.append({
                    "kind": "high_complexity",
                    "message": f"'{node.name}' has high cyclomatic complexity ({cc}) — consider refactoring",
                    "lineno": getattr(node, "lineno", None),
                })

    # ── 7. Undefined variables (best-effort) ──────────────────────────────────
    try:
        class UndefinedVarVisitor(ast.NodeVisitor):
            def __init__(self):
                self.defined_vars = set()
                self.current_scope = set()

            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.defined_vars.add(target.id)
                        self.current_scope.add(target.id)
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load) and node.id not in self.defined_vars:
                    issues.append({
                        "kind": "undefined_var",
                        "message": f"Possibly undefined variable: '{node.id}'",
                        "lineno": node.lineno,
                    })
                self.generic_visit(node)

        visitor = UndefinedVarVisitor()
        visitor.visit(tree)
    except Exception:
        pass

    return {"ok": True, "issues": issues, "complexity": complexity}


def _is_used_in_tree(name, tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load):
            return True
    return False
