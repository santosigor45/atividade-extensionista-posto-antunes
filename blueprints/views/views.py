from flask import render_template, redirect, url_for, send_from_directory, abort
from flask_login import current_user
from models import *


def home():
    if current_user.is_authenticated:
        return render_template("home.html")
    else:
        return redirect(url_for('views.login'))


def abastecimentos():
    motoristas = [motorista for motorista in Motoristas.query.all()]
    postos = [posto for posto in Postos.query.all()]
    cidades = [cidade for cidade in Cidades.query.all()]
    placas = [placa for placa in Placas.query.all()]
    return render_template("abastecimentos.html", placas=placas, postos=postos,
                           cidades=cidades, motoristas=motoristas)


def entrega_combustivel():
    postos_proprios = [posto for posto in Postos.query.all() if "bomba" in posto.posto.lower()]
    return render_template("entrega_combustivel.html", postos_proprios=postos_proprios)


def pesquisar():
    return render_template('pesquisar/pesquisar.html')


def pesquisar_tables(table):
    template = f'pesquisar/pesquisar_{table}.html'
    context = {}

    if table == 'abastecimentos':
        context = {
            'motoristas': Motoristas.query.all(),
            'postos': Postos.query.all(),
            'cidades': Cidades.query.all(),
            'placas': Placas.query.all()
        }
    elif table == 'entrega_combustivel':
        context['postos_proprios'] = [
            posto for posto in Postos.query.all()
            if "bomba" in posto.posto.lower()
        ]

    return render_template(template, **context)


def graficos():
    return render_template('graficos.html')


def serve_file(filename):
    return send_from_directory('', filename)


def health_check():
    return 'OK', 200
