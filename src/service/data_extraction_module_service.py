from src.repository.data_extraction_module_repository import get_sth_comet_data
from datetime import datetime

def convert_types(data):
    """
    Converte objetos datetime para string.
    """
    if isinstance(data, list):
        return [convert_types(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_types(value) for key, value in data.items()}
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def extract_data_service(date_from, date_to, limit, entities):
    """
    Serviço responsável por combinar os dados de diferentes entidades e atributos,
    utilizando timestamps como chave.
    """
    combined_data = {}

    for entity in entities:
        entity_id = entity["entity_id"]
        attributes = entity["attributes"]

        for attribute in attributes:
            data = get_sth_comet_data(entity_id, attribute, date_from, date_to, limit)
            for record in data:
                timestamp = record['recvTime']
                if timestamp not in combined_data:
                    combined_data[timestamp] = {'timestamp': timestamp}
                combined_data[timestamp][f"{entity_id}_{attribute}"] = record.get('attrValue', None)
    
    total_records = len(combined_data)
    
    if total_records > 0:
        combined_data = convert_types(list(combined_data.values()))
        return combined_data
    else:
        raise Exception("Nenhum registro encontrado no STH-Comet.")
