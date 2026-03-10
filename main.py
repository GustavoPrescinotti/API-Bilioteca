from flask import Flask
import fdb
import sys

app = Flask(__name__)
app.config.from_pyfile('config.py')

host = app.config['DB_HOST']
database = app.config['DB_NAME']
user = app.config['DB_USE']
password = app.config['DB_PASSWORD']

try:
    con = fdb.connect(host=host, database=database, user=user, password=password)
    print('Conectado com sucesso!')
except Exception as e:
    print(f'Erro ao conectar no banco de dados: {e}')
    sys.exit(1)


app.config["DB_CONN"] = con

from view import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)