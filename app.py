import hashlib
from flask import Flask, flash, render_template, request, redirect, session, url_for
import pymysql

# Configuração do Flask
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Mude para uma chave secreta segura

# Configuração de conexão com MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'gtr3253',
    'db': 'estoque_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Função para conectar ao banco de dados
def get_db_connection():
    return pymysql.connect(**db_config)

# Rota para a página de login
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hashing da senha
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM usuarios WHERE username = %s AND password = %s', (username, hashed_password))
            user = cursor.fetchone()

        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('index'))  # Redireciona para a página inicial, independentemente de ser admin
        else:
            flash('Login inválido! Verifique seu usuário e senha.')
    
    return render_template('login.html')


app.secret_key = 'gtr3253'  # Altere para uma chave segura


# Rota para a página de logout
@app.route('/logout')
def logout():
    session.clear()  # Limpa todos os dados da sessão
    return redirect(url_for('login'))  # Redireciona para a página de login

# Rota para exibir o estoque
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM produtos')
        produtos = cursor.fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

# Rota para adicionar produto (com verificação de admin)
@app.route('/adicionar', methods=('GET', 'POST'))
def adicionar_produto():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = int(request.form['quantidade'])
        preco = float(request.form['preco'])

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM produtos WHERE nome = %s', (nome,))
            produto = cursor.fetchone()

            if produto:
                nova_quantidade = produto['quantidade'] + quantidade
                cursor.execute('UPDATE produtos SET quantidade = %s WHERE nome = %s', (nova_quantidade, nome))
            else:
                cursor.execute('INSERT INTO produtos (nome, quantidade, preco) VALUES (%s, %s, %s)', (nome, quantidade, preco))

        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('adicionar.html')

    return render_template('adicionar.html')

# Rota para criar novos usuários (acesso somente para admin)
@app.route('/criar_usuario', methods=('GET', 'POST'))
def criar_usuario():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM usuarios WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

    if not user or not user['is_admin']:
        return "Acesso negado!", 403  # Apenas admin pode acessar esta rota

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin', 'off') == 'on'  # Verifica se o checkbox está marcado

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO usuarios (username, password, is_admin) VALUES (%s, %s, %s)', (username, hashed_password, is_admin))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('criar_usuario.html')

# Rota para remover produto
@app.route('/remover/<int:id>')
def remover_produto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Verifica se o usuário é um admin
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM usuarios WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

    if not user or not user['is_admin']:
        return "Acesso negado!", 403  # Apenas admin pode acessar esta rota

    # Se o usuário for admin, prossegue com a remoção
    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM produtos WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Rota para atualizar quantidade do produto
@app.route('/atualizar/<int:id>', methods=('GET', 'POST'))
def atualizar_produto(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM produtos WHERE id = %s', (id,))
        produto = cursor.fetchone()

    if request.method == 'POST':
        quantidade = int(request.form['quantidade'])

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('UPDATE produtos SET quantidade = %s WHERE id = %s', (quantidade, id))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    conn.close()
    return render_template('atualizar.html', produto=produto)

# Executar o servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
