from microstructure_server import create_app
from config import Config
from microstructure_server.services.startup import start_services

app = create_app()

if __name__ == '__main__':
    start_services()
    config = Config()
    app.run(
        host=config.config['host'],
        port=config.config['port'],
        debug=config.debug,
        use_reloader=True,
    )
