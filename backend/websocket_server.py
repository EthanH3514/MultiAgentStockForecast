from flask_socketio import SocketIO, emit
from flask import Flask

class WebSocketServer:
    def __init__(self, app: Flask):
        self.socketio = SocketIO(app, cors_allowed_origins="*")
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected')
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected')
    
    def emit_analysis_progress(self, agent_type: str, message: str, reasoning: str = None):
        """发送分析进度到前端"""
        data = {
            'agent_type': agent_type,
            'message': message
        }
        if reasoning:
            data['reasoning'] = reasoning
        self.socketio.emit('analysis_progress', data)
    
    def run(self, app: Flask, **kwargs):
        self.socketio.run(app, **kwargs)