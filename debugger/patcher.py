import re

def extract_unified_diff(text: str) -> str:
    # Try ```diff fenced
    m = re.search(r"```diff(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Try ``` fenced
    m = re.search(r"```(?:diff)?(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Fallback scan
    start = None
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("diff --") or ln.startswith("--- ") or ln.startswith("@@"):
            start = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:]).strip()

def apply_patch(original: str, diff_text: str) -> str:
    if not diff_text.strip():
        return original
    
    # For now, return original (safe mode)
    # In a more advanced version, we could implement actual patching
    return original
