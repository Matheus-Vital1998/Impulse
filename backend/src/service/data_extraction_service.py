# src/service/data_extraction_service.py

from src.repository.data_extraction_repository import get_sth_comet_data
from datetime import datetime
import csv
import shutil
import os

def convert_types(data):
    """
    Converte objetos datetime para strings no formato ISO.
    """
    if isinstance(data, list):
        return [convert_types(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_types(value) for key, value in data.items()}
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def extract_data(input_data, date_from, date_to):
    """
    Serviço responsável por extrair e combinar os dados das entidades e atributos,
    e salvar os dados em 'sth-comet_data.csv'.
    """
    combined_data = {}

    for entity in input_data["entities"]:
        entity_id = entity["entity_id"]
        entity_type = entity.get("entity_type", "DefaultType")
        attributes = entity["attributes"]
        
        for attribute in attributes:
            data = get_sth_comet_data(entity_type, entity_id, attribute, date_from, date_to)
            for record in data:
                timestamp = record['recvTime']
                if timestamp not in combined_data:
                    combined_data[timestamp] = {'timestamp': timestamp}
                key = f"{entity_id}_{attribute}"
                combined_data[timestamp][key] = record.get('attrValue', None)
            print(
                f"Dados para o atributo '{attribute}' da entidade '{entity_id}' "
                f"do tipo '{entity_type}' extraídos..."
            )

    combined_data_list = convert_types(list(combined_data.values()))

    # Salvar os dados combinados em CSV
    save_data_to_csv(combined_data_list, input_data)

    # Criar uma cópia de 'sth-comet_data.csv' nomeada 'preprocessing_data.csv'
    create_preprocessing_copy('sth-comet_data.csv', 'processed_data.csv')

def save_data_to_csv(data_list, input_data):
    """
    Salva os dados extraídos em um arquivo CSV chamado 'sth-comet_data.csv'.
    """
    filename = 'sth-comet_data.csv'
    headers = ['timestamp'] + [
        f"{entity['entity_id']}_{attr}"
        for entity in input_data["entities"]
        for attr in entity["attributes"]
    ]

    with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        for data in data_list:
            writer.writerow(data)
    print(f'Dados extraídos e salvos em "{filename}". Total de registros: {len(data_list)}')

def create_preprocessing_copy(source_file, destination_file):
    """
    Função para criar uma cópia do arquivo de dados para pré-processamento.
    """
    try:
        if os.path.exists(source_file):
            shutil.copyfile(source_file, destination_file)
            print(f"Cópia de '{source_file}' criada como '{destination_file}'.")
        else:
            print(f"O arquivo '{source_file}' não foi encontrado.")
    except Exception as e:
        print(f"Erro ao copiar o arquivo: {e}")
