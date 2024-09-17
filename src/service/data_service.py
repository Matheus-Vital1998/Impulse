import requests
from datetime import datetime
from src.repository.weather_station_repository import WeatherStationRepository

class DataService:
    def __init__(self, sth_comet_ip, sth_comet_port, service, service_path, orion_host, orion_port):
        # Repositório que mantém a conexão com a API do Fiware e STH-Comet
        self.repository = WeatherStationRepository(orion_host, orion_port, service, service_path)
        self.sth_comet_ip = sth_comet_ip
        self.sth_comet_port = sth_comet_port
        self.service = service
        self.service_path = service_path

    def get_weather_data_service(self, entity_id):
        """Obtém dados meteorológicos usando a repository."""
        return self.repository.get_weather_data(entity_id)

    def extract_data_service(self, date_from, date_to, limit, entities):
        """
        Extrai os dados do STH-Comet para múltiplas entidades e atributos.
        """
        combined_data = {}
        
        for entity in entities:
            entity_id = entity['entity_id']
            entity_type = entity['entity_type']
            attributes = entity['attributes']
            
            for attribute in attributes:
                try:
                    # Obtém os dados do STH-Comet via repository
                    attribute_data = self.get_sth_comet_data(entity_id, entity_type, attribute, date_from, date_to, limit)
                    for record in attribute_data:
                        timestamp = record['recvTime']
                        if timestamp not in combined_data:
                            combined_data[timestamp] = {'timestamp': timestamp}
                        combined_data[timestamp][attribute] = record.get('attrValue', None)
                except Exception as e:
                    print(f"Error extracting data for entity {entity_id}, attribute {attribute}: {e}")

        if combined_data:
            combined_data = self.convert_types(list(combined_data.values()))

            # Salva o resultado em um arquivo .txt
            self.save_to_txt(combined_data)

            return combined_data
        else:
            return {"message": "No data found"}

    def get_sth_comet_data(self, entity_id, entity_type, attribute, date_from, date_to, limit):
        offset = 0
        attribute_data = []

        sth_comet_url = f"http://{self.sth_comet_ip}:{self.sth_comet_port}"

        try:
            while True:
                url = f'{sth_comet_url}/STH/v1/contextEntities/type/{entity_type}/id/{entity_id}/attributes/{attribute}'
                params = {
                    'hLimit': limit,
                    'hOffset': offset,
                    'dateFrom': date_from,
                    'dateTo': date_to
                }
                headers = {
                    'Fiware-Service': self.service,
                    'Fiware-ServicePath': self.service_path
                }

                print(f"Request URL: {url}")
                print(f"Request Params: {params}")

                response = requests.get(url, params=params, headers=headers)
                print(f"Response Status: {response.status_code}")
                print(f"Response Text: {response.text}")

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
                    print(f"Error accessing API: {response.status_code} - {response.text}")
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            return attribute_data

    def convert_types(self, data):
        """Converte tipos de dados para garantir que os formatos estejam corretos."""
        if isinstance(data, list):
            return [self.convert_types(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.convert_types(value) for key, value in data.items()}
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    def save_to_txt(self, data):
        """Salva os dados extraídos em um arquivo .txt."""
        try:
            with open('extracted_data.txt', 'w') as file:
                for record in data:
                    file.write(f"{record}\n")
            print("Dados salvos em extracted_data.txt")
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")
