import os
import sys
import subprocess
import time
import webbrowser
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    if not is_admin():
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return

    # Install requirements
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Start Flask app in a separate process
    flask_process = subprocess.Popen([sys.executable, "app.py"])
    
    # Wait for Flask to start
    time.sleep(3)
    
    # Open browser
    webbrowser.open('http://127.0.0.1:5000')
    
    try:
        # Keep the script running
        flask_process.wait()
    except KeyboardInterrupt:
        flask_process.terminate()
        print("\nServer stopped")

if __name__ == "__main__":
    main()
