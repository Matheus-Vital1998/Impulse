import requests
import json
with open('src/config.json') as config_file:  # Ajuste o caminho para refletir sua estrutura
    config = json.load(config_file)

def get_sth_comet_data(entity_id, attribute, date_from, date_to, limit):
    """
    Função responsável por buscar dados do STH-Comet para uma entidade e atributo específico.
    """
    offset = 0
    attribute_data = []
    
    sth_comet_ip = config['sth_comet_host']
    sth_comet_port = config['sth_comet_port']
    fiware_service = config['fiware_service']
    fiware_service_path = config['fiware_service_path']

    while True:
        url = f'http://{sth_comet_ip}:{sth_comet_port}/STH/v1/contextEntities/type/WeatherStation/id/{entity_id}/attributes/{attribute}'
        params = {
            'hLimit': limit,
            'hOffset': offset,
            'dateFrom': date_from,
            'dateTo': date_to
        }
        headers = {
            'Fiware-Service': fiware_service,
            'Fiware-ServicePath': fiware_service_path
        }

        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            contextResponses = data.get('contextResponses', [])

            if not contextResponses:
                break

            for item in contextResponses:
                attr = item.get('contextElement', {}).get('attributes', [{}])[0]
                values = attr.get('values', [])
                attribute_data.extend(values)
            
            if len(contextResponses[0]['contextElement']['attributes'][0]['values']) < limit:
                break

            offset += limit
        else:
            raise Exception(f"Erro ao acessar STH-Comet: {response.status_code} - {response.text}")

    return attribute_data
