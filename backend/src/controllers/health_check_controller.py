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
        summary: Verifica o status do backend
        description: >
            Este endpoint verifica se o backend está funcionando corretamente
            e também retorna a versão do Orion Context Broker se o serviço estiver acessível.
        responses:
          200:
            description: Serviço está saudável
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Estado do serviço
                  example: "healthy"
                orion_version:
                  type: string
                  description: Versão do Orion Context Broker
                  example: "v2.6.0"
          500:
            description: Erro ao verificar a saúde
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Estado do serviço
                  example: "unhealthy"
                error:
                  type: string
                  description: Descrição do erro ocorrido
                  example: "Connection to Orion failed"
        """
        try:
            # Chama o serviço para verificar a versão do Orion Context Broker
            orion_version = check_orion_version()
            return jsonify({"status": "healthy", "orion_version": orion_version}), 200
        except Exception as e:
            # Captura exceções e retorna o erro em formato JSON
            return jsonify({"status": "unhealthy", "error": str(e)}), 500
