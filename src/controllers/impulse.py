from flask import Blueprint, jsonify
from flasgger import swag_from

# Cria um Blueprint para o módulo impulse
impulse_bp = Blueprint('impulse_bp', __name__)

@impulse_bp.route('/status', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Retorna o status da API',
            'examples': {
                'application/json': {
                    "status": "API está funcionando!"
                }
            }
        }
    }
})
def status():
    """
    Verifica o status da API
    ---
    responses:
      200:
        description: Retorna o status da API
    """
    return jsonify({"status": "API está funcionando!"})
