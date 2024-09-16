import requests

class WeatherStationRepository:
    def __init__(self, fiware_url):
        self.fiware_url = fiware_url

    def get_weather_data(self, entity_id):
        url = f'{self.fiware_url}/v2/entities/{entity_id}?attrs=temperature,humidity'
        headers = {
            'Fiware-Service': service,
            'Fiware-ServicePath': service_path
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
