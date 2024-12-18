import json
from flask import redirect, jsonify
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

# Configuração do Swagger
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
    "specs_route": "/apidocs/",
    "sorter": "none",
    "info": {
        "title": "Impulse API",
        "description": """
            Bem-vindo à documentação da API Impulse!<br>
            Esta API é usada para operações de extração, processamento e predição de dados integrados ao FIWARE.
        """,
        "version": "1.0.0",
        "termsOfService": "https://example.com/terms",
        "contact": {
            "name": "Equipe de Desenvolvimento",
            "email": "mat.vital.santos@gmail.com",
            "url": "https://github.com/Matheus-Vital1998/Impulse/tree/main?tab=readme-ov-file"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "tags": [
        {"name": "Health Check", "description": "Endpoints relacionados à saúde da API."},
        {"name": "Attribute Mapping", "description": "Mapeamento de atributos para modelos de dados."},
        {"name": "Data Extraction", "description": "Extração de dados do STH-Comet."},
        {"name": "Preprocessing", "description": "Pré-processamento de dados para modelos preditivos."},
        {"name": "Model Training", "description": "Treinamento de modelos usando XGBoost."},
        {"name": "Prediction & Anomaly Detection", "description": "Predição e detecção de anomalias."}
    ],
    "uiSettings": {
        "tagsSorter": "none",  # Ordena as tags conforme configuradas
        "operationsSorter": "none",  # Ordena as operações conforme registradas
        "docExpansion": "none",  # Recolhe descrições por padrão
        "filter": True  # Adiciona um campo de filtro no Swagger UI
    }
})

@app.route('/')
def home():
    return redirect('/apidocs')

# Registrar rotas das controllers na ordem desejada
register_health_routes(app)  # 1. Health Check
register_attribute_mapping_routes(app)  # 2. Attribute Mapping
register_extraction_routes(app)  # 3. Data Extraction
register_preprocessing_routes(app)  # 4. Preprocessing
register_xgboost_train_routes(app)  # 5. Model Training
register_prediction_routes(app)  # 6. Prediction & Anomaly Detection

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
