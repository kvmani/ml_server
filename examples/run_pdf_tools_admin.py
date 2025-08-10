"""Example app showing plugin polling for pdf_tools."""

from ml_server.app.server import create_app
from ml_server.plugins import PluginRegistry

app = create_app(startup=False)
registry = PluginRegistry(app)
registry.register_remote("pdf_tools", "http://localhost:8000/pdf_tools")
app.extensions["plugin_registry"] = registry

if __name__ == "__main__":
    app.run(port=5000)
