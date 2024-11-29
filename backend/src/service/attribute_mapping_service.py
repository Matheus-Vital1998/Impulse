# src/service/attribute_mapping_service.py

from src.repository.attribute_mapping_repository import get_entities_from_orion

def format_to_input_data(entities):
    """
    Função para converter os dados no padrão input_data solicitado.
    """
    formatted_data = {
        "entities": []
    }
    
    for entity in entities:
        entity_data = {
            "entity_id": entity['id'],
            "entity_type": entity.get('type', 'DefaultType'),
            "attributes": [key for key in entity.keys() if key not in ['id', 'type']]
        }
        formatted_data["entities"].append(entity_data)
    
    return formatted_data

def get_formatted_entities(limit=100):
    """
    Serviço para obter as entidades formatadas a partir do Orion Context Broker.
    """
    entities = get_entities_from_orion(limit=limit)
    if entities:
        return format_to_input_data(entities)
    else:
        return {"entities": []}
