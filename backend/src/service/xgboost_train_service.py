# src/service/xgboost_train_service.py

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, make_scorer
from src.repository.xgboost_train_repository import load_data, save_trained_model, save_model_info

def feature_engineering(data, feature_flags, params):
    """Gera recursos baseados no tempo com base nos flags fornecidos."""
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
        if feature_flags.get(feature, True):  # Padrão é True se feature_flags estiver ausente
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
    if feature_flags.get("is_weekend", True):  # Padrão é True
        data['is_weekend'] = data['timestamp'].dt.dayofweek >= 5

    # Componente de tendência
    if feature_flags.get('trend', True):
        # Incluir índice temporal como recurso para tendência
        data['time_index'] = np.arange(len(data))

    # Incluir componente de ciclos
    if feature_flags.get('cycles', True):
        # Incluir seno e cosseno do time_index para capturar ciclos
        n = len(data)
        data['time_index_sin'] = np.sin(2 * np.pi * data['time_index'] / n)
        data['time_index_cos'] = np.cos(2 * np.pi * data['time_index'] / n)

    # Aplicar suavização para remover ruído se 'denoise' for True
    if feature_flags.get('denoise', False):
        # Aplicar média móvel para suavizar a variável alvo
        data[params["target_name"]] = data[params["target_name"]].rolling(window=3, center=True).mean()
        data.dropna(inplace=True)  # Rolling introduz NaNs

    # Tratar valores ausentes
    data.dropna(inplace=True)
    data.fillna(data.mean(), inplace=True)
    return data

def get_feature_list(feature_flags):
    """Compila uma lista de recursos a serem usados no modelo."""
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

    # Construir a lista de recursos com base em feature_flags
    for feature in ['hour', 'minute', 'second', 'millisecond', 'day_of_year',
                    'week_of_year', 'month', 'year', 'day_of_week', 'quarter']:
        if feature_flags.get(feature, True):  # Padrão é True
            features.append(feature)
            if feature in time_periods and feature_flags.get('seasonality', True):
                features.extend([f'{feature}_sin', f'{feature}_cos'])

    if feature_flags.get("is_weekend", True):
        features.append('is_weekend')

    # Incluir 'time_index' se 'trend' for True
    if feature_flags.get('trend', True):
        features.append('time_index')

    # Incluir seno e cosseno do time_index se 'cycles' for True
    if feature_flags.get('cycles', True):
        features.extend(['time_index_sin', 'time_index_cos'])

    return features

def configure_xgboost_params(user_params):
    """Configura os hiperparâmetros do XGBoost, usando padrões quando necessário."""
    default_hyperparameters = {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 6,
        "subsample": 1,
        "colsample_bytree": 1,
        "gamma": 0,
        "reg_alpha": 0,
        "reg_lambda": 1,
        "min_child_weight": 1,
    }

    if not user_params:
        user_params = {}
    # Atualiza hiperparâmetros padrão com valores fornecidos pelo usuário
    for key, value in default_hyperparameters.items():
        if key not in user_params or user_params[key] is None:
            user_params[key] = value

    return user_params

def train_model(X, y, xgboost_params):
    """Treina o modelo XGBoost usando os dados e hiperparâmetros fornecidos."""
    model = xgb.XGBRegressor(objective='reg:squarederror', **xgboost_params)
    model.fit(X, y)
    return model

def perform_cross_validation(model, X, y):
    """Realiza validação cruzada em série temporal e calcula métricas de desempenho."""
    tscv = TimeSeriesSplit(n_splits=5)
    rmse_scorer = make_scorer(mean_squared_error, squared=False, greater_is_better=False)
    mape_scorer = make_scorer(mean_absolute_percentage_error, greater_is_better=False)

    cv_scores_rmse = cross_val_score(model, X, y, cv=tscv, scoring=rmse_scorer)
    mean_cv_rmse = -cv_scores_rmse.mean()  # Negativo porque greater_is_better=False
    std_cv_rmse = cv_scores_rmse.std()

    cv_scores_mape = cross_val_score(model, X, y, cv=tscv, scoring=mape_scorer)
    mean_cv_mape = -cv_scores_mape.mean()
    std_cv_mape = cv_scores_mape.std()

    metrics = {
        'Cross-Validated Root Mean Squared Error': float(mean_cv_rmse),
        'Standard Deviation of CV RMSE': float(std_cv_rmse),
        'Cross-Validated Mean Absolute Percentage Error': float(mean_cv_mape),
        'Standard Deviation of CV MAPE': float(std_cv_mape)
    }

    return metrics

def detect_anomalies(data, y_pred, params):
    """Detecta anomalias com base nos parâmetros de desvio e limiares."""
    y_actual = data[params["target_name"]]
    anomalies = pd.Series([False]*len(y_actual))

    # Verificar anomalias com base nos parâmetros fornecidos
    if "allowed_deviation" in params:
        anomalies = anomalies | (np.abs(y_actual - y_pred) > params["allowed_deviation"])
    if "threshold_max" in params:
        anomalies = anomalies | (y_actual > params["threshold_max"])
    if "threshold_min" in params:
        anomalies = anomalies | (y_actual < params["threshold_min"])

    anomaly_count = anomalies.sum()
    total_points = len(y_actual)
    anomaly_rate = anomaly_count / total_points if total_points > 0 else 0

    anomaly_metrics = {
        'Total Anomalies Detected': int(anomaly_count),
        'Total Data Points': int(total_points),
        'Anomaly Rate': float(anomaly_rate)
    }

    return anomaly_metrics

def get_feature_importances(model, features, feature_flags):
    """Calcula as importâncias das características detalhadas e simplificadas."""
    feature_importances = model.feature_importances_

    # Importâncias detalhadas das características
    feature_importance_list = sorted(
        zip(features, feature_importances),
        key=lambda x: x[1],
        reverse=True
    )
    feature_importance_list = [(feat, float(imp)) for feat, imp in feature_importance_list]

    # Importâncias simplificadas das características
    simplified_importances = {}
    for feat, imp in zip(features, feature_importances):
        # Remover sufixos '_sin' e '_cos' para obter a característica base
        if feat.endswith('_sin') or feat.endswith('_cos'):
            base_feat = feat[:-4]
        else:
            base_feat = feat
        simplified_importances[base_feat] = simplified_importances.get(base_feat, 0) + float(imp)

    # Garantir que todas as características ativas estejam incluídas
    for feature in feature_flags:
        if feature_flags.get(feature, True):
            if feature not in simplified_importances:
                simplified_importances[feature] = 0.0

    # Ordenar importâncias simplificadas
    simplified_importance_list = sorted(
        simplified_importances.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return simplified_importance_list, feature_importance_list

def train_xgboost_model(params):
    """Função principal para treinar o modelo XGBoost e retornar métricas."""
    # Verificar se 'target_name' é fornecido
    if 'target_name' not in params or not params['target_name']:
        raise ValueError('O parâmetro "target_name" é obrigatório e não pode estar vazio.')

    # Carregar dados
    file_path = 'processed_data.csv'
    data = load_data(file_path, params["target_name"])

    # Verificar se os dados foram carregados corretamente
    if data.empty:
        raise ValueError(f'Nenhum dado encontrado para o alvo "{params["target_name"]}".')

    # Tratar feature_flags padrão
    feature_flags = params.get("feature_flags")
    if not feature_flags:
        feature_flags = {feature: True for feature in ['hour', 'minute', 'second', 'millisecond',
                                                       'day_of_year', 'week_of_year', 'month', 'year',
                                                       'day_of_week', 'quarter', 'is_weekend',
                                                       'trend', 'seasonality', 'denoise', 'cycles']}

    # Engenharia de recursos nos dados históricos
    data = feature_engineering(data, feature_flags, params)

    # Obter lista de recursos
    FEATURES = get_feature_list(feature_flags)
    X = data[FEATURES]
    y = data[params["target_name"]]

    # Configurar hiperparâmetros do XGBoost
    xgboost_params = configure_xgboost_params(params.get("xgboost_hyperparameters"))

    # Treinar modelo
    model = train_model(X, y, xgboost_params)

    # Métricas de validação cruzada
    metrics = perform_cross_validation(model, X, y)

    # Prever nos dados de treinamento para detecção de anomalias
    y_pred = model.predict(X)

    # Detectar anomalias nos dados de treinamento se os parâmetros forem fornecidos
    if any(param in params for param in ["allowed_deviation", "threshold_max", "threshold_min"]):
        anomaly_metrics = detect_anomalies(data, y_pred, params)
        metrics.update(anomaly_metrics)

    # Obter importâncias das características
    simplified_importances, detailed_importances = get_feature_importances(model, FEATURES, feature_flags)
    metrics['Feature Importances Simplified'] = simplified_importances
    metrics['Feature Importances Detailed'] = detailed_importances

    # Converter métricas para tipos serializáveis
    for key, value in metrics.items():
        if isinstance(value, np.generic):
            metrics[key] = value.item()

    # Salvar o modelo treinado
    model_filename = save_trained_model(model, params['target_name'])

    # Salvar informações do modelo, incluindo métricas
    save_model_info(params, model_filename, metrics)

    return metrics
