import os

from flask import Blueprint, jsonify
import MetaTrader5 as mt5
from flasgger import swag_from

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
@swag_from({
    'tags': ['Health'],
    'responses': {
        200: {
            'description': 'Health check successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'mt5_connected': {'type': 'boolean'},
                    'mt5_initialized': {'type': 'boolean'}
                }
            }
        }
    }
})
def health_check():
    """
    Health Check Endpoint
    ---
    description: Check the health status of the application and MT5 connection.
    responses:
      200:
        description: Health check successful
    """
    terminal_installed = os.path.exists(r"C:\Program Files\MetaTrader 5\terminal64.exe")
    return jsonify({
        "status": "healthy",
        "mt5_connected": mt5 is not None,
        "mt5_initialized": terminal_installed,
        "mt5_terminal_installed": terminal_installed
    }), 200
