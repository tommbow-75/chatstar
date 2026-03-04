import uvicorn
from PyQt6.QtCore import QThread, pyqtSignal
from backend.main import app as fastapi_app

class BackendThread(QThread):
    finished_signal = pyqtSignal()
    started_signal = pyqtSignal()
    
    def __init__(self, host="127.0.0.1", port=8000):
        super().__init__()
        self.host = host
        self.port = port
        # uvicorn.Config and Server allow us to run it inside a thread
        self.config = uvicorn.Config(fastapi_app, host=self.host, port=self.port, log_level="info")
        self.server = uvicorn.Server(self.config)

    def run(self):
        self.started_signal.emit()
        self.server.run()
        self.finished_signal.emit()

    def stop(self):
        self.server.should_exit = True
        self.wait()
