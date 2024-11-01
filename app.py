import hashlib
from flask import Flask, flash, render_template, request, redirect, session, url_for
import pymysql

# Configuração do Flask
app = Flask(__name__)
app.secret_key = 'gtr3253' 

# Configuração do banco MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'gtr3253',
    'db': 'estoque_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Conecta ao banco de dados
def conectar_banco():
    return pymysql.connect(**db_config)

# Página de login
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']
        
        # Cria um hash da senha
        senha_hashed = hashlib.sha256(senha.encode()).hexdigest()

        conn = conectar_banco()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM usuarios WHERE username = %s AND password = %s', (usuario, senha_hashed))
            usuario_encontrado = cursor.fetchone()

        conn.close()

        if usuario_encontrado:
            # Salva informações do usuário na sessão
            session['user_id'] = usuario_encontrado['id']
            session['username'] = usuario_encontrado['username']
            session['is_admin'] = usuario_encontrado['is_admin']
            return redirect(url_for('index'))
        else:
            flash('Login inválido! Verifique seu usuário e senha.')
    
    return render_template('login.html')

# Página de logout
@app.route('/logout')
def logout():
    session.clear()  # Limpa a sessão
    return redirect(url_for('login'))

# Página principal que exibe o estoque
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = conectar_banco()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM produtos')
        produtos = cursor.fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

# Adicionar produto
@app.route('/adicionar', methods=('GET', 'POST'))
def adicionar_produto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = int(request.form['quantidade'])
        preco = float(request.form['preco'])

        conn = conectar_banco()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM produtos WHERE nome = %s', (nome,))
            produto_encontrado = cursor.fetchone()

            if produto_encontrado:
                nova_quantidade = produto_encontrado['quantidade'] + quantidade
                cursor.execute('UPDATE produtos SET quantidade = %s WHERE nome = %s', (nova_quantidade, nome))
            else:
                cursor.execute('INSERT INTO produtos (nome, quantidade, preco) VALUES (%s, %s, %s)', (nome, quantidade, preco))

        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('adicionar.html')

# Criar usuário (somente para admin)
@app.route('/criar_usuario', methods=('GET', 'POST'))
def criar_usuario():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = conectar_banco()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM usuarios WHERE id = %s', (session['user_id'],))
        usuario_atual = cursor.fetchone()

    if not usuario_atual or not usuario_atual['is_admin']:
        return "Acesso negado!", 403

    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']
        is_admin = request.form.get('is_admin', 'off') == 'on'
        
        senha_hashed = hashlib.sha256(senha.encode()).hexdigest()

        conn = conectar_banco()
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO usuarios (username, password, is_admin) VALUES (%s, %s, %s)', (usuario, senha_hashed, is_admin))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('criar_usuario.html')

# Remover produto
@app.route('/remover/<int:id>')
def remover_produto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = conectar_banco()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM usuarios WHERE id = %s', (session['user_id'],))
        usuario_atual = cursor.fetchone()

    if not usuario_atual or not usuario_atual['is_admin']:
        return "Acesso negado!", 403  

    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM produtos WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Atualizar quantidade do produto
@app.route('/atualizar/<int:id>', methods=('GET', 'POST'))
def atualizar_produto(id):
    conn = conectar_banco()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM produtos WHERE id = %s', (id,))
        produto = cursor.fetchone()

    if request.method == 'POST':
        quantidade = int(request.form['quantidade'])

        conn = conectar_banco()
        with conn.cursor() as cursor:
            cursor.execute('UPDATE produtos SET quantidade = %s WHERE id = %s', (quantidade, id))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    conn.close()
    return render_template('atualizar.html', produto=produto)

# Rodar o servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
