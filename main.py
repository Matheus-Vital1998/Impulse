import json
from src.server.instance import app
from src.controllers.impulse import impulse_bp
from flasgger import Swagger

# Carregar as configurações do arquivo config.json
with open('config.json') as config_file:
    config = json.load(config_file)

# Inicializa o Swagger
swagger = Swagger(app, config={
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

# Registro do Blueprint do controlador impulse
app.register_blueprint(impulse_bp, url_prefix='/api')

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
    # Inicia o servidor
    app.run(debug=True)
