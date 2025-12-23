from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import routes
import analysis


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:qweasd@127.0.0.1:3306/wine?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'

db=SQLAlchemy(app)


if __name__ == '__main__':
    app.run()
