import requests

def get_sth_comet_data(entity_id, entity_type, attribute, date_from, date_to, limit):
    sth_comet_ip = '127.0.0.1'
    sth_comet_port = 8666
    service = 'smart'
    service_path = '/'

    offset = 0
    attribute_data = []

    try:
        while True:
            url = f'http://{sth_comet_ip}:{sth_comet_port}/STH/v1/contextEntities/type/{entity_type}/id/{entity_id}/attributes/{attribute}'
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
