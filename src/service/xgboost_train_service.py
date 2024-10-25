# src/service/xgboost_train_service.py

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, make_scorer
from src.repository.xgboost_train_repository import load_data, save_trained_model, save_model_info

def feature_engineering(data, feature_flags):
    """Gera atributos baseados em tempo com base nos flags fornecidos."""
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

    # Geração de atributos com base nos flags
    for feature in ['hour', 'minute', 'second', 'millisecond', 'day_of_year',
                    'week_of_year', 'month', 'year', 'day_of_week', 'quarter']:
        if feature_flags.get(feature, True):  # Padrão é True se o flag estiver ausente
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
    if feature_flags.get("is_weekend", True):  # Padrão é True
        data['is_weekend'] = data['timestamp'].dt.dayofweek >= 5

    # Trata valores ausentes
    data.dropna(inplace=True)
    data.fillna(data.mean(), inplace=True)
    return data

def get_feature_list(feature_flags):
    """Compila a lista de atributos a serem usados no modelo."""
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

    # Construção da lista de atributos com base nos flags
    for feature in ['hour', 'minute', 'second', 'millisecond', 'day_of_year',
                    'week_of_year', 'month', 'year', 'day_of_week', 'quarter']:
        if feature_flags.get(feature, True):  # Padrão é True
            features.append(feature)
            if feature in time_periods:
                features.extend([f'{feature}_sin', f'{feature}_cos'])

    if feature_flags.get("is_weekend", True):
        features.append('is_weekend')

    return features

def configure_xgboost_params(user_params):
    """Configura os hiperparâmetros do XGBoost, usando padrões onde necessário."""
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
    # Atualiza os hiperparâmetros padrão com os valores fornecidos pelo usuário
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
    """Realiza validação cruzada temporal e calcula métricas de desempenho."""
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

    # Verifica anomalias com base nos parâmetros fornecidos
    if "allowed_deviation" in params:
        anomalies = anomalies | (np.abs(y_actual - y_pred) > params["allowed_deviation"])
    if "threshold_max" in params:
        anomalies = anomalies | (y_actual > params["threshold_max"])
    if "threshold_min" in params:
        anomalies = anomalies | (y_actual < params["threshold_min"])

    anomaly_count = anomalies.sum()
    total_points = len(y_actual)
    anomaly_percentage = (anomaly_count / total_points) * 100 if total_points > 0 else 0

    anomaly_metrics = {
        'Total Anomalies Detected': int(anomaly_count),
        'Total Data Points': int(total_points),
        'Anomaly Percentage': float(anomaly_percentage)
    }

    return anomaly_metrics

def get_feature_importances(model, features, feature_flags):
    """Calcula as importâncias dos atributos detalhadas e simplificadas."""
    feature_importances = model.feature_importances_

    # Importâncias detalhadas dos atributos
    feature_importance_list = sorted(
        zip(features, feature_importances),
        key=lambda x: x[1],
        reverse=True
    )
    feature_importance_list = [(feat, float(imp)) for feat, imp in feature_importance_list]

    # Importâncias simplificadas dos atributos
    simplified_importances = {}
    for feat, imp in zip(features, feature_importances):
        # Remove sufixos '_sin' e '_cos' para obter o atributo base
        if feat.endswith('_sin') or feat.endswith('_cos'):
            base_feat = feat[:-4]
        else:
            base_feat = feat
        simplified_importances[base_feat] = simplified_importances.get(base_feat, 0) + float(imp)

    # Garante que todos os atributos ativos sejam incluídos
    for feature in feature_flags:
        if feature_flags.get(feature, True):
            if feature not in simplified_importances:
                simplified_importances[feature] = 0.0

    # Ordena as importâncias simplificadas
    simplified_importance_list = sorted(
        simplified_importances.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return simplified_importance_list, feature_importance_list

def train_xgboost_model(params):
    """Função principal para treinar o modelo XGBoost e retornar métricas."""
    # Carrega os dados
    file_path = 'processed_data.csv'
    data = load_data(file_path, params["target_name"])

    # Trata os feature_flags padrão
    feature_flags = params.get("feature_flags")
    if not feature_flags:
        feature_flags = {feature: True for feature in ['hour', 'minute', 'second', 'millisecond',
                                                       'day_of_year', 'week_of_year', 'month', 'year',
                                                       'day_of_week', 'quarter', 'is_weekend']}

    # Engenharia de atributos nos dados históricos
    data = feature_engineering(data, feature_flags)

    # Obtem a lista de atributos
    FEATURES = get_feature_list(feature_flags)
    X = data[FEATURES]
    y = data[params["target_name"]]

    # Configura os hiperparâmetros do XGBoost
    xgboost_params = configure_xgboost_params(params.get("xgboost_hyperparameters"))

    # Treina o modelo
    model = train_model(X, y, xgboost_params)

    # Métricas de validação cruzada
    metrics = perform_cross_validation(model, X, y)

    # Predição nos dados de treinamento para detecção de anomalias
    y_pred = model.predict(X)

    # Detecta anomalias nos dados de treinamento se os parâmetros forem fornecidos
    if any(param in params for param in ["allowed_deviation", "threshold_max", "threshold_min"]):
        anomaly_metrics = detect_anomalies(data, y_pred, params)
        metrics.update(anomaly_metrics)

    # Obtem as importâncias dos atributos
    simplified_importances, detailed_importances = get_feature_importances(model, FEATURES, feature_flags)
    metrics['Feature Importances Simplified'] = simplified_importances
    metrics['Feature Importances Detailed'] = detailed_importances

    # Salva o modelo treinado
    model_filename = save_trained_model(model, params['target_name'])

    # Salva as informações do modelo, incluindo métricas
    save_model_info(params, model_filename, metrics)

    return metrics
