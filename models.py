from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Numero(db.Model):
    ...
    id = db.Column(db.Integer, primary_key=True)

    numero = db.Column(
        db.Integer,
        unique=True,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default="disponivel"
    )

    nome = db.Column(
        db.String(100)
    )

    telefone = db.Column(
        db.String(20)
    )

class Reserva(db.Model):
    __tablename__ = "reserva"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True)
    nome = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    valor_total = db.Column(db.Float)
    status = db.Column(db.String(20), default="aguardando_pagamento")
    data = db.Column(db.DateTime, default=datetime.utcnow)

    numeros = db.relationship("ReservaNumero", backref="reserva")

class ReservaNumero(db.Model):
    __tablename__ = "reserva_numero"

    id = db.Column(db.Integer, primary_key=True)

    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reserva.id")
    )

    numero_id = db.Column(
        db.Integer,
        db.ForeignKey("numero.id")
    )