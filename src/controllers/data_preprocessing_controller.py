# src/controllers/data_preprocessing_controller.py

from flask import request, jsonify
from src.service.data_preprocessing_service import (
    handle_missing_values,
    handle_outliers,
    handle_scaling,
    analyze_data
)
from src.repository.data_preprocessing_repository import (
    load_data,
    save_data,
    load_preprocessing_log,
    save_preprocessing_log
)
import json

def register_preprocessing_routes(app):
    @app.route('/preprocess-data', methods=['POST'])
    def preprocess_data():
        """
        Endpoint para pré-processar dados.
        ---
        tags:
          - Preprocessing
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                treatment_options:
                  type: object
                  description: Opções de tratamento por coluna
                  example:
                    urn:ngsi-ld:SPweather:001_PRECIPITACAO_TOTAL_HORARIO_mm:
                      missing_values: 'mean'
                      outliers: 'remove'
                    urn:ngsi-ld:SPweather:001_TEMPERATURA_DO_AR_BULBO_SECO_HORARIA_Celsius:
                      missing_values: 'median'
                      outliers: 'cap'
                      scaling: 'standard'
        responses:
          200:
            description: Dados pré-processados com sucesso
            schema:
              type: object
              properties:
                analysis:
                  type: object
                  description: Resultados da análise após o pré-processamento
          400:
            description: Dados de entrada inválidos
          500:
            description: Erro durante o pré-processamento
        """
        try:
            input_data = request.get_json()
            if not input_data or 'treatment_options' not in input_data:
                return jsonify({'error': 'Dados de entrada inválidos'}), 400

            treatment_options = input_data['treatment_options']

            # Caminhos dos arquivos (podem ser configurados no config.json)
            data_file_path = 'processed_data.csv'  # Atualizado para salvar em 'processed_data.csv'
            preprocessing_log_file = 'preprocessing.json'

            # Carrega os dados
            data = load_data(data_file_path)
            if data.empty:
                return jsonify({'error': 'Nenhum dado carregado. Verifique o arquivo de entrada.'}), 500

            # Carrega ou inicializa o log de pré-processamento
            preprocessing_log = load_preprocessing_log(preprocessing_log_file)

            # Garante que todas as colunas estejam presentes no log de pré-processamento
            for col in data.columns:
                if col not in preprocessing_log:
                    preprocessing_log[col] = {'missing_values': "", 'outliers': "", 'normalization': ""}

            # Inicializa o dicionário para armazenar scalers
            scaler_dict = {}

            # Aplica tratamentos por coluna
            for column, treatments in treatment_options.items():
                if column in data.columns:
                    # Garante que a coluna exista no log de pré-processamento
                    if column not in preprocessing_log:
                        preprocessing_log[column] = {'missing_values': "", 'outliers': "", 'normalization': ""}
                    # Trata valores ausentes
                    if 'missing_values' in treatments:
                        method = treatments['missing_values']
                        data = handle_missing_values(data, column, method, preprocessing_log)
                    # Trata outliers
                    if 'outliers' in treatments:
                        method = treatments['outliers']
                        data = handle_outliers(data, column, method, preprocessing_log)
                    # Aplica escalonamento
                    if 'scaling' in treatments:
                        method = treatments['scaling']
                        data = handle_scaling(data, column, method, scaler_dict, preprocessing_log)
                else:
                    print(f"Coluna '{column}' não encontrada nos dados.")

            # Salva o log de pré-processamento
            save_preprocessing_log(preprocessing_log, preprocessing_log_file)

            # Analisa os dados após o tratamento para gerar recomendações
            analysis = analyze_data(data, preprocessing_log)

            # Salva os dados tratados
            if not data.empty:
                save_data(data, data_file_path)
            else:
                return jsonify({'error': 'Nenhum dado restante após o tratamento.'}), 500

            # Prepara a resposta
            response = {
                'analysis': analysis
            }

            return jsonify(response), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
