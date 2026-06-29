from flask import Flask, render_template, request, redirect, session, url_for
from sqlalchemy import case
from models import db, Numero, Reserva, ReservaNumero
import pandas as pd
from flask import send_file
import random
import string

app = Flask(__name__)

#Configuração da rifa

VALOR_NUMERO = 15.00
app.secret_key = "rifa2026"

import os

database_url = os.getenv("DATABASE_URL", "sqlite:///database.db")

if database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():

    db.create_all()

    if Numero.query.count() == 0:

        for i in range(1, 201):

            db.session.add(
                Numero(numero=i)
            )

        db.session.commit()

def gerar_codigo():
    codigo = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6,
        )
    )
    return f"MONY-{codigo}"

@app.route("/")
def index():

    numeros = Numero.query.order_by(Numero.numero).all()

    reservados = Numero.query.filter(
        Numero.status.in_(["reservado", "pago"])
    ).count()

    disponiveis = Numero.query.filter_by(
        status="disponivel"
    ).count()

    return render_template(
        "index.html",
        numeros=numeros,
        reservados=reservados,
        disponiveis=disponiveis
    )
    
@app.route("/reservar/<int:id>", methods=["GET", "POST"])
def reservar(id):

    numero = Numero.query.get(id)

    if request.method == "POST":

        numero.nome = request.form["nome"]
        numero.telefone = request.form["telefone"]
        numero.status = "reservado"

        db.session.commit()

        return render_template(
    "sucesso.html",
    numero=numero
)

    return render_template(
    "reservar.html",
    numero=numero
)
   
@app.route("/checkout")
def checkout():

    ids = request.args.get("ids", "")

    if ids == "":
        return redirect(url_for("index"))

    lista_ids = [int(i) for i in ids.split(",")]

    numeros = Numero.query.filter(
        Numero.id.in_(lista_ids)
    ).order_by(
        case(
            *[(Numero.id == i, pos) for pos, i in enumerate(lista_ids)],
            else_=999
        )
    ).all()

    total = len(numeros) * VALOR_NUMERO

    return render_template(
        "checkout.html",
        numeros=numeros,
        total=total
    )

@app.route("/confirmar_reserva", methods=["POST"])
def confirmar_reserva():

    nome = request.form["nome"]
    telefone = request.form["telefone"]

    ids = [
        int(id_numero)
        for id_numero in request.form.getlist("ids")
        if id_numero
    ]

    codigo = gerar_codigo()

    reserva = Reserva(
        codigo=codigo,
        nome=nome,
        telefone=telefone,
        valor_total=len(ids) * VALOR_NUMERO,
    )

    db.session.add(reserva)
    db.session.flush()

    for id_numero in ids:

        numero = Numero.query.get(id_numero)

        if not numero:
            continue

        if numero.status != "disponivel":
            return f"O número {numero.numero} não está mais disponível."

        numero.nome = nome
        numero.telefone = telefone
        numero.status = "reservado"

        db.session.add(
            ReservaNumero(
                reserva_id=reserva.id,
                numero_id=numero.id,
            )
        )

    db.session.commit()

    numeros = (
        Numero.query.filter(Numero.id.in_(ids))
        .order_by(Numero.numero)
        .all()
    )

    total = len(numeros) * VALOR_NUMERO

    return render_template(
        "pagamento.html",
        numeros=numeros,
        total=total,
        reserva=reserva,
    )

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        senha = request.form["senha"]

        if senha == "123456":

            session["admin"] = True

            return redirect("/admin")

    return render_template("login.html")

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")
    busca = request.args.get("busca", "")

    if busca:
        numeros = Numero.query.filter(
        (Numero.nome.contains(busca)) |
        (Numero.numero.like(f"%{busca}%"))
    ).order_by(Numero.numero).all()

    else:
        numeros = Numero.query.order_by(
        Numero.numero
    ).all()

    reservados = Numero.query.filter(
        Numero.status.in_(["reservado", "pago"])
    ).count()

    disponiveis = Numero.query.filter_by(
        status="disponivel"
    ).count()

    arrecadado = reservados * VALOR_NUMERO
    percentual = round((reservados / 200) * 100)
    reservas = Reserva.query.order_by(Reserva.data.desc()).all()

    return render_template(
    "admin.html",
    numeros=numeros,
    reservas=reservas,
    reservados=reservados,
    disponiveis=disponiveis,
    arrecadado=arrecadado,
    percentual=percentual,
    busca=busca
    
    )

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

@app.route("/confirmar_pagamento/<int:id>")
def confirmar_pagamento(id):

    if not session.get("admin"):
        return redirect("/login")

    reserva = Reserva.query.get(id)

    if not reserva:
        return "Reserva não encontrada."

    reserva.status = "pago"

    for item in reserva.numeros:
        numero = Numero.query.get(item.numero_id)

        if numero:
            numero.status = "pago"

    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/cancelar_reserva/<int:id>")
def cancelar_reserva(id):

    if not session.get("admin"):
        return redirect("/login")

    reserva = Reserva.query.get(id)

    if not reserva:
        return "Reserva não encontrada."

    for item in reserva.numeros:
        numero = Numero.query.get(item.numero_id)

        if numero and reserva.status != "pago":
            numero.status = "disponivel"
            numero.nome = None
            numero.telefone = None

    reserva.status = "cancelada"

    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/toggle/<int:id>")
def toggle(id):

    numero = Numero.query.get(id)

    if numero.status == "disponivel":
        numero.status = "reservado"

    elif numero.status == "reservado":
        numero.status = "pago"

    else:
        numero.status = "disponivel"

    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/exportar")
def exportar():

    if not session.get("admin"):
        return redirect("/login")

    numeros = Numero.query.order_by(Numero.numero).all()

    dados = []

    for numero in numeros:
        dados.append({
            "Número": f"{numero.numero:03d}",
            "Nome": numero.nome or "",
            "Telefone": numero.telefone or "",
            "Status": numero.status
        })

    df = pd.DataFrame(dados)

    arquivo = "participantes.xlsx"
    df.to_excel(arquivo, index=False)

    return send_file(
        arquivo,
        as_attachment=True
    )



if __name__ == "__main__":
    app.run(debug=True)