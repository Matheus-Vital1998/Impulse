import requests
import json
with open('src/config.json') as config_file:  # Ajuste o caminho para refletir sua estrutura
    config = json.load(config_file)

def get_orion_version():
    """
    Função para obter a versão do Orion Context Broker.
    """
    orion_host = config['orion_context_broker_host']
    orion_port = config['orion_context_broker_port']

    url = f'http://{orion_host}:{orion_port}/version'

    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json().get("orion", {}).get("version", "unknown")
    else:
        raise Exception(f"Erro ao acessar Orion Context Broker: {response.status_code} - {response.text}")
