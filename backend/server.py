"""
server.py
---------
Servidor HTTP escrito com a biblioteca padrão do Python (http.server),
sem nenhum framework (nada de Flask/Django). A ideia é mostrar pros
alunos, na "unha", como um servidor web funciona por baixo dos panos:

1. Ele "escuta" uma porta (8000)
2. Para cada requisição, olha o MÉTODO (GET/POST/PUT/DELETE) e o CAMINHO
3. Decide se é um arquivo estático (HTML/CSS/JS) ou uma rota de API (/api/...)
4. Para rotas de API, conversa com o banco (database.py) e responde em JSON

Como rodar:
    cd backend
    python server.py
Depois abra http://localhost:8000 no navegador.
"""

import json
import mimetypes
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs

import database

PORTA = 8000
PASTA_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Sessões em memória: { token_sessao: usuario_id_ou_None }
# Simplificado de propósito para fins didáticos. Em produção isso
# ficaria em algo persistente (banco, Redis, etc), pois reinicia
# do zero toda vez que o servidor é reiniciado.
SESSOES_LOGADAS = {}


# ---------------------------------------------------------------------------
# Handler principal: cada requisição HTTP vira uma instância desta classe
# ---------------------------------------------------------------------------
class SkateShopHandler(BaseHTTPRequestHandler):

    # ---- utilidades gerais -------------------------------------------------

    def log_message(self, formato, *args):
        # Deixa o log do terminal mais enxuto/didático
        print(f"[{self.command}] {self.path} -> {args[1] if len(args) > 1 else ''}")

    def enviar_json(self, status: int, dados, cookie: SimpleCookie | None = None):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        if cookie:
            for morsel in cookie.values():
                self.send_header("Set-Cookie", morsel.OutputString())
        self.end_headers()
        self.wfile.write(corpo)

    def ler_corpo_json(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        if tamanho == 0:
            return {}
        bruto = self.rfile.read(tamanho)
        try:
            return json.loads(bruto.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def obter_token_sessao(self):
        """
        Lê o cookie 'token_sessao'. Se o visitante ainda não tem um,
        cria um novo token aleatório -- assim o carrinho funciona mesmo
        para quem não está logado.
        """
        cookies = SimpleCookie(self.headers.get("Cookie"))
        if "token_sessao" in cookies:
            return cookies["token_sessao"].value, None

        novo_token = secrets.token_hex(16)
        cookie_saida = SimpleCookie()
        cookie_saida["token_sessao"] = novo_token
        cookie_saida["token_sessao"]["path"] = "/"
        cookie_saida["token_sessao"]["httponly"] = True
        return novo_token, cookie_saida

    def obter_usuario_logado(self, conexao, token_sessao):
        usuario_id = SESSOES_LOGADAS.get(token_sessao)
        if not usuario_id:
            return None
        linha = conexao.execute(
            "SELECT id, nome, email, papel FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return dict(linha) if linha else None

    # ---- roteamento ----------------------------------------------------

    def do_GET(self):
        caminho = urlparse(self.path).path
        if caminho.startswith("/api/"):
            self.rotear_api("GET", caminho)
        else:
            self.servir_arquivo_estatico(caminho)

    def do_POST(self):
        self.rotear_api("POST", urlparse(self.path).path)

    def do_PUT(self):
        self.rotear_api("PUT", urlparse(self.path).path)

    def do_DELETE(self):
        self.rotear_api("DELETE", urlparse(self.path).path)

    # ---- arquivos estáticos (HTML/CSS/JS) -------------------------------

    def servir_arquivo_estatico(self, caminho):
        if caminho == "/":
            caminho = "/index.html"

        # Impede "path traversal" (ex: /../../etc/passwd)
        caminho_relativo = caminho.lstrip("/")
        caminho_absoluto = os.path.normpath(os.path.join(PASTA_FRONTEND, caminho_relativo))
        if not caminho_absoluto.startswith(os.path.normpath(PASTA_FRONTEND)):
            self.send_error(403, "Acesso negado")
            return

        if not os.path.isfile(caminho_absoluto):
            self.send_error(404, "Arquivo não encontrado")
            return

        tipo_conteudo, _ = mimetypes.guess_type(caminho_absoluto)
        with open(caminho_absoluto, "rb") as arquivo:
            conteudo = arquivo.read()

        self.send_response(200)
        self.send_header("Content-Type", tipo_conteudo or "application/octet-stream")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    # ---- roteador de API -------------------------------------------------

    def rotear_api(self, metodo, caminho):
        token_sessao, cookie_novo = self.obter_token_sessao()
        conexao = database.conectar()
        try:
            usuario = self.obter_usuario_logado(conexao, token_sessao)

            # --- Produtos ---
            if metodo == "GET" and caminho == "/api/produtos":
                return self.listar_produtos(conexao, cookie_novo)

            m = re.fullmatch(r"/api/produtos/(\d+)", caminho)
            if m and metodo == "GET":
                return self.obter_produto(conexao, int(m.group(1)), cookie_novo)
            if metodo == "POST" and caminho == "/api/produtos":
                return self.criar_produto(conexao, usuario, cookie_novo)
            if m and metodo == "PUT":
                return self.atualizar_produto(conexao, int(m.group(1)), usuario, cookie_novo)
            if m and metodo == "DELETE":
                return self.remover_produto(conexao, int(m.group(1)), usuario, cookie_novo)

            # --- Autenticação ---
            if metodo == "POST" and caminho == "/api/auth/cadastro":
                return self.cadastrar_usuario(conexao, token_sessao, cookie_novo)
            if metodo == "POST" and caminho == "/api/auth/login":
                return self.login(conexao, token_sessao, cookie_novo)
            if metodo == "POST" and caminho == "/api/auth/logout":
                return self.logout(token_sessao, cookie_novo)
            if metodo == "GET" and caminho == "/api/auth/eu":
                return self.enviar_json(200, {"usuario": usuario}, cookie_novo)

            # --- Carrinho ---
            if metodo == "GET" and caminho == "/api/carrinho":
                return self.ver_carrinho(conexao, token_sessao, cookie_novo)
            if metodo == "POST" and caminho == "/api/carrinho":
                return self.adicionar_ao_carrinho(conexao, token_sessao, cookie_novo)

            m = re.fullmatch(r"/api/carrinho/(\d+)", caminho)
            if m and metodo == "PUT":
                return self.atualizar_item_carrinho(conexao, token_sessao, int(m.group(1)), cookie_novo)
            if m and metodo == "DELETE":
                return self.remover_item_carrinho(conexao, token_sessao, int(m.group(1)), cookie_novo)

            # --- Pedido / checkout ---
            if metodo == "POST" and caminho == "/api/pedido":
                return self.finalizar_pedido(conexao, token_sessao, usuario, cookie_novo)

            self.enviar_json(404, {"erro": "Rota não encontrada"})
        finally:
            conexao.close()

    # ---- handlers: produtos ----------------------------------------------

    def listar_produtos(self, conexao, cookie):
        parametros = parse_qs(urlparse(self.path).query)
        categoria = parametros.get("categoria", [None])[0]
        busca = parametros.get("busca", [None])[0]
        apenas_destaque = parametros.get("destaque", [None])[0]

        sql = "SELECT * FROM produtos WHERE 1=1"
        args = []
        if categoria:
            sql += " AND categoria = ?"
            args.append(categoria)
        if busca:
            sql += " AND (nome LIKE ? OR descricao LIKE ?)"
            args += [f"%{busca}%", f"%{busca}%"]
        if apenas_destaque == "1":
            sql += " AND destaque = 1"
        sql += " ORDER BY id"

        linhas = conexao.execute(sql, args).fetchall()
        self.enviar_json(200, {"produtos": [dict(linha) for linha in linhas]}, cookie)

    def obter_produto(self, conexao, produto_id, cookie):
        linha = conexao.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not linha:
            return self.enviar_json(404, {"erro": "Produto não encontrado"}, cookie)
        self.enviar_json(200, {"produto": dict(linha)}, cookie)

    def _exigir_admin(self, usuario, cookie):
        if not usuario or usuario["papel"] != "admin":
            self.enviar_json(403, {"erro": "Apenas administradores podem fazer isso"}, cookie)
            return False
        return True

    def criar_produto(self, conexao, usuario, cookie):
        if not self._exigir_admin(usuario, cookie):
            return
        dados = self.ler_corpo_json()
        campos_obrigatorios = ["nome", "descricao", "preco", "categoria", "estoque", "icone", "cor"]
        if not all(campo in dados for campo in campos_obrigatorios):
            return self.enviar_json(400, {"erro": "Campos obrigatórios faltando"}, cookie)

        cursor = conexao.execute(
            """INSERT INTO produtos (nome, descricao, preco, categoria, estoque, icone, cor, destaque)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                dados["nome"], dados["descricao"], float(dados["preco"]), dados["categoria"],
                int(dados["estoque"]), dados["icone"], dados["cor"], int(dados.get("destaque", 0)),
            ),
        )
        conexao.commit()
        self.enviar_json(201, {"id": cursor.lastrowid}, cookie)

    def atualizar_produto(self, conexao, produto_id, usuario, cookie):
        if not self._exigir_admin(usuario, cookie):
            return
        dados = self.ler_corpo_json()
        existente = conexao.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not existente:
            return self.enviar_json(404, {"erro": "Produto não encontrado"}, cookie)

        atualizado = {**dict(existente), **dados}
        conexao.execute(
            """UPDATE produtos SET nome=?, descricao=?, preco=?, categoria=?,
               estoque=?, icone=?, cor=?, destaque=? WHERE id=?""",
            (
                atualizado["nome"], atualizado["descricao"], float(atualizado["preco"]),
                atualizado["categoria"], int(atualizado["estoque"]), atualizado["icone"],
                atualizado["cor"], int(atualizado["destaque"]), produto_id,
            ),
        )
        conexao.commit()
        self.enviar_json(200, {"ok": True}, cookie)

    def remover_produto(self, conexao, produto_id, usuario, cookie):
        if not self._exigir_admin(usuario, cookie):
            return
        conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conexao.commit()
        self.enviar_json(200, {"ok": True}, cookie)

    # ---- handlers: autenticação --------------------------------------

    def cadastrar_usuario(self, conexao, token_sessao, cookie):
        dados = self.ler_corpo_json()
        nome, email, senha = dados.get("nome"), dados.get("email"), dados.get("senha")
        if not nome or not email or not senha:
            return self.enviar_json(400, {"erro": "Preencha nome, email e senha"}, cookie)

        ja_existe = conexao.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        if ja_existe:
            return self.enviar_json(409, {"erro": "Já existe uma conta com esse email"}, cookie)

        senha_hash, salt = database.gerar_hash_senha(senha)
        cursor = conexao.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, salt, papel) VALUES (?, ?, ?, ?, 'cliente')",
            (nome, email, senha_hash, salt),
        )
        conexao.commit()
        SESSOES_LOGADAS[token_sessao] = cursor.lastrowid
        self.enviar_json(201, {"ok": True}, cookie)

    def login(self, conexao, token_sessao, cookie):
        dados = self.ler_corpo_json()
        email, senha = dados.get("email"), dados.get("senha")
        linha = conexao.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        if not linha:
            return self.enviar_json(401, {"erro": "Email ou senha inválidos"}, cookie)

        hash_calculado, _ = database.gerar_hash_senha(senha, linha["salt"])
        if hash_calculado != linha["senha_hash"]:
            return self.enviar_json(401, {"erro": "Email ou senha inválidos"}, cookie)

        SESSOES_LOGADAS[token_sessao] = linha["id"]
        self.enviar_json(200, {"usuario": {"id": linha["id"], "nome": linha["nome"], "papel": linha["papel"]}}, cookie)

    def logout(self, token_sessao, cookie):
        SESSOES_LOGADAS.pop(token_sessao, None)
        self.enviar_json(200, {"ok": True}, cookie)

    # ---- handlers: carrinho --------------------------------------------

    def ver_carrinho(self, conexao, token_sessao, cookie):
        linhas = conexao.execute(
            """SELECT ci.produto_id, ci.quantidade, p.nome, p.preco, p.icone, p.cor
               FROM carrinho_itens ci JOIN produtos p ON p.id = ci.produto_id
               WHERE ci.token_sessao = ?""",
            (token_sessao,),
        ).fetchall()
        itens = [dict(linha) for linha in linhas]
        total = sum(item["preco"] * item["quantidade"] for item in itens)
        self.enviar_json(200, {"itens": itens, "total": round(total, 2)}, cookie)

    def adicionar_ao_carrinho(self, conexao, token_sessao, cookie):
        dados = self.ler_corpo_json()
        produto_id = dados.get("produto_id")
        quantidade = int(dados.get("quantidade", 1))

        produto = conexao.execute("SELECT id FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not produto:
            return self.enviar_json(404, {"erro": "Produto não encontrado"}, cookie)

        existente = conexao.execute(
            "SELECT id, quantidade FROM carrinho_itens WHERE token_sessao=? AND produto_id=?",
            (token_sessao, produto_id),
        ).fetchone()
        if existente:
            conexao.execute(
                "UPDATE carrinho_itens SET quantidade = ? WHERE id = ?",
                (existente["quantidade"] + quantidade, existente["id"]),
            )
        else:
            conexao.execute(
                "INSERT INTO carrinho_itens (token_sessao, produto_id, quantidade) VALUES (?, ?, ?)",
                (token_sessao, produto_id, quantidade),
            )
        conexao.commit()
        self.enviar_json(201, {"ok": True}, cookie)

    def atualizar_item_carrinho(self, conexao, token_sessao, produto_id, cookie):
        dados = self.ler_corpo_json()
        quantidade = int(dados.get("quantidade", 1))
        if quantidade <= 0:
            conexao.execute(
                "DELETE FROM carrinho_itens WHERE token_sessao=? AND produto_id=?",
                (token_sessao, produto_id),
            )
        else:
            conexao.execute(
                "UPDATE carrinho_itens SET quantidade=? WHERE token_sessao=? AND produto_id=?",
                (quantidade, token_sessao, produto_id),
            )
        conexao.commit()
        self.enviar_json(200, {"ok": True}, cookie)

    def remover_item_carrinho(self, conexao, token_sessao, produto_id, cookie):
        conexao.execute(
            "DELETE FROM carrinho_itens WHERE token_sessao=? AND produto_id=?",
            (token_sessao, produto_id),
        )
        conexao.commit()
        self.enviar_json(200, {"ok": True}, cookie)

    # ---- handler: fechar pedido -----------------------------------------

    def finalizar_pedido(self, conexao, token_sessao, usuario, cookie):
        linhas = conexao.execute(
            """SELECT ci.produto_id, ci.quantidade, p.nome, p.preco
               FROM carrinho_itens ci JOIN produtos p ON p.id = ci.produto_id
               WHERE ci.token_sessao = ?""",
            (token_sessao,),
        ).fetchall()
        if not linhas:
            return self.enviar_json(400, {"erro": "Carrinho vazio"}, cookie)

        itens = [dict(linha) for linha in linhas]
        total = sum(item["preco"] * item["quantidade"] for item in itens)
        usuario_id = usuario["id"] if usuario else None

        cursor = conexao.execute(
            "INSERT INTO pedidos (usuario_id, total, itens_json) VALUES (?, ?, ?)",
            (usuario_id, total, json.dumps(itens, ensure_ascii=False)),
        )
        conexao.execute("DELETE FROM carrinho_itens WHERE token_sessao = ?", (token_sessao,))
        conexao.commit()
        self.enviar_json(201, {"pedido_id": cursor.lastrowid, "total": round(total, 2)}, cookie)


def iniciar_servidor():
    database.inicializar_banco()
    servidor = ThreadingHTTPServer(("0.0.0.0", PORTA), SkateShopHandler)
    print(f"Servidor rodando em http://localhost:{PORTA}")
    print("Login admin de teste -> email: admin@skateshop.com | senha: admin123")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        servidor.shutdown()


if __name__ == "__main__":
    iniciar_servidor()
