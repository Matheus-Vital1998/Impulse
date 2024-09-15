from src.repository.weather_station_repository import get_sth_comet_data
from datetime import datetime

def extract_data_service(data):
    date_from = data['date_from']
    date_to = data['date_to']
    limit = data['limit']
    entities = data['entities']

    combined_data = {}
    print(f"Extraction started...")

    for entity in entities:
        entity_id = entity['entity_id']
        entity_type = entity['entity_type']
        attributes = entity['attributes']
        
        for attribute in attributes:
            attribute_data = get_sth_comet_data(entity_id, entity_type, attribute, date_from, date_to, limit)
            for record in attribute_data:
                timestamp = record['recvTime']
                if timestamp not in combined_data:
                    combined_data[timestamp] = {'timestamp': timestamp}
                combined_data[timestamp][attribute] = record.get('attrValue', None)
            print(f"Data for attribute '{attribute}' from entity '{entity_id}' extracted...")

    total_records = len(combined_data)
    print(f"Total combined records: {total_records}")

    if total_records > 0:
        combined_data = convert_types(list(combined_data.values()))
        save_data_to_file(combined_data, attributes)
        print(f'Data extracted and saved to "weather_station_data.txt". Total records: {total_records}')
    else:
        print("No records found in STH-Comet API.")

    return combined_data

def convert_types(data):
    if isinstance(data, list):
        return [convert_types(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_types(value) for key, value in data.items()}
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def save_data_to_file(data, attributes):
    with open('weather_station_data.txt', 'w') as file:
        file.write("timestamp," + ",".join(attributes) + "\n")
        for record in data:
            line = record['timestamp']
            for attribute in attributes:
                line += "," + str(record.get(attribute, ''))
            file.write(line + '\n')
