# src/controllers/predict_and_anomaly_detection_controller.py

from flask import request, jsonify
from src.service.predict_and_anomaly_detection_service import perform_prediction

def register_prediction_routes(app):
    @app.route('/predict-and-anomaly-detection', methods=['POST'])
    def predict_and_anomaly_detection():
        """
        Endpoint para realizar predição e detecção de anomalias.
        ---
        tags:
          - Prediction & Anomaly Detection
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                target_name:
                  type: string
                  description: Nome da variável alvo a ser predita.
                forecast_horizon:
                  type: integer
                  description: Número de horas à frente para prever.
                allowed_deviation:
                  type: number
                  description: Desvio permitido para detecção de anomalias.
                threshold_max:
                  type: number
                  description: Valor máximo permitido para a variável alvo.
                threshold_min:
                  type: number
                  description: Valor mínimo permitido para a variável alvo.
                date_from:
                  type: string
                  format: date-time
                  description: Data inicial para os dados históricos (ISO 8601).
                date_to:
                  type: string
                  format: date-time
                  description: Data final para os dados históricos (ISO 8601).
          - in: header
            name: Content-Type
            required: true
            type: string
            default: application/json
        responses:
          200:
            description: Predição e detecção de anomalias realizadas com sucesso.
            schema:
              type: object
              properties:
                message:
                  type: string
                data:
                  type: array
                  items:
                    type: object
                    properties:
                      timestamp:
                        type: string
                        format: date-time
                      actual_data:
                        type: number
                      predicted_data:
                        type: number
                      anomaly_alert:
                        type: boolean
          400:
            description: Requisição inválida.
          500:
            description: Erro interno do servidor.
        """
        try:
            params = request.get_json()
            if 'target_name' not in params or not params['target_name']:
                return jsonify({'error': 'O parâmetro "target_name" é obrigatório e não pode ser vazio.'}), 400

            result = perform_prediction(params)
            return jsonify(result), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
