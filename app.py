from flask import Flask, render_template, request, redirect, session, url_for
from models import db, Numero
import pandas as pd
from flask import send_file

app = Flask(__name__)

app.secret_key = "rifa2026"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
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

    arrecadado = reservados * 15
    percentual = round((reservados / 200) * 100)

    return render_template(
    "admin.html",
    numeros=numeros,
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