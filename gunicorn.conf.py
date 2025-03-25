import multiprocessing

# Gunicorn configuration for Flask-SocketIO
bind = '0.0.0.0:5000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'eventlet'
keepalive = 120
reload = True
preload_app = True
websocket_ping_interval = 30
websocket_ping_timeout = 120
websocket_max_message_size = 1024 * 1024 * 10  # 10MB
websocket_per_message_deflate = True
websocket_compression_level = 6

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'