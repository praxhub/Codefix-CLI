from codefixcli.debugger.llm import build_prompt

def test_fix_prompt():
    code = "print('hello')"
    ast_data = {"issues": []}
    run_data = {"stdout": "hello"}
    prompt = build_prompt(code, ast_data, run_data)
    assert "print('hello')" in prompt
    assert "LLM" in prompt or "CODEFIX" in prompt
