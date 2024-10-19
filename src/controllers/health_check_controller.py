from flask import jsonify
from src.service.health_check_service import check_orion_version

def register_health_routes(app):
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Endpoint para verificar a saúde do backend solicitando a versão do Orion Context Broker
        ---
        tags:
          - Health Check
        responses:
          200:
            description: Serviço está saudável
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Estado do serviço
                orion_version:
                  type: string
                  description: Versão do Orion Context Broker
          500:
            description: Erro ao verificar a saúde
        """
        try:
            orion_version = check_orion_version()
            return jsonify({"status": "healthy", "orion_version": orion_version}), 200
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 500
