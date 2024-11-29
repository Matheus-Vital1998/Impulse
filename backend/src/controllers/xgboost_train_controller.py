# src/controllers/xgboost_train_controller.py

from flask import request, jsonify
from src.service.xgboost_train_service import train_xgboost_model

def register_xgboost_train_routes(app):
    @app.route('/train-xgboost-model', methods=['POST'])
    def train_xgboost_model_endpoint():
        """
        Endpoint para treinar um modelo XGBoost com recursos avançados.
        ---
        tags:
          - Model Training
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
                allowed_deviation:
                  type: number
                  description: Desvio permitido para detecção de anomalias.
                threshold_max:
                  type: number
                  description: Valor máximo permitido para a variável alvo.
                threshold_min:
                  type: number
                  description: Valor mínimo permitido para a variável alvo.
                feature_flags:
                  type: object
                  description: Flags para incluir ou excluir recursos.
                  properties:
                    hour:
                      type: boolean
                    minute:
                      type: boolean
                    second:
                      type: boolean
                    millisecond:
                      type: boolean
                    day_of_year:
                      type: boolean
                    week_of_year:
                      type: boolean
                    month:
                      type: boolean
                    year:
                      type: boolean
                    day_of_week:
                      type: boolean
                    quarter:
                      type: boolean
                    is_weekend:
                      type: boolean
                    trend:
                      type: boolean
                    seasonality:
                      type: boolean
                    denoise:
                      type: boolean
                    cycles:
                      type: boolean
                xgboost_hyperparameters:
                  type: object
                  description: Hiperparâmetros para o modelo XGBoost.
                  properties:
                    n_estimators:
                      type: integer
                    learning_rate:
                      type: number
                    max_depth:
                      type: integer
                    subsample:
                      type: number
                    colsample_bytree:
                      type: number
                    gamma:
                      type: number
                    reg_alpha:
                      type: number
                    reg_lambda:
                      type: number
                    min_child_weight:
                      type: number
        responses:
          200:
            description: Modelo treinado com sucesso.
            schema:
              type: object
          400:
            description: Requisição inválida.
          500:
            description: Erro interno do servidor.
        """
        try:
            params = request.get_json()
            if 'target_name' not in params or not params['target_name']:
                return jsonify({'error': 'O parâmetro "target_name" é obrigatório e não pode ser vazio.'}), 400

            metrics = train_xgboost_model(params)
            return jsonify(metrics), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
