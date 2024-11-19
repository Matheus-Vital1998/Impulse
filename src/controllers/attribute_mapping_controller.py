from flask import jsonify, request
from src.service.attribute_mapping_service import get_formatted_entities

def register_attribute_mapping_routes(app):
    @app.route('/attribute-mapping', methods=['GET'])
    def attribute_mapping():
        """
        Endpoint para obter o mapeamento de atributos das entidades do Orion Context Broker.
        ---
        tags:
          - Attribute Mapping
        parameters:
          - in: query
            name: limit
            type: integer
            description: Número máximo de entidades a serem retornadas.
        responses:
          200:
            description: Mapeamento obtido com sucesso
            schema:
              type: object
              properties:
                entities:
                  type: array
                  items:
                    type: object
                    properties:
                      entity_id:
                        type: string
                      entity_type:
                        type: string
                      attributes:
                        type: array
                        items:
                          type: string
          500:
            description: Erro ao obter o mapeamento
        """
        try:
            limit = request.args.get('limit', default=100, type=int)
            formatted_data = get_formatted_entities(limit=limit)
            return jsonify(formatted_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
