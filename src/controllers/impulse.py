from flask import Blueprint, jsonify, request
from src.service.data_service import DataService
from flasgger import swag_from

# Cria um Blueprint para o módulo impulse
impulse_bp = Blueprint('impulse_bp', __name__)

# Instancia o DataService com a URL do Fiware
fiware_url = "http://fiware-orion-url:1026"  # Substitua pela URL correta
data_service = DataService(fiware_url)

@impulse_bp.route('/weather/<entity_id>', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Retorna os dados meteorológicos de uma estação',
            'examples': {
                'application/json': {
                    "temperature": "20.5",
                    "humidity": "60%"
                }
            }
        },
        404: {
            'description': 'Estação meteorológica não encontrada'
        }
    }
})
def get_weather(entity_id):
    """
    Obtém os dados de uma estação meteorológica
    ---
    parameters:
      - name: entity_id
        in: path
        type: string
        required: true
        description: ID da estação meteorológica
    responses:
      200:
        description: Retorna os dados meteorológicos de uma estação
      404:
        description: Estação meteorológica não encontrada
    """
    data = data_service.get_weather_data_service(entity_id)
    return jsonify(data), 200 if 'error' not in data else 404

@impulse_bp.route('/extract_data', methods=['POST'])
@swag_from({
    'responses': {
        200: {
            'description': 'Dados extraídos com sucesso',
            'examples': {
                'application/json': {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "temperature": "20.5",
                    "humidity": "60%"
                }
            }
        },
        500: {
            'description': 'Erro interno do servidor'
        }
    }
})

def extract_data():
    """
    Extrai dados de múltiplas entidades e atributos
    ---
    parameters:
      - name: body
        in: body
        schema:
          id: ExtractData
          required:
            - date_from
            - date_to
            - limit
            - entities
          properties:
            date_from:
              type: string
              format: date-time
              description: Data de início para a extração
            date_to:
              type: string
              format: date-time
              description: Data de fim para a extração
            limit:
              type: integer
              description: Limite de resultados por página
            entities:
              type: array
              items:
                type: object
                properties:
                  entity_id:
                    type: string
                    description: ID da entidade
                  entity_type:
                    type: string
                    description: Tipo da entidade
                  attributes:
                    type: array
                    items:
                      type: string
                    description: Atributos a serem extraídos
    responses:
      200:
        description: Dados extraídos com sucesso
      500:
        description: Erro interno do servidor
    """
    try:
        data = request.json
        date_from = data['date_from']
        date_to = data['date_to']
        limit = data['limit']
        entities = data['entities']

        result = data_service.extract_data_service(date_from, date_to, limit, entities)
        return jsonify(result), 200 if 'message' not in result else 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
