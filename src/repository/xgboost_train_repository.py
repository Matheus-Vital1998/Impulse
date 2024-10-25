# src/repository/xgboost_train_repository.py

import pandas as pd
import os
import json

def load_data(file_path, target_name):
    """Carrega o conjunto de dados e extrai a variável alvo."""
    data = pd.read_csv(file_path, delimiter=',')
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce', utc=True)
    if target_name not in data.columns:
        raise ValueError(f"Target '{target_name}' não encontrado nos dados.")
    return data

def save_trained_model(model, target_name):
    """Salva o modelo treinado na pasta 'trained_models'."""
    os.makedirs('trained_models', exist_ok=True)
    model_filename = os.path.join('trained_models', f"{target_name}_xgboost_model.json")
    model.save_model(model_filename)
    return model_filename

def save_model_info(params, model_filename, metrics):
    """Salva as informações do modelo e métricas em 'trained_models.json'."""
    model_info = {
        "target_name": params["target_name"],
        "model_filename": os.path.basename(model_filename),
        "allowed_deviation": params.get("allowed_deviation"),
        "threshold_max": params.get("threshold_max"),
        "threshold_min": params.get("threshold_min"),
        "feature_flags": params.get("feature_flags"),
        "xgboost_hyperparameters": params.get("xgboost_hyperparameters"),
        "training_metrics": metrics
    }

    os.makedirs('trained_models', exist_ok=True)
    trained_models_path = os.path.join('trained_models', 'trained_models.json')

    if os.path.exists(trained_models_path):
        with open(trained_models_path, 'r') as f:
            models = json.load(f)
    else:
        models = {}

    models[params["target_name"]] = model_info

    with open(trained_models_path, 'w') as f:
        json.dump(models, f, indent=4)
