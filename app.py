from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configura o caminho do banco de dados PostgreSQL do Supabase
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://usuario:senha@host:porta/nome_do_banco'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cria o objeto de banco de dados
db = SQLAlchemy(app)

# Define o modelo da tabela "Ingrediente"
class Ingrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID único
    nome = db.Column(db.String(100), nullable=False)  # Nome do ingrediente
    quantidade = db.Column(db.Float, nullable=False)  # Quantidade disponível
    unidade = db.Column(db.String(10), nullable=False)  # Unidade de medida (g, ml, un)
    preco = db.Column(db.Float, nullable=False)  # Preço unitário em reais

# Tabela de associação entre Receita e Ingredientes usados com suas quantidades
class IngredienteReceita(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID único
    receita_id = db.Column(db.Integer, db.ForeignKey('receita.id'))  # ID da receita
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingrediente.id'))  # ID do ingrediente
    quantidade_usada = db.Column(db.Float, nullable=False)  # Quantidade usada na receita

    ingrediente = db.relationship('Ingrediente')  # Acesso ao objeto Ingrediente

# Modelo da Receita
class Receita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

    ingredientes_usados = db.relationship('IngredienteReceita', backref='receita', lazy=True)

# Rota principal para mostrar todos os ingredientes
@app.route('/')
def home():
    ingredientes = Ingrediente.query.all()
    return render_template('index.html', ingredientes=ingredientes)

# Rota para cadastrar novos ingredientes
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = float(request.form['quantidade'])
        unidade = request.form['unidade']
        preco = float(request.form['preco'])

        novo_ingrediente = Ingrediente(
            nome=nome,
            quantidade=quantidade,
            unidade=unidade,
            preco=preco
        )

        db.session.add(novo_ingrediente)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('cadastro.html')

@app.route('/receitas')
def ver_receitas():
    receitas = Receita.query.all()
    receitas_com_custos = []

    for receita in receitas:
        custo_total = 0
        ingredientes_usados = IngredienteReceita.query.filter_by(receita_id=receita.id).all()
        for ing_rec in ingredientes_usados:
            custo_total += ing_rec.quantidade_usada * ing_rec.ingrediente.preco

        receitas_com_custos.append({
            'nome': receita.nome,
            'custo_total': custo_total,
            'id': receita.id
        })

    return render_template('receitas.html', receitas=receitas_com_custos)

@app.route('/cadastrar_receita', methods=['GET', 'POST'])
def cadastrar_receita():
    if request.method == 'POST':
        nome_receita = request.form['nome']
        nova_receita = Receita(nome=nome_receita)
        db.session.add(nova_receita)
        db.session.commit()

        ingredientes = Ingrediente.query.all()
        custo_total = 0

        for ing in ingredientes:
            if f'ingrediente_{ing.id}' in request.form:
                qtd = float(request.form.get(f'quantidade_{ing.id}', 0))
                if qtd > 0:
                    custo_ingrediente = qtd * ing.preco
                    custo_total += custo_ingrediente

                    ing_rec = IngredienteReceita(
                        receita_id=nova_receita.id,
                        ingrediente_id=ing.id,
                        quantidade_usada=qtd
                    )
                    db.session.add(ing_rec)

        db.session.commit()
        return redirect(url_for('ver_receitas'))

    ingredientes = Ingrediente.query.all()
    return render_template('cadastrar_receita.html', ingredientes=ingredientes)

@app.route('/editar_receita/<int:receita_id>', methods=['GET', 'POST'])
def editar_receita(receita_id):
    receita = Receita.query.get_or_404(receita_id)
    ingredientes = Ingrediente.query.all()
    ingredientes_usados = {ing_rec.ingrediente_id: ing_rec.quantidade_usada for ing_rec in receita.ingredientes_usados}

    if request.method == 'POST':
        receita.nome = request.form['nome']
        db.session.commit()

        IngredienteReceita.query.filter_by(receita_id=receita.id).delete()
        db.session.commit()

        for ing in ingredientes:
            if f'ingrediente_{ing.id}' in request.form:
                qtd = float(request.form.get(f'quantidade_{ing.id}', 0))
                if qtd > 0:
                    ing_rec = IngredienteReceita(
                        receita_id=receita.id,
                        ingrediente_id=ing.id,
                        quantidade_usada=qtd
                    )
                    db.session.add(ing_rec)

        db.session.commit()
        return redirect(url_for('ver_receitas'))

    return render_template('editar_receita.html', receita=receita, ingredientes=ingredientes, ingredientes_usados=ingredientes_usados)

@app.route('/editar_ingrediente/<int:ingrediente_id>', methods=['GET', 'POST'])
def editar_ingrediente(ingrediente_id):
    ingrediente = Ingrediente.query.get_or_404(ingrediente_id)

    if request.method == 'POST':
        ingrediente.nome = request.form['nome']
        ingrediente.quantidade = float(request.form['quantidade'])
        ingrediente.unidade = request.form['unidade']
        ingrediente.preco = float(request.form['preco'])
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('editar_ingrediente.html', ingrediente=ingrediente)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)