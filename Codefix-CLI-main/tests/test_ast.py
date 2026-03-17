from codefixcli.debugger.scan import scan

def test_syntax_error():
    res = scan("if True")
    assert res["ok"] is False

def test_clean_code():
    res = scan("x = 10\nprint(x)")
    assert res["ok"] is True
    assert len(res["issues"]) == 0
