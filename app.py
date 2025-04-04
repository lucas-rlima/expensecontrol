from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# Usa a variável de ambiente DATABASE_URL do Render
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gastos.db'
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
    datas = db.session.query(Gasto.data).all()
    meses = sorted(set(d[0].strftime('%Y-%m') for d in datas))
    return meses

@app.route('/')
def index():
    mes_selecionado = request.args.get('mes') or datetime.today().strftime('%Y-%m')
    gastos = Gasto.query.filter(db.func.strftime('%Y-%m', Gasto.data) == mes_selecionado).all()
    meses_disponiveis = obter_meses_disponiveis()
    hoje = datetime.today().strftime('%Y-%m-%d')  # Obtém a data de hoje no formato YYYY-MM-DD
    return render_template("index.html", gastos=gastos, hoje=hoje, mes_atual=mes_selecionado, meses=meses_disponiveis)

@app.route('/add', methods=['POST'])
def add_gasto():
    categoria = request.form['categoria']
    valor = float(request.form['valor'])
    data = datetime.strptime(request.form['data'], '%Y-%m-%d')
    novo_gasto = Gasto(categoria=categoria, valor=valor, data=data)

    db.session.add(novo_gasto)
    db.session.commit()

    return redirect('/')

@app.route('/analisar')
def analisar():
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
                    f"Gasto alto detectado em {categoria} (R${gasto.valor:.2f}, acima da média de R${media:.2f})"
                )

    # 📊 Agrupa valores por dia
    gastos_por_dia = defaultdict(float)
    for gasto in gastos:
        dia = gasto.data.strftime('%d')  # Apenas o dia (01, 02, ...)
        gastos_por_dia[dia] += gasto.valor

    dias = sorted(gastos_por_dia.keys())
    valores = [gastos_por_dia[d] for d in dias]
    valor_maximo = max(gastos_por_dia.values()) if gastos_por_dia else 0
    valor_maximo_ajustado = ((valor_maximo // 250) + 1) * 250

    return render_template("analise.html", 
                           alertas=alertas, 
                           dias=dias, 
                           valores=valores, 
                           max_y=valor_maximo_ajustado,
                           mes_atual=mes_selecionado,
                           meses=meses_disponiveis)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

