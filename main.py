# main.py

import json
from flask import redirect
from src.server.instance import app
from src.controllers.data_extraction_controller import register_extraction_routes
from src.controllers.data_preprocessing_controller import register_preprocessing_routes
from src.controllers.health_check_controller import register_health_routes
from src.controllers.attribute_mapping_controller import register_attribute_mapping_routes
from src.controllers.xgboost_train_controller import register_xgboost_train_routes
from src.controllers.predict_and_anomaly_detection_controller import register_prediction_routes
from flasgger import Swagger

# Carregar as configurações do arquivo config.json
with open('src/config.json') as config_file:
    config = json.load(config_file)

# Inicializa o Swagger
swagger = Swagger(app, config={
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
})

@app.route('/')
def home():
    return redirect('/apidocs')

# Registrar rotas das controllers
register_health_routes(app)
register_extraction_routes(app)
register_preprocessing_routes(app)
register_attribute_mapping_routes(app)
register_xgboost_train_routes(app)
register_prediction_routes(app)

# Exemplo de acesso às variáveis de configuração carregadas
sth_comet_host = config['sth_comet_host']
sth_comet_port = config['sth_comet_port']
orion_context_broker_host = config['orion_context_broker_host']
orion_context_broker_port = config['orion_context_broker_port']
service = config['fiware_service']
service_path = config['fiware_service_path']

# Agora, essas variáveis podem ser usadas em qualquer lugar do código
print(f"STH Comet Host: {sth_comet_host}")
print(f"Orion Context Broker Host: {orion_context_broker_host}")

if __name__ == '__main__':
    # Inicia o servidor Flask
    app.run(debug=True, host='0.0.0.0', port=5000)
