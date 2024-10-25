# src/service/predict_and_anomaly_detection_service.py

import pandas as pd
import numpy as np
from src.repository.predict_and_anomaly_detection_repository import (
    load_model_info,
    update_model_info,
    load_trained_model,
    load_processed_data
)

def feature_engineering(data, feature_flags):
    """Gera atributos baseados no tempo para os dados de entrada."""
    # Define períodos para atributos cíclicos
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

    # Geração de atributos com base nos feature_flags
    for feature in ['hour', 'minute', 'second', 'millisecond', 'day_of_year',
                    'week_of_year', 'month', 'year', 'day_of_week', 'quarter']:
        if feature_flags.get(feature, True):
            if feature == 'millisecond':
                data[feature] = data['timestamp'].dt.microsecond // 1000
            elif feature == 'week_of_year':
                data[feature] = data['timestamp'].dt.isocalendar().week.astype(int)
            else:
                data[feature] = getattr(data['timestamp'].dt, feature)
            # Cria atributos cíclicos se aplicável
            if feature in time_periods:
                period = time_periods[feature]
                data[f'{feature}_sin'] = np.sin(2 * np.pi * data[feature] / period)
                data[f'{feature}_cos'] = np.cos(2 * np.pi * data[feature] / period)

    # Cria o atributo 'is_weekend' se habilitado
    if feature_flags.get("is_weekend", True):
        data['is_weekend'] = data['timestamp'].dt.dayofweek >= 5

    # Trata valores ausentes
    data.fillna(data.mean(), inplace=True)
    return data

def get_feature_list(feature_flags):
    """Compila a lista de atributos a serem usados para predição."""
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

    # Construção da lista de atributos com base nos feature_flags
    for feature in ['hour', 'minute', 'second', 'millisecond', 'day_of_year',
                    'week_of_year', 'month', 'year', 'day_of_week', 'quarter']:
        if feature_flags.get(feature, True):
            features.append(feature)
            if feature in time_periods:
                features.extend([f'{feature}_sin', f'{feature}_cos'])

    if feature_flags.get("is_weekend", True):
        features.append('is_weekend')

    return features

def prepare_future_data(future_timestamps, feature_flags):
    """Prepara os dados futuros para predição."""
    future_data = pd.DataFrame({'timestamp': future_timestamps})
    future_data = feature_engineering(future_data, feature_flags)
    FEATURES = get_feature_list(feature_flags)
    X_future = future_data[FEATURES]
    return X_future, future_timestamps

def perform_prediction(params):
    """Função principal para realizar a predição e detecção de anomalias."""
    target_name = params["target_name"]

    # Carrega e atualiza as informações do modelo
    model_info = update_model_info(target_name, params)

    # Carrega o modelo treinado
    model = load_trained_model(model_info["model_filename"])

    # Carrega os dados processados
    data = load_processed_data(target_name)

    # Trata os feature_flags padrão
    feature_flags = model_info.get("feature_flags")
    if not feature_flags:
        feature_flags = {feature: True for feature in ['hour', 'minute', 'second', 'millisecond',
                                                       'day_of_year', 'week_of_year', 'month', 'year',
                                                       'day_of_week', 'quarter', 'is_weekend']}

    # Aplica engenharia de atributos nos dados históricos
    data = feature_engineering(data, feature_flags)

    # Prepara os dados para predição
    FEATURES = get_feature_list(feature_flags)
    X = data[FEATURES]
    y = data[target_name]

    # Realiza predições nos dados históricos
    y_pred = model.predict(X)

    # Detecta anomalias nos dados históricos
    anomalies = pd.Series([False]*len(y), index=data.index)
    if "allowed_deviation" in model_info and model_info["allowed_deviation"] is not None:
        anomalies = anomalies | (np.abs(y - y_pred) > model_info["allowed_deviation"])
    if "threshold_max" in model_info and model_info["threshold_max"] is not None:
        anomalies = anomalies | (y > model_info["threshold_max"])
    if "threshold_min" in model_info and model_info["threshold_min"] is not None:
        anomalies = anomalies | (y < model_info["threshold_min"])

    # Gera timestamps futuros com base no horizonte de previsão
    forecast_horizon = params.get("forecast_horizon", 720)
    last_timestamp = data['timestamp'].iloc[-1]
    future_timestamps = pd.date_range(
        start=last_timestamp + pd.Timedelta(seconds=1),
        periods=forecast_horizon,
        freq='H',
        tz=last_timestamp.tzinfo
    )

    # Prepara os dados futuros
    X_future, future_timestamps = prepare_future_data(future_timestamps, feature_flags)

    # Realiza predições para os timestamps futuros
    future_predictions = model.predict(X_future)

    # Detecta anomalias nas predições futuras
    future_anomalies = pd.Series([False]*len(future_predictions), index=range(len(future_predictions)))
    if "threshold_max" in model_info and model_info["threshold_max"] is not None:
        future_anomalies = future_anomalies | (future_predictions > model_info["threshold_max"])
    if "threshold_min" in model_info and model_info["threshold_min"] is not None:
        future_anomalies = future_anomalies | (future_predictions < model_info["threshold_min"])

    # Combina dados históricos e futuros para retorno
    historical_data = pd.DataFrame({
        'timestamp': data['timestamp'],
        'actual_data': y,
        'predicted_data': y_pred,
        'anomaly_alert': anomalies
    })

    future_data = pd.DataFrame({
        'timestamp': future_timestamps,
        'predicted_data': future_predictions,
        'anomaly_alert': future_anomalies
    })

    # Concatenar os dados
    final_data = pd.concat([historical_data, future_data], ignore_index=True)

    # Converter alertas de anomalia para bool
    final_data['anomaly_alert'] = final_data['anomaly_alert'].astype(bool)

    # Retornar os dados como uma lista de dicionários
    result = final_data.to_dict(orient='records')
    return result
