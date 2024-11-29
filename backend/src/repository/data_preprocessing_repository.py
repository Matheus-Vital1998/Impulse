# src/repository/data_preprocessing_repository.py

import pandas as pd
import json

def load_data(file_path):
    """
    Carrega dados de um arquivo CSV.
    """
    try:
        data = pd.read_csv(file_path, delimiter=',')
        data.columns = data.columns.str.strip()
        print(f"Dados carregados com sucesso de {file_path}")
        return data
    except Exception as e:
        print(f"Erro ao carregar dados de {file_path}: {e}")
        return pd.DataFrame()

def save_data(data, file_path):
    """
    Salva dados em um arquivo CSV.
    """
    try:
        data.to_csv(file_path, index=False, sep=',')
        print(f"Dados salvos em {file_path}")
    except Exception as e:
        print(f"Erro ao salvar dados em {file_path}: {e}")

def load_preprocessing_log(preprocessing_log_file):
    """
    Carrega o log de pré-processamento de um arquivo JSON.
    """
    try:
        with open(preprocessing_log_file, 'r') as f:
            preprocessing_log = json.load(f)
        print(f"Log de pré-processamento carregado de {preprocessing_log_file}")
    except (FileNotFoundError, json.JSONDecodeError):
        preprocessing_log = {}
        print(f"Novo log de pré-processamento criado em {preprocessing_log_file}")
    return preprocessing_log

def save_preprocessing_log(preprocessing_log, preprocessing_log_file):
    """
    Salva o log de pré-processamento em um arquivo JSON.
    """
    try:
        with open(preprocessing_log_file, 'w') as f:
            json.dump(preprocessing_log, f, indent=4)
        print(f"Log de pré-processamento salvo em {preprocessing_log_file}")
    except Exception as e:
        print(f"Erro ao salvar log de pré-processamento em {preprocessing_log_file}: {e}")
