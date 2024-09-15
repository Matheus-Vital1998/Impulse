from flask import Flask

# Cria a instância do app
app = Flask(__name__)

# Configurações adicionais podem ser inseridas aqui
app.config['SWAGGER'] = {
    'title': 'Impulse API',
    'uiversion': 3
}
