import json
from src.server.instance import app
from src.controllers.data_extraction_module_controller import register_extraction_routes
from src.controllers.health_check_controller import register_health_routes
from flasgger import Swagger

# Carregar as configurações do arquivo config.json
with open('src/config.json') as config_file:
    config = json.load(config_file)

# Inicializa o Swagger
swagger = Swagger(app, config={  # Simples inicialização do Swagger
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # Todas as rotas
            "model_filter": lambda tag: True,  # Todos os modelos
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
})

# Registrar rotas das controllers
register_extraction_routes(app)
register_health_routes(app)

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
    # Inicia o servidor Flask, já que você está usando Flask diretamente
    app.run(debug=True)
