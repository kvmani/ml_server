from flask import Blueprint

# Create the blueprint
super_resolution_bp = Blueprint(
    'super_resolution',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

# Import routes after blueprint creation to avoid circular imports
from . import routes 