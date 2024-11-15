# src/repository/predict_and_anomaly_detection_repository.py

import os
import json
import xgboost as xgb
import re

def sanitize_filename(name):
    """
    Substitui caracteres inválidos por sublinhados para criar um nome de arquivo válido no Windows.
    """
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
