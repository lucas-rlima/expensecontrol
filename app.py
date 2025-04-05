from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from collections import defaultdict
import re

app = Flask(__name__)

# Usa a variável de ambiente DATABASE_URL do Render
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
database_url = os.getenv("DATABASE_URL", "")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo do banco de dados
class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, nullable=False, default=datetime.today)

# Cria as tabelas
with app.app_context():
    db.create_all()

def obter_meses_disponiveis():
    # Obtém os meses disponíveis no banco de dados
    datas = db.session.query(Gasto.data).all()
    meses = sorted(set(d[0].strftime('%Y-%m') for d in datas))
    return meses

@app.route('/')
def index():
    # Pega o mês atual ou o mês passado na URL
    mes_selecionado = request.args.get('mes') or datetime.today().strftime('%Y-%m')
    gastos = Gasto.query.filter(db.func.strftime('%Y-%m', Gasto.data) == mes_selecionado).all()
    meses_disponiveis = obter_meses_disponiveis()
    hoje = datetime.today().strftime('%Y-%m-%d')  # Obtém a data de hoje no formato YYYY-MM-DD
    return render_template("index.html", gastos=gastos, hoje=hoje, mes_atual=mes_selecionado, meses=meses_disponiveis)

@app.route('/add', methods=['POST'])
def add_gasto():
    # Adiciona um novo gasto
    categoria = request.form['categoria']
    valor = float(request.form['valor'])
    data = datetime.strptime(request.form['data'], '%Y-%m-%d')
    novo_gasto = Gasto(categoria=categoria, valor=valor, data=data)

    db.session.add(novo_gasto)
    db.session.commit()

    return redirect('/')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_gasto(id):
    # Encontra o gasto pelo ID
    gasto = Gasto.query.get_or_404(id)

    if request.method == 'POST':
        # Atualiza os dados do gasto
        gasto.categoria = request.form['categoria']
        gasto.valor = float(request.form['valor'])
        gasto.data = datetime.strptime(request.form['data'], '%Y-%m-%d')

        db.session.commit()
        return redirect('/')

    # Se for GET, exibe o formulário com os dados do gasto
    return render_template('editar_gasto.html', gasto=gasto)

@app.route('/excluir/<int:id>', methods=['GET'])
def excluir_gasto(id):
    # Encontra o gasto pelo ID
    gasto = Gasto.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    return redirect('/')

@app.route('/analisar')
def analisar():
    # Pega o mês atual ou o mês passado na URL para análise
    mes_selecionado = request.args.get('mes') or datetime.today().strftime('%Y-%m')
    gastos = Gasto.query.filter(db.func.strftime('%Y-%m', Gasto.data) == mes_selecionado).all()
    meses_disponiveis = obter_meses_disponiveis()

    # 🚨 Detecta gastos acima da média
    categorias = {}
    for gasto in gastos:
        categorias.setdefault(gasto.categoria, []).append(gasto.valor)

    alertas = []
    for categoria, valores in categorias.items():
        media = sum(valores) / len(valores)
        for gasto in Gasto.query.filter_by(categoria=categoria).all():
            if gasto.valor > media * 1.5 and gasto in gastos:  # só do mês atual
                alertas.append(
                    f"Gasto alto detectado em {categoria} (Foi gasto R${gasto.valor:.2f}, este valor está acima da média dessa categoria que é R${media:.2f})"
                )

    # 📊 Agrupa valores por dia
    gastos_por_dia = defaultdict(float)
    for gasto in gastos:
        dia = gasto.data.strftime('%d')  # Apenas o dia (01, 02, ...)
        gastos_por_dia[dia] += gasto.valor

    dias = sorted(gastos_por_dia.keys())
    valores = [gastos_por_dia[d] for d in dias]
    valor_maximo = max(gastos_por_dia.values()) if gastos_por_dia else 0
    valor_maximo_ajustado = ((valor_maximo // 250) + 1) * 250  # Ajuste do valor máximo do gráfico

    return render_template("analise.html", 
                           alertas=alertas, 
                           dias=dias, 
                           valores=valores, 
                           max_y=valor_maximo_ajustado,
                           mes_atual=mes_selecionado,
                           meses=meses_disponiveis)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
