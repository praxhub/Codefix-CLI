import subprocess
import sys
import tempfile
import os
import time

def run_in_sandbox(code: str, timeout: int = 5) -> dict:
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    # Windows-safe process group flag
    _extra = {}
    if sys.platform == "win32":
        _extra["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        _extra["preexec_fn"] = os.setsid

    try:
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            **_extra,
        )
        elapsed = time.perf_counter() - t0
        return {
            "ok": True,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "elapsed": round(elapsed, 4),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True, "elapsed": timeout}
    except Exception as e:
        return {"ok": False, "error": str(e), "elapsed": 0}
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
