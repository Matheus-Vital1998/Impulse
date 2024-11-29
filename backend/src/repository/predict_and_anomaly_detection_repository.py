# src/repository/predict_and_anomaly_detection_repository.py

import os
import json
import xgboost as xgb
import re
import pandas as pd

def sanitize_filename(name):
    """Substitui caracteres inválidos por sublinhados para criar um nome de arquivo válido."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def load_model_info(target_name):
    """Carrega as informações do modelo a partir de 'trained_models.json'."""
    trained_models_path = os.path.join('trained_models', 'trained_models.json')
    if os.path.exists(trained_models_path):
        with open(trained_models_path, 'r') as f:
            models = json.load(f)
        if target_name in models:
            return models[target_name]
        else:
            raise ValueError(f"Modelo para o alvo '{target_name}' não encontrado.")
    else:
        raise FileNotFoundError("O arquivo 'trained_models.json' não existe.")

def load_trained_model(model_filename):
    """Carrega o modelo XGBoost treinado a partir do arquivo."""
    model_path = os.path.join('trained_models', model_filename)
    if os.path.exists(model_path):
        model = xgb.XGBRegressor()
        model.load_model(model_path)
        return model
    else:
        raise FileNotFoundError(f"O arquivo de modelo '{model_filename}' não foi encontrado.")

def load_processed_data(target_name, file_path='processed_data.csv', date_from=None, date_to=None):
    """Carrega os dados históricos do 'processed_data.csv' dentro de um intervalo de datas."""
    if os.path.exists(file_path):
        data = pd.read_csv(file_path, delimiter=',')
        data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce', utc=True)
        if target_name not in data.columns:
            raise ValueError(f"Alvo '{target_name}' não encontrado nos dados.")
        data = data[['timestamp', target_name]]

        # Filtrar por intervalo de datas se especificado
        if date_from:
            date_from = pd.to_datetime(date_from, utc=True)
            data = data[data['timestamp'] >= date_from]
        if date_to:
            date_to = pd.to_datetime(date_to, utc=True)
            data = data[data['timestamp'] <= date_to]

        return data
    else:
        raise FileNotFoundError(f"O arquivo '{file_path}' não foi encontrado.")
