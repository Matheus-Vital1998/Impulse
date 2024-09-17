import requests

class WeatherStationRepository:
    def __init__(self, orion_host, orion_port, service, service_path):
        self.orion_url = f'http://{orion_host}:{orion_port}'
        self.service = service
        self.service_path = service_path

    def get_weather_data(self, entity_id):
        url = f'{self.orion_url}/v2/entities/{entity_id}?attrs=temperature,humidity'
        headers = {
            'Fiware-Service': self.service,
            'Fiware-ServicePath': self.service_path
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
