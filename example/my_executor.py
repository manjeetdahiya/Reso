from src.executor.server import Server
from example.my_workflow import my_workflow

# just have executor and server in it
server = Server({'my_workflow': my_workflow})

app = server.app
