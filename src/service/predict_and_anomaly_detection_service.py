# src/service/predict_and_anomaly_detection_service.py

import pandas as pd
import numpy as np
from src.repository.predict_and_anomaly_detection_repository import (
    load_model_info,
    load_trained_model
)

def feature_engineering(data, feature_flags):
    """Gera recursos baseados no tempo para os dados de entrada."""
    # Definir períodos de tempo para recursos cíclicos
    time_periods = {
        'hour': 24,
        'minute': 60,
        'second': 60,
        'millisecond': 1000,
        'day_of_year': 365,
        'week_of_year': 52,
        'month': 12,
        'day_of_week': 7,
        'quarter': 4,
    }

    # Gerar recursos com base em feature_flags
    for feature in ['hour', 'minute', 'second', 'millisecond', 'day_of_year',
                    'week_of_year', 'month', 'year', 'day_of_week', 'quarter']:
        if feature_flags.get(feature, True):
            if feature == 'millisecond':
                data[feature] = data['timestamp'].dt.microsecond // 1000
            elif feature == 'week_of_year':
                data[feature] = data['timestamp'].dt.isocalendar().week.astype(int)
            else:
                data[feature] = getattr(data['timestamp'].dt, feature)
            # Criar recursos cíclicos se aplicável
            if feature in time_periods and feature_flags.get('seasonality', True):
                period = time_periods[feature]
                data[f'{feature}_sin'] = np.sin(2 * np.pi * data[feature] / period)
                data[f'{feature}_cos'] = np.cos(2 * np.pi * data[feature] / period)

    # Criar recurso 'is_weekend' se habilitado
    if feature_flags.get("is_weekend", True):
        data['is_weekend'] = data['timestamp'].dt.dayofweek >= 5

    # Componente de tendência
    if feature_flags.get('trend', False):  # Padrão é False
        data['time_index'] = np.arange(len(data))

    # Incluir componente de ciclos
    if feature_flags.get('cycles', False):  # Padrão é False
        n = len(data)
        data['time_index_sin'] = np.sin(2 * np.pi * data['time_index'] / n)
        data['time_index_cos'] = np.cos(2 * np.pi * data['time_index'] / n)

    # Tratar valores ausentes nas features
    data.fillna(method='ffill', inplace=True)
    data.fillna(method='bfill', inplace=True)

    return data

def get_feature_list(feature_flags):
    """Compila uma lista de recursos a serem usados para previsão."""
    features = []
    time_periods = {
        'hour': 24,
        'minute': 60,
        'second': 60,
        'millisecond': 1000,
        'day_of_year': 365,
        'week_of_year': 52,
        'month': 12,
        'day_of_week': 7,
        'quarter': 4,
    }

    for feature in ['hour', 'minute', 'second', 'millisecond', 'day_of_year',
                    'week_of_year', 'month', 'year', 'day_of_week', 'quarter']:
        if feature_flags.get(feature, True):
            features.append(feature)
            if feature in time_periods and feature_flags.get('seasonality', True):
                features.extend([f'{feature}_sin', f'{feature}_cos'])

    if feature_flags.get("is_weekend", True):
        features.append('is_weekend')

    if feature_flags.get('trend', False):
        features.append('time_index')

    if feature_flags.get('cycles', False):
        features.extend(['time_index_sin', 'time_index_cos'])

    return features

def prepare_future_data(future_timestamps, feature_flags):
    future_data = pd.DataFrame({'timestamp': future_timestamps})
    future_data = feature_engineering(future_data, feature_flags)
    FEATURES = get_feature_list(feature_flags)
    X_future = future_data[FEATURES]
    return X_future, future_timestamps

def perform_prediction(params):
    """Função principal para realizar a predição e detecção de anomalias futuras."""
    target_name = params["target_name"]

    # Carrega as informações do modelo
    model_info = load_model_info(target_name)

    # Carrega o modelo treinado
    model = load_trained_model(model_info["model_filename"])

    # Utiliza os feature_flags salvos no modelo treinado
    feature_flags = model_info.get("feature_flags")
    if not feature_flags:
        feature_flags = {}

    # Gerar timestamps futuros com base no horizonte de previsão
    forecast_horizon = params.get("forecast_horizon", 720)
    last_timestamp = pd.Timestamp.now()  # Utiliza o timestamp atual
    future_timestamps = pd.date_range(
        start=last_timestamp + pd.Timedelta(seconds=1),
        periods=forecast_horizon,
        freq='H'
    )

    # Preparar os dados futuros
    X_future, future_timestamps = prepare_future_data(future_timestamps, feature_flags)

    # Realiza predições para os timestamps futuros
    future_predictions = model.predict(X_future)

    # Detecta anomalias nas predições futuras
    future_anomalies = pd.Series([False] * len(future_predictions))
    if "threshold_max" in model_info and model_info["threshold_max"] is not None:
        future_anomalies = future_anomalies | (future_predictions > model_info["threshold_max"])
    if "threshold_min" in model_info and model_info["threshold_min"] is not None:
        future_anomalies = future_anomalies | (future_predictions < model_info["threshold_min"])

    future_data = pd.DataFrame({
        'timestamp': future_timestamps,
        'predicted_data': future_predictions,
        'anomaly_alert': future_anomalies.astype(bool)
    })

    result = future_data.to_dict(orient='records')

    output = {
        "message": "Previsão e detecção de anomalias futuras concluídas com sucesso.",
        "data": result
    }

    return output
