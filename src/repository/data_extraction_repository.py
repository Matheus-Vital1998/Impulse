# src/repository/data_extraction_repository.py

import requests
import json

# Carregar configurações do arquivo config.json
with open('src/config.json') as config_file:
    config = json.load(config_file)

sth_comet_ip = config['sth_comet_host']
sth_comet_port = config['sth_comet_port']
service = config['fiware_service']
service_path = config['fiware_service_path']

def get_sth_comet_data(entity_type, entity_id, attribute, date_from, date_to, limit=100):
    """
    Função para obter dados da API STH-Comet para um atributo específico.
    """
    offset = 0
    attribute_data = []

    while True:
        url = (
            f'http://{sth_comet_ip}:{sth_comet_port}/STH/v1/contextEntities/'
            f'type/{entity_type}/id/{entity_id}/attributes/{attribute}'
        )
        params = {
            'hLimit': limit,
            'hOffset': offset,
            'dateFrom': date_from,
            'dateTo': date_to
        }
        headers = {
            'Fiware-Service': service,
            'Fiware-ServicePath': service_path
        }

        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            context_responses = data.get('contextResponses', [])

            if not context_responses:
                break

            for item in context_responses:
                attr = item.get('contextElement', {}).get('attributes', [{}])[0]
                values = attr.get('values', [])
                attribute_data.extend(values)
            
            if len(values) < limit:
                break

            offset += limit
        else:
            raise Exception(
                f"Erro ao acessar API STH-Comet: {response.status_code} - "
                f"{response.text}"
            )

    return attribute_data
