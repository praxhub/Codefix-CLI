import subprocess
import sys
import tempfile
import os
import signal

def run_in_sandbox(code: str, timeout: int = 5):
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    with open(path, "w") as f:
        f.write(code)

    try:
        # Use timeout command to ensure process termination
        proc = subprocess.run(
            [sys.executable, path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            preexec_fn=os.setsid  # Create new process group
        )
        return {
            "ok": True,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            os.remove(path)
        except:
            pass  # File might not exist
