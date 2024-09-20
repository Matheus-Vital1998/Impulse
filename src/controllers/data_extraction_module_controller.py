from flask import Flask, request, jsonify
from service.data_extraction_module_service import extract_data_service
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/extract-data', methods=['POST'])
def extract_data():
    """
    Endpoint para extração de dados do STH-Comet
    ---
    tags:
      - Data Extraction
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            date_from:
              type: string
              description: Data de início no formato ISO
            date_to:
              type: string
              description: Data de fim no formato ISO
            limit:
              type: integer
              description: Limite de registros por request
            entities:
              type: array
              description: Lista de entidades e atributos
              items:
                type: object
                properties:
                  entity_id:
                    type: string
                  attributes:
                    type: array
                    items:
                      type: string
    responses:
      200:
        description: Extração de dados bem-sucedida
      500:
        description: Erro ao processar a extração de dados
    """
    try:
        data = request.get_json()

        date_from = data.get('date_from')
        date_to = data.get('date_to')
        limit = data.get('limit')
        entities = data.get('entities')

        result = extract_data_service(date_from, date_to, limit, entities)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
