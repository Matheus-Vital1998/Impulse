# src/repository/attribute_mapping_repository.py

import requests
import json

# Carregar configurações do arquivo config.json
with open('src/config.json') as config_file:
    config = json.load(config_file)

orion_ip = config['orion_context_broker_host']
orion_port = config['orion_context_broker_port']
service = config['fiware_service']
service_path = config['fiware_service_path']

def get_entities_from_orion(limit=100):
    """
    Função para obter todas as entidades e seus atributos do Orion Context Broker.
    """
    url = f"http://{orion_ip}:{orion_port}/v2/entities"
    headers = {
        'Fiware-Service': service,
        'Fiware-ServicePath': service_path
    }
    params = {
        'limit': limit  # Limite de entidades por requisição
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erro ao acessar Orion Context Broker: {response.status_code} - {response.text}")
