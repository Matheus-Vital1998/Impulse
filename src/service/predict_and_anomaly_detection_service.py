# src/service/predict_and_anomaly_detection_service.py

import pandas as pd
import numpy as np
from src.repository.predict_and_anomaly_detection_repository import (
    load_model_info,
    load_trained_model,
    load_processed_data
)
from datetime import datetime, timedelta, timezone

def feature_engineering(data, feature_flags, params):
    """Gera recursos baseados no tempo para os dados de entrada."""
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
            if feature == 'millisecond':
                data[feature] = data['timestamp'].dt.microsecond // 1000
            elif feature == 'week_of_year':
                data[feature] = data['timestamp'].dt.isocalendar().week.astype(int)
            else:
                data[feature] = getattr(data['timestamp'].dt, feature)
            # Criação de recursos cíclicos
            if feature in time_periods and feature_flags.get('seasonality', True):
                period = time_periods[feature]
                data[f'{feature}_sin'] = np.sin(2 * np.pi * data[feature] / period)
                data[f'{feature}_cos'] = np.cos(2 * np.pi * data[feature] / period)

    if feature_flags.get("is_weekend", True):
        data['is_weekend'] = data['timestamp'].dt.dayofweek >= 5

    if feature_flags.get('trend', False):
        data['time_index'] = np.arange(len(data))

    if feature_flags.get('cycles', False):
        n = len(data)
        data['time_index_sin'] = np.sin(2 * np.pi * data['time_index'] / n)
        data['time_index_cos'] = np.cos(2 * np.pi * data['time_index'] / n)

    # Atualizar o tratamento de NaNs
    data.ffill(inplace=True)
    data.bfill(inplace=True)

    # Resetar o índice
    data.reset_index(drop=True, inplace=True)

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

def prepare_future_data(future_timestamps, feature_flags, params):
    future_data = pd.DataFrame({'timestamp': future_timestamps})
    future_data = feature_engineering(future_data, feature_flags, params)
    FEATURES = get_feature_list(feature_flags)
    X_future = future_data[FEATURES]
    return X_future, future_timestamps

def perform_prediction(params):
    """Função principal para realizar a predição e detecção de anomalias."""
    target_name = params["target_name"]

    # Carrega as informações do modelo
    model_info = load_model_info(target_name)

    # Carrega o modelo treinado
    model = load_trained_model(model_info["model_filename"])

    # Utiliza os feature_flags salvos no modelo treinado
    feature_flags = model_info.get("feature_flags", {})

    # Remover 'microsecond' dos feature_flags se estiver presente
    if 'microsecond' in feature_flags:
        feature_flags['microsecond'] = False

    # Obter as datas de início e fim dos parâmetros
    date_from = params.get('date_from')
    date_to = params.get('date_to')

    # Se date_to não for fornecido, usar a data atual
    if not date_to:
        date_to = datetime.now(timezone.utc).isoformat()

    # Se date_from não for fornecido, usar date_to menos um período padrão (exemplo: 30 dias)
    if not date_from:
        date_from = (pd.to_datetime(date_to) - timedelta(days=30)).isoformat()

    # Carregar os dados históricos dentro do intervalo especificado
    data = load_processed_data(target_name, date_from=date_from, date_to=date_to)

    # Verificar se há dados suficientes
    if data.empty:
        raise ValueError("Nenhum dado histórico disponível no intervalo especificado.")

    # Manter apenas as colunas necessárias
    data = feature_engineering(data, feature_flags, params)

    # Preparar os dados históricos para previsão
    FEATURES = get_feature_list(feature_flags)
    X_historical = data[FEATURES]
    y_historical = data[target_name]

    # Fazer previsões nos dados históricos
    y_pred_historical = model.predict(X_historical)

    # Detectar anomalias nos dados históricos
    anomalies_historical = pd.Series([False]*len(y_historical))
    if "allowed_deviation" in model_info and model_info["allowed_deviation"] is not None:
        anomalies_historical = anomalies_historical | (np.abs(y_historical - y_pred_historical) > model_info["allowed_deviation"])
    if "threshold_max" in model_info and model_info["threshold_max"] is not None:
        anomalies_historical = anomalies_historical | (y_historical > model_info["threshold_max"])
    if "threshold_min" in model_info and model_info["threshold_min"] is not None:
        anomalies_historical = anomalies_historical | (y_historical < model_info["threshold_min"])

    # Criar DataFrame com os dados históricos
    historical_data = pd.DataFrame({
        'timestamp': data['timestamp'],
        'actual_data': y_historical,
        'predicted_data': y_pred_historical,
        'anomaly_alert': anomalies_historical.astype(bool)
    })

    # Gerar timestamps futuros com base no horizonte de previsão
    forecast_horizon = params.get("forecast_horizon", 720)
    last_timestamp = data['timestamp'].iloc[-1]
    future_timestamps = pd.date_range(
        start=last_timestamp + pd.Timedelta(seconds=1),
        periods=forecast_horizon,
        freq='H',
        tz=last_timestamp.tzinfo
    )

    # Preparar os dados futuros
    X_future, future_timestamps = prepare_future_data(future_timestamps, feature_flags, params)

    # Fazer previsões nos dados futuros
    future_predictions = model.predict(X_future)

    # Detectar anomalias nas previsões futuras
    future_anomalies = pd.Series([False] * len(future_predictions))
    if "threshold_max" in model_info and model_info["threshold_max"] is not None:
        future_anomalies = future_anomalies | (future_predictions > model_info["threshold_max"])
    if "threshold_min" in model_info and model_info["threshold_min"] is not None:
        future_anomalies = future_anomalies | (future_predictions < model_info["threshold_min"])

    # Criar DataFrame com os resultados futuros
    future_data = pd.DataFrame({
        'timestamp': future_timestamps,
        'actual_data': [None] * len(future_timestamps),
        'predicted_data': future_predictions,
        'anomaly_alert': future_anomalies.astype(bool)
    })

    # Combinar os dados históricos e futuros
    final_data = pd.concat([historical_data, future_data], ignore_index=True)

    # Ordenar por timestamp
    final_data.sort_values('timestamp', inplace=True)

    # Converter final_data para lista de dicionários
    result = final_data.to_dict(orient='records')

    output = {
        "message": "Previsão e detecção de anomalias concluídas com sucesso.",
        "data": result
    }

    return output
