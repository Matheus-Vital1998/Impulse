# src/controllers/data_extraction_controller.py

from flask import request, jsonify
from src.service.data_extraction_service import extract_data

def register_extraction_routes(app):
    @app.route('/extract-data', methods=['POST'])
    def extract_data_endpoint():
        """
        Endpoint para extrair dados da API STH-Comet.
        ---
        tags:
          - Data Extraction
        parameters:
          - in: body
            name: body
            required: true
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
                        description: ID da entidade
                      entity_type:
                        type: string
                        description: Tipo da entidade
                      attributes:
                        type: array
                        items:
                          type: string
                        description: Lista de atributos
        responses:
          200:
            description: Dados extraídos com sucesso
            schema:
              type: object
              properties:
                data:
                  type: array
                  items:
                    type: object
          400:
            description: Requisição inválida
          500:
            description: Erro ao extrair dados
        """
        try:
            input_data = request.get_json()
            if not input_data or 'entities' not in input_data:
                return jsonify({'error': 'Dados de entrada inválidos'}), 400

            date_from = request.args.get(
                'date_from', '2016-01-01T00:00:00.000Z'
            )
            date_to = request.args.get(
                'date_to', '2025-01-31T23:59:59.999Z'
            )

            data = extract_data(input_data, date_from, date_to)

            return jsonify({'data': data}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
