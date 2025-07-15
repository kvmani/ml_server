from microstructure_server import create_app
from config import Config
from microstructure_server.services.startup import start_services

app = create_app()