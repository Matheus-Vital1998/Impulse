# src/service/data_extraction_service.py

from src.repository.data_extraction_repository import get_sth_comet_data
from datetime import datetime

def convert_types(data):
    """
    Converte objetos datetime para strings ISO format.
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
    Serviço responsável por extrair e combinar os dados das entidades e atributos.
    """
    combined_data = {}

    for entity in input_data["entities"]:
        entity_id = entity["entity_id"]
        entity_type = entity.get("entity_type", "DefaultType")  # Define um tipo padrão se não for fornecido
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
    return combined_data_list
