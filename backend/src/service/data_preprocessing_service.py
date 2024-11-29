# src/service/data_preprocessing_service.py

import pandas as pd
import numpy as np
from scipy.stats import zscore
from sklearn.preprocessing import MinMaxScaler, StandardScaler

def handle_missing_values(data, column, method, preprocessing_log):
    """
    Trata valores ausentes em uma coluna específica usando o método especificado.
    """
    existing_method = preprocessing_log[column]['missing_values']
    if existing_method and existing_method != method:
        print(f"Não é possível aplicar o método de valores ausentes '{method}' na coluna '{column}' porque o método '{existing_method}' já foi aplicado.")
        return data
    try:
        if method == 'drop':
            data.dropna(subset=[column], inplace=True)
            preprocessing_log[column]['missing_values'] = method
        elif method == 'mean':
            if pd.api.types.is_numeric_dtype(data[column]):
                mean_value = data[column].mean()
                data[column].fillna(mean_value, inplace=True)
                preprocessing_log[column]['missing_values'] = method
            else:
                raise ValueError(f"Não é possível calcular a média para a coluna não numérica '{column}'")
        elif method == 'median':
            if pd.api.types.is_numeric_dtype(data[column]):
                median_value = data[column].median()
                data[column].fillna(median_value, inplace=True)
                preprocessing_log[column]['missing_values'] = method
            else:
                raise ValueError(f"Não é possível calcular a mediana para a coluna não numérica '{column}'")
        elif method == 'ffill':
            data[column].fillna(method='ffill', inplace=True)
            preprocessing_log[column]['missing_values'] = method
        elif method == 'bfill':
            data[column].fillna(method='bfill', inplace=True)
            preprocessing_log[column]['missing_values'] = method
        elif method == 'interpolate':
            data[column] = data[column].interpolate()
            preprocessing_log[column]['missing_values'] = method
        else:
            print(f"Método de tratamento de valores ausentes desconhecido '{method}' para a coluna '{column}'")
    except Exception as e:
        print(f"Erro ao tratar valores ausentes na coluna '{column}': {e}")
    return data

def handle_outliers(data, column, method, preprocessing_log):
    """
    Trata outliers em uma coluna específica usando o método especificado.
    """
    existing_method = preprocessing_log[column]['outliers']
    if existing_method and existing_method != method:
        print(f"Não é possível aplicar o método de outliers '{method}' na coluna '{column}' porque o método '{existing_method}' já foi aplicado.")
        return data
    try:
        if pd.api.types.is_numeric_dtype(data[column]):
            if method == 'remove':
                z_scores = zscore(data[column].dropna())
                abs_z_scores = np.abs(z_scores)
                filtered_entries = abs_z_scores < 3
                data = data.loc[data[column].dropna().index[filtered_entries]]
                preprocessing_log[column]['outliers'] = method
            elif method == 'cap':
                q1 = data[column].quantile(0.25)
                q3 = data[column].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                data[column] = data[column].clip(lower=lower_bound, upper=upper_bound)
                preprocessing_log[column]['outliers'] = method
            else:
                print(f"Método de tratamento de outliers desconhecido '{method}' para a coluna '{column}'")
        else:
            print(f"Não é possível tratar outliers na coluna não numérica '{column}'")
    except Exception as e:
        print(f"Erro ao tratar outliers na coluna '{column}': {e}")
    return data

def handle_scaling(data, column, method, scaler_dict, preprocessing_log):
    """
    Aplica escalonamento a uma coluna específica usando o método especificado.
    """
    existing_method = preprocessing_log[column]['normalization']
    if existing_method and existing_method != method:
        print(f"Não é possível aplicar o método de normalização '{method}' na coluna '{column}' porque o método '{existing_method}' já foi aplicado.")
        return data
    try:
        if pd.api.types.is_numeric_dtype(data[column]):
            if method == 'minmax':
                scaler = MinMaxScaler()
                data[[column]] = scaler.fit_transform(data[[column]])
                scaler_dict[column] = scaler
                preprocessing_log[column]['normalization'] = method
            elif method == 'standard':
                scaler = StandardScaler()
                data[[column]] = scaler.fit_transform(data[[column]])
                scaler_dict[column] = scaler
                preprocessing_log[column]['normalization'] = method
            else:
                print(f"Método de escalonamento desconhecido '{method}' para a coluna '{column}'")
        else:
            print(f"Não é possível escalonar a coluna não numérica '{column}'")
    except Exception as e:
        print(f"Erro ao escalonar a coluna '{column}': {e}")
    return data

def analyze_data(data, preprocessing_log):
    """
    Analisa os dados após o tratamento para gerar recomendações.
    """
    analysis = {}
    numeric_columns = data.select_dtypes(include='number').columns
    for column in data.columns:
        missing_count = int(data[column].isnull().sum())
        outlier_count = None
        normalization_applied = preprocessing_log[column]['normalization'] != ""
        if column in numeric_columns:
            # Identifica outliers usando z-score
            z_scores = zscore(data[column].dropna())
            outliers = np.abs(z_scores) > 3
            outlier_count = int(np.sum(outliers))
        else:
            outlier_count = None
        analysis[column] = {
            'missing_values': missing_count,
            'outliers': outlier_count,
            'normalization': normalization_applied
        }
    return analysis
