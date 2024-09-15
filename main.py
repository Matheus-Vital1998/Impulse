from src.server.instance import app
from src.controllers.impulse import impulse_bp
from flasgger import Swagger

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

if __name__ == '__main__':
    # Inicia o servidor
    app.run(debug=True)
