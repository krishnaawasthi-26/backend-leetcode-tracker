import subprocess
import sys
import threading
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent


def run_fastapi():
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"],
        cwd=BACKEND_DIR,
    )


def run_sync_script():
    subprocess.run([sys.executable, "sync_submissions.py"], cwd=BACKEND_DIR)


if __name__ == "__main__":
    t1 = threading.Thread(target=run_fastapi)
    t2 = threading.Thread(target=run_sync_script)

    t1.start()
    t2.start()

    t1.join()
    t2.join()