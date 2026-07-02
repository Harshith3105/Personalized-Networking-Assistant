import sys
import subprocess
import time
import signal

def run_services():
    python_exe = sys.executable
    print(f"Using Python executable: {python_exe}")
    
    # 1. Start FastAPI Backend via Uvicorn
    backend_cmd = [
        python_exe, "-m", "uvicorn", "backend.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ]
    print(f"Launching FastAPI backend: {' '.join(backend_cmd)}")
    backend_proc = subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Wait a bit for backend to start up
    time.sleep(2)
    
    # 2. Start Streamlit Frontend
    frontend_cmd = [
        python_exe, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "127.0.0.1"
    ]
    print(f"Launching Streamlit frontend: {' '.join(frontend_cmd)}")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Setup non-blocking log reading or simple print loop
    import threading
    
    def log_reader(pipe, prefix):
        for line in iter(pipe.readline, ''):
            print(f"[{prefix}] {line.strip()}")
            
    backend_thread = threading.Thread(target=log_reader, args=(backend_proc.stdout, "BACKEND"), daemon=True)
    frontend_thread = threading.Thread(target=log_reader, args=(frontend_proc.stdout, "FRONTEND"), daemon=True)
    
    backend_thread.start()
    frontend_thread.start()
    
    print("\n" + "="*50)
    print("Personalized Networking Assistant is running!")
    print("Backend API: http://127.0.0.1:8000/docs (Swagger UI)")
    print("Streamlit UI: http://127.0.0.1:8501")
    print("Press Ctrl+C to stop all services.")
    print("="*50 + "\n")
    
    try:
        while True:
            # Check if either process terminated
            if backend_proc.poll() is not None:
                print("Backend process terminated unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("Frontend process terminated unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        # Clean up processes
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
            frontend_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
            frontend_proc.kill()
        print("Services stopped.")

if __name__ == "__main__":
    run_services()
