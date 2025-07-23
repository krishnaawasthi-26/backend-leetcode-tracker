import subprocess
import threading

def run_fastapi():
    subprocess.run(["uvicorn", "api.main:app", "--reload", "--port", "8002"])

def run_sync_script():
    subprocess.run(["python", "sync_submissions.py"])

if __name__ == "__main__":
    t1 = threading.Thread(target=run_fastapi)
    t2 = threading.Thread(target=run_sync_script)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
