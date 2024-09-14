from flask import Flask
from flask_restx import Api, Resource  # Alteração de restplus para restx

from src.server.instance import server

app, api = server.app, server.api

primeiro_teste_db = [
    {'id': 0, 'title': 'Teste 1'},
    {'id': 1, 'title': 'Teste 2'}
]

@api.route('/impulse')
class Impulse(Resource):
    def get(self):
        return primeiro_teste_db
