import io
import os
from flask import Flask, jsonify, request, send_file,Response
from main import app, con
from flask_bcrypt import generate_password_hash, check_password_hash
from funcao import *
from fpdf import FPDF
import pygal
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@app.route('/email_enviar', methods=['POST'])
def email_enviar():
    dados = request.get_json()
    assunto = dados.get('assunto')
    mensagem = dados.get('mensagem')
    destinario = dados.get('destinario')

    if not assunto or not mensagem or not destinario:
        return jsonify({'erro': 'Os campos assunto, mensagem e destinario são obrigatórios.'}), 400

    thread = threading.Thread(target=enviando_email, args=(destinario, assunto, mensagem))
    thread.start()

    return jsonify({'mensagem': 'E-mail adicionado à fila de envio com sucesso!'}), 200


@app.route('/grafico')
def grafico():
    try:
        cur = con.cursor()


        cur.execute("""
                    SELECT ano_publicacao, COUNT(*)
                    FROM livro
                    GROUP BY ano_publicacao
                    ORDER BY ano_publicacao
                    """)
        resultado = cur.fetchall()


        grafico_barras = pygal.Bar()
        grafico_barras.title = 'Quantidade de livros por ano de publicação'

        for i in resultado:
            grafico_barras.add(str(i[0]), i[1])

        return Response(grafico_barras.render(), mimetype='image/svg+xml')

    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar o gráfico: {e}'}), 500

    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/livro',methods=['GET'])
def livro():
    try:
        cur = con.cursor()
        cur.execute('select id_livro,titulo,autor,ano_publicacao FROM livro')
        livros = cur.fetchall()

        listar_livro = []
        for livro in livros:
            listar_livro.append({
                'id_livro': livro[0],
                'titulo': livro[1],
                'autor': livro[2],
                'ano_publicacao': livro[3]
            })

        return jsonify(mensagem='lista de livro', livros=listar_livro)

    except Exception as e:
        return jsonify({"message": "Erro ao consultar o banco de dados: {e}"}), 500
    finally:
        cur.close()

@app.route('/criar_livro',methods=['POST'])
def criar_livro():
    try:

        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        ano_publicacao = request.form.get('ano_publicacao')
        imagem = request.files.get('imagem')

        cur = con.cursor()
        cur.execute('SELECT 1 from livro where titulo = ?',(titulo,))
        if cur.fetchone():
            return jsonify({'erro':'Livro ja cadastrado'}), 400
        if not titulo or not autor or not ano_publicacao:
            return jsonify({'erro': 'Os campos titulo, autor e ano_publicacao são obrigatórios.'}), 400

        cur.execute(
            'INSERT INTO livro (titulo, autor, ano_publicacao) VALUES (?, ?, ?) RETURNING id_livro',
            (titulo, autor, ano_publicacao)
        )
        codigo_livro = cur.fetchone()[0]
        con.commit()
        caminho_imagem = None
        if imagem:
            nome_imagem = f'{codigo_livro}.jpg'
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], 'Livros')
            os.makedirs(caminho_imagem_destino, exist_ok=True)
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)
            imagem.save(caminho_imagem)
        return jsonify({
            'mensagem': 'Livro cadastrado com sucesso',
            'livro': {
                'titulo': titulo,
                'autor': autor,
                'ano_publicacao': ano_publicacao
            }
        }), 201

    except Exception as e:
        return jsonify({"message": f"Erro ao consultar o banco de dados: {e}"}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/editar_livro/<int:id>',methods=['PUT'])
def editar_livro(id):
    cur = con.cursor()

    try:
        cur.execute("""SELECT id_livro, titulo, autor, ano_publicacao FROM livro WHERE id_livro = ?""", (id,))
        tem_livro = cur.fetchone()
        if not tem_livro:
            cur.close()
            return jsonify({'erro': 'Livro não encontrado'}), 404


        dados = request.get_json()
        titulo = dados.get('titulo')
        autor = dados.get('autor')
        ano_publicacao = dados.get('ano_publicacao')


        cur.execute("""UPDATE livro SET titulo = ?, autor = ?, ano_publicacao = ? WHERE id_livro = ?""",
                    (titulo, autor, ano_publicacao, id))
        con.commit()

        return jsonify({
            'mensagem': 'Livro atualizado com sucesso',
            'livro': {
                'titulo': titulo,
                'id_livro': id,
                'autor': autor,
                'ano_publicacao': ano_publicacao
            }
        }), 200

    except Exception as e:
        return jsonify({
            'erro': f'Erro ao atualizar o livro: {e}'
        }), 500

    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/deletar_livro/<int:id>',methods=['DELETE'])
def deletar_livro(id):
    cur = con.cursor()

    try:
        cur.execute(
            'SELECT 1 FROM livro WHERE id_livro = ?',
            (id,)
        )

        if not cur.fetchone():
            return jsonify({'erro': 'Livro não encontrado'}), 404

        cur.execute(
            'DELETE FROM livro WHERE id_livro = ?',
            (id,)
        )

        con.commit()

        return jsonify({
            'mensagem': 'Livro deletado com sucesso',
            'id_livro': id
        }), 200

    except Exception as e:
        return jsonify({
            'erro': f'Erro ao deletar o livro: {e}'
        }), 500

    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        cur = con.cursor()
        cur.execute('SELECT id_usuario, nome, email FROM usuario')
        usuarios = cur.fetchall()

        lista = []
        for u in usuarios:
            lista.append({
                'id': u[0],
                'nome': u[1],
                'email': u[2]
            })
        return jsonify(mensagem='Lista de usuários', usuarios=lista)
    except Exception as e:
        return jsonify({"erro": f"Erro no banco: {e}"}), 500
    finally:
        cur.close()

@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    try:
        dados = request.get_json()
        nome = dados.get('nome')
        email = dados.get('email')
        senha_pura = dados.get('senha')


        erro_senha = verificar_senha(senha_pura)
        if erro_senha:
            return jsonify({'erro': erro_senha}), 400


        senha_crip = generate_password_hash(senha_pura)

        cur = con.cursor()

        cur.execute('SELECT 1 FROM usuario WHERE email = ?', (email,))
        if cur.fetchone():
            return jsonify({'erro': 'Email já cadastrado'}), 400

        cur.execute(
            'INSERT INTO usuario (nome, email, senha) VALUES (?, ?, ?)',
            (nome, email, senha_crip)
        )
        con.commit()

        return jsonify({'mensagem': 'Usuário criado com sucesso!'}), 201

    except Exception as e:
        return jsonify({"erro": f"Erro ao criar: {e}"}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/deletar_usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    try:
        cur = con.cursor()
        cur.execute('DELETE FROM usuario WHERE id_usuario = ?', (id,))
        con.commit()
        return jsonify({'mensagem': 'Usuário removido'}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao deletar: {e}"}), 500
    finally:
        cur.close()

@app.route('/login_usuario', methods=['POST'])
def login_usuario():
    try:
        dados = request.get_json()
        email = dados.get('email')
        senha_digitada = dados.get('senha')

        cur = con.cursor()

        cur.execute('SELECT id_usuario, nome, senha FROM usuario WHERE email = ?', (email,))
        usuario = cur.fetchone()

        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404


        senha_hash_banco = usuario[2]


        if check_password_hash(senha_hash_banco, senha_digitada):
            return jsonify({'mensagem': 'Login realizado com sucessooo!',})

        else:
            return jsonify({'erro': 'Senha incorreta'}), 401

    except Exception as e:
        return jsonify({"erro": f"Erro no login: {e}"}), 500
    finally:
            cur.close()

@app.route('/editar_usuario/<int:id>', methods=['PUT'])
def editar_usuario(id):
    cur = con.cursor()

    try:
        cur.execute("SELECT id_usuario FROM usuario WHERE id_usuario = ?", (id,))
        if not cur.fetchone():
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        dados = request.get_json() or {}
        nome = dados.get('nome')
        email = dados.get('email')
        senha_pura = dados.get('senha')


        senha_hash = None
        if senha_pura is not None:
            erro_senha = verificar_senha(senha_pura)
            if erro_senha:
                return jsonify({'erro': erro_senha}), 400
            senha_hash = generate_password_hash(senha_pura)

        if senha_hash is None:
            cur.execute(
                "UPDATE usuario SET nome = ?, email = ? WHERE id_usuario = ?",
                (nome, email, id)
            )
        else:
            cur.execute(
                "UPDATE usuario SET nome = ?, email = ?, senha = ? WHERE id_usuario = ?",
                (nome, email, senha_hash, id)
            )

        con.commit()

        return jsonify({
            'mensagem': 'Usuário editado com sucesso',
            'usuario': {
                'id_usuario': id,
                'nome': nome,
                'email': email
            }
        }), 200

    except Exception as e:
        return jsonify({'erro': f'Erro ao atualizar o usuário: {e}'}), 500
    finally:
        cur.close()


@app.route('/relatorio_livros', methods=['GET'])
def gerar_pdf():
    try:
        cur = con.cursor()
        cur.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livro")
        livros = cur.fetchall()

        pdf = FPDF()
        pdf.add_page()


        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 15, "Relatório de Livros da Biblioteca", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(20, 10, "ID", border=1, align="C")
        pdf.cell(85, 10, "Título", border=1, align="C")
        pdf.cell(60, 10, "Autor", border=1, align="C")
        pdf.cell(25, 10, "Ano", border=1, align="C", ln=True)


        pdf.set_font("Helvetica", "", 10)
        for livro in livros:
            id_livro = str(livro[0])
            titulo = str(livro[1])[:35]
            autor = str(livro[2])[:25]
            ano = str(livro[3])


            pdf.cell(20, 10, id_livro, border=1, align="C")
            pdf.cell(85, 10, titulo, border=1)
            pdf.cell(60, 10, autor, border=1)
            pdf.cell(25, 10, ano, border=1, align="C", ln=True)


        pdf_out = pdf.output(dest='S')

        if isinstance(pdf_out, str):
            pdf_bytes = pdf_out.encode('latin-1')
        else:
            pdf_bytes = bytes(pdf_out)

        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="relatorio_livros.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar o PDF: {e}'}), 500

    finally:
        if 'cur' in locals():
            cur.close()