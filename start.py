import webbrowser
import threading
import time
from app import app, socketio

browser_opened = False

def open_browser():
    global browser_opened
    if not browser_opened:
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:5000')
        browser_opened = True

if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)
