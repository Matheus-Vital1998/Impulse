# src/repository/predict_and_anomaly_detection_repository.py

<<<<<<< HEAD
import os
import json
import xgboost as xgb
import re

def sanitize_filename(name):
    """
    Substitui caracteres inválidos por sublinhados para criar um nome de arquivo válido no Windows.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', name)
=======
import pandas as pd
import os
import json
import xgboost as xgb
>>>>>>> nova-feature-docker

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
<<<<<<< HEAD
        raise FileNotFoundError("O arquivo 'trained_models.json' não existe.")
=======
        raise FileNotFoundError("trained_models.json não existe.")

def update_model_info(target_name, params):
    """Atualiza os parâmetros do modelo com quaisquer novas configurações fornecidas."""
    model_info = load_model_info(target_name)
    updated = False

    for param in ['allowed_deviation', 'threshold_max', 'threshold_min']:
        if param in params:
            model_info[param] = params[param]
            updated = True

    if updated:
        trained_models_path = os.path.join('trained_models', 'trained_models.json')
        with open(trained_models_path, 'r') as f:
            models = json.load(f)
        models[target_name] = model_info
        with open(trained_models_path, 'w') as f:
            json.dump(models, f, indent=4)

    return model_info
>>>>>>> nova-feature-docker

def load_trained_model(model_filename):
    """Carrega o modelo XGBoost treinado a partir do arquivo."""
    model_path = os.path.join('trained_models', model_filename)
    if os.path.exists(model_path):
        model = xgb.XGBRegressor()
        model.load_model(model_path)
        return model
    else:
        raise FileNotFoundError(f"O arquivo de modelo '{model_filename}' não foi encontrado.")
<<<<<<< HEAD
=======

def load_processed_data(target_name):
    """Carrega os dados processados do arquivo 'processed_data.csv'."""
    file_path = 'processed_data.csv'
    data = pd.read_csv(file_path, delimiter=',')
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce', utc=True)

    if target_name not in data.columns:
        raise ValueError(f"Alvo '{target_name}' não encontrado nos dados.")

    data = data[['timestamp', target_name]]
    return data
>>>>>>> nova-feature-docker
