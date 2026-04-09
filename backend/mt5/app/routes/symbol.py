import re

from flask import Blueprint, jsonify, request
import MetaTrader5 as mt5
from flasgger import swag_from
import logging

symbol_bp = Blueprint('symbol', __name__)
logger = logging.getLogger(__name__)

FOREX_CURRENCIES = {
    'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
    'SEK', 'NOK', 'DKK', 'SGD', 'HKD', 'ZAR', 'TRY', 'PLN',
    'CZK', 'HUF', 'MXN', 'CNH'
}
FOREX_PATH_KEYWORDS = ('forex', 'fx', 'majors', 'minors', 'exotics')


def is_forex_symbol(symbol_name: str, path: str = '', description: str = '') -> bool:
    searchable_parts = ' '.join([symbol_name or '', path or '', description or '']).lower()
    if any(keyword in searchable_parts for keyword in FOREX_PATH_KEYWORDS):
        return True

    normalized_name = re.sub(r'[^A-Z]', '', (symbol_name or '').upper())
    for idx in range(max(0, len(normalized_name) - 5)):
        candidate = normalized_name[idx:idx + 6]
        if len(candidate) == 6 and candidate[:3] in FOREX_CURRENCIES and candidate[3:] in FOREX_CURRENCIES:
            return True

    return False

@symbol_bp.route('/symbol_info_tick/<symbol>', methods=['GET'])
@swag_from({
    'tags': ['Symbol'],
    'parameters': [
        {
            'name': 'symbol',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Symbol name to retrieve tick information.'
        }
    ],
    'responses': {
        200: {
            'description': 'Tick information retrieved successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'bid': {'type': 'number'},
                    'ask': {'type': 'number'},
                    'last': {'type': 'number'},
                    'volume': {'type': 'integer'},
                    'time': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Failed to get symbol tick info.'
        }
    }
})
def get_symbol_info_tick_endpoint(symbol):
    """
    Get Symbol Tick Information
    ---
    description: Retrieve the latest tick information for a given symbol.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return jsonify({"error": "Failed to get symbol tick info"}), 404
    
    tick_dict = tick._asdict()
    return jsonify(tick_dict)

@symbol_bp.route('/symbol_info/<symbol>', methods=['GET'])
@swag_from({
    'tags': ['Symbol'],
    'parameters': [
        {
            'name': 'symbol',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Symbol name to retrieve information.'
        }
    ],
    'responses': {
        200: {
            'description': 'Symbol information retrieved successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'path': {'type': 'string'},
                    'description': {'type': 'string'},
                    'volume_min': {'type': 'number'},
                    'volume_max': {'type': 'number'},
                    'volume_step': {'type': 'number'},
                    'price_digits': {'type': 'integer'},
                    'spread': {'type': 'number'},
                    'points': {'type': 'integer'},
                    'trade_mode': {'type': 'integer'},
                    # Add other relevant fields as needed
                }
            }
        },
        404: {
            'description': 'Failed to get symbol info.'
        }
    }
})
def get_symbol_info(symbol):
    """
    Get Symbol Information
    ---
    description: Retrieve detailed information for a given symbol.
    """
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return jsonify({"error": "Failed to get symbol info"}), 404
    
    symbol_info_dict = symbol_info._asdict()
    return jsonify(symbol_info_dict)


@symbol_bp.route('/symbols/forex', methods=['GET'])
@swag_from({
    'tags': ['Symbol'],
    'parameters': [
        {
            'name': 'visible_only',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'When true, only return symbols currently visible in Market Watch.'
        },
        {
            'name': 'search',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Optional case-insensitive text filter for symbol name or description.'
        }
    ],
    'responses': {
        200: {
            'description': 'Forex symbols retrieved successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer'},
                    'symbols': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'description': {'type': 'string'},
                                'path': {'type': 'string'},
                                'visible': {'type': 'boolean'},
                                'trade_mode': {'type': 'integer'},
                                'digits': {'type': 'integer'}
                            }
                        }
                    }
                }
            }
        },
        500: {
            'description': 'Internal server error.'
        }
    }
})
def list_forex_symbols():
    """
    List Forex Symbols
    ---
    description: Retrieve all available forex-like symbols from the connected MT5 terminal.
    """
    try:
        visible_only = request.args.get('visible_only', 'false').lower() in ('1', 'true', 'yes')
        search = request.args.get('search', '').strip().lower()

        symbols = mt5.symbols_get()
        if symbols is None:
            return jsonify({"error": "Failed to load symbols from MT5"}), 500

        forex_symbols = []
        for symbol in symbols:
            symbol_dict = symbol._asdict()
            if not is_forex_symbol(
                symbol_dict.get('name', ''),
                symbol_dict.get('path', ''),
                symbol_dict.get('description', '')
            ):
                continue

            if visible_only and not symbol_dict.get('visible', False):
                continue

            if search:
                haystack = ' '.join([
                    symbol_dict.get('name', ''),
                    symbol_dict.get('description', ''),
                    symbol_dict.get('path', '')
                ]).lower()
                if search not in haystack:
                    continue

            forex_symbols.append({
                'name': symbol_dict.get('name'),
                'description': symbol_dict.get('description'),
                'path': symbol_dict.get('path'),
                'visible': symbol_dict.get('visible'),
                'trade_mode': symbol_dict.get('trade_mode'),
                'digits': symbol_dict.get('digits')
            })

        forex_symbols.sort(key=lambda item: item['name'] or '')
        return jsonify({
            'count': len(forex_symbols),
            'symbols': forex_symbols
        })

    except Exception as e:
        logger.error(f"Error in list_forex_symbols: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
