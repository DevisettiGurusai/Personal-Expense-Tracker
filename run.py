import subprocess
import time
import sys
import os

def run_app():
    print("🚀 Starting Personal Expense Tracker (Web App)...")
    
    # 1. Start Backend
    print("📡 Launching Backend (FastAPI) on http://localhost:8000...")
    backend_dir = os.path.join(os.getcwd(), "backend")
    # Launch server.py from within the backend folder so it finds .env and expenses.db
    backend_proc = subprocess.Popen([sys.executable, "server.py"], cwd=backend_dir)
    
    # 2. Start Frontend
    print("🎨 Launching Frontend (React/Vite) on http://localhost:5173...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("⚠️ node_modules not found in frontend directory. Please run 'npm install' inside the 'frontend' folder first.")
    
    frontend_proc = subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, shell=True)
    
    try:
        print("\n✅ Both servers are running!")
        print("👉 Access the app at: http://localhost:5173")
        print("\nPress Ctrl+C to stop both servers.")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("👋 Goodbye!")

if __name__ == "__main__":
    run_app()
