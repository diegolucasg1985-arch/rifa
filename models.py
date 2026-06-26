from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Numero(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    numero = db.Column(
        db.Integer,
        unique=True,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="disponivel"
        "reservado"
        "pago"
    )

    nome = db.Column(
        db.String(100)
    )

    telefone = db.Column(
        db.String(20)
    )
   