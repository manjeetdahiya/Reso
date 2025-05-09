from src.executor.server import Server
from example.my_workflow import my_workflow

server = Server({'test_workflow': my_workflow})

app = server.app
