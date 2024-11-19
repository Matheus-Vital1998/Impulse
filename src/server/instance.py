from flask import Flask

# Cria a instância do app
app = Flask(__name__)

# Configurações básicas do Flask (se necessário)
app.config['DEBUG'] = True  # Habilita o modo de depuração (desative em produção)
