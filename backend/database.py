"""
database.py
------------
Aqui fica TUDO relacionado ao banco de dados SQLite:
- criação das tabelas (schema)
- inserção de dados de exemplo (seed)
- funções auxiliares de conexão

Ideia pedagógica: mostrar pros alunos que o "modelo" da aplicação
(as tabelas) fica separado da lógica do servidor (server.py).
"""

import sqlite3
import hashlib
import secrets
import os

# Caminho do arquivo do banco. Fica ao lado deste script.
CAMINHO_DB = os.path.join(os.path.dirname(__file__), "skateshop.db")


def conectar():
    """
    Abre uma conexão com o banco.
    row_factory = sqlite3.Row faz as linhas se comportarem como
    dicionários (dá pra fazer linha["nome"] em vez de linha[2]).
    """
    conexao = sqlite3.connect(CAMINHO_DB)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def gerar_hash_senha(senha: str, salt: str | None = None):
    """
    Nunca guardamos senha em texto puro no banco!
    Aqui usamos um "salt" (valor aleatório) + SHA-256.
    Isso é uma versão simplificada só para fins didáticos --
    em produção o ideal é usar bcrypt/argon2.
    """
    if salt is None:
        salt = secrets.token_hex(8)
    hash_resultado = hashlib.sha256((salt + senha).encode("utf-8")).hexdigest()
    return hash_resultado, salt


def criar_tabelas(conexao):
    cursor = conexao.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            papel TEXT NOT NULL DEFAULT 'cliente', -- 'cliente' ou 'admin'
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL NOT NULL,
            categoria TEXT NOT NULL,      -- 'roupa' ou 'equipamento'
            estoque INTEGER NOT NULL DEFAULT 0,
            icone TEXT NOT NULL,          -- emoji usado como "imagem" do produto
            cor TEXT NOT NULL,            -- cor de destaque do card (hex)
            destaque INTEGER NOT NULL DEFAULT 0 -- 1 = aparece na landing page
        );

        CREATE TABLE IF NOT EXISTS carrinho_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_sessao TEXT NOT NULL,
            produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
            quantidade INTEGER NOT NULL DEFAULT 1,
            UNIQUE(token_sessao, produto_id)
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER REFERENCES usuarios(id),
            total REAL NOT NULL,
            itens_json TEXT NOT NULL,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conexao.commit()


def popular_dados_exemplo(conexao):
    """Insere produtos e um usuário admin, só se o banco ainda estiver vazio."""
    cursor = conexao.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM produtos")
    if cursor.fetchone()["total"] == 0:
        produtos_exemplo = [
            ("Shape Concreto Selvagem", "Shape 8.0\" maple canadense 7 camadas, gráfico exclusivo.", 289.90, "equipamento", 14, "🛹", "#FF5A1F", 1),
            ("Truck Eixo de Ferro 139mm", "Par de trucks em liga de alumínio, altura média.", 219.90, "equipamento", 20, "⚙️", "#6B6F76", 0),
            ("Rodas Fúria 52mm 99A", "Jogo com 4 rodas de poliuretano, dureza 99A para street.", 129.90, "equipamento", 30, "🎡", "#D4FF3D", 1),
            ("Rolamento Abec 7", "Kit com 8 rolamentos de alta velocidade + espaçadores.", 69.90, "equipamento", 40, "🔩", "#14151A", 0),
            ("Lixa Grip Tape Preta", "Lixa profissional para shape, corte sob medida.", 39.90, "equipamento", 50, "▪️", "#14151A", 0),
            ("Capacete Proteção Urbana", "Capacete certificado, ajuste de aba traseira.", 179.90, "equipamento", 12, "⛑️", "#FF5A1F", 0),
            ("Camiseta Concrete Wave", "100% algodão, estampa serigrafada frente e costas.", 89.90, "roupa", 25, "👕", "#D4FF3D", 1),
            ("Moletom Asphalt Crew", "Moletom canguru, forro flanelado, bolso frontal.", 189.90, "roupa", 18, "🧥", "#6B6F76", 1),
            ("Boné Aba Reta Grip", "Boné 5 painéis com fecho ajustável em couro sintético.", 79.90, "roupa", 22, "🧢", "#14151A", 0),
            ("Tênis Street Low", "Sola vulcanizada, cabedal reforçado na zona de ollie.", 249.90, "roupa", 16, "👟", "#FF5A1F", 1),
            ("Meia Cano Alto Grip", "Kit com 3 pares, reforço no calcanhar.", 34.90, "roupa", 60, "🧦", "#D4FF3D", 0),
            ("Mochila Transporte Deck", "Compartimento lateral para o shape, bolso para notebook.", 159.90, "roupa", 10, "🎒", "#6B6F76", 0),
        ]
        cursor.executemany(
            """INSERT INTO produtos (nome, descricao, preco, categoria, estoque, icone, cor, destaque)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            produtos_exemplo,
        )

    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    if cursor.fetchone()["total"] == 0:
        senha_hash, salt = gerar_hash_senha("admin123")
        cursor.execute(
            """INSERT INTO usuarios (nome, email, senha_hash, salt, papel)
               VALUES (?, ?, ?, ?, ?)""",
            ("Administrador da Loja", "admin@skateshop.com", senha_hash, salt, "admin"),
        )

    conexao.commit()


def inicializar_banco():
    """Função chamada pelo server.py na inicialização do sistema."""
    conexao = conectar()
    criar_tabelas(conexao)
    popular_dados_exemplo(conexao)
    conexao.close()
    print(f"[banco] pronto em: {CAMINHO_DB}")


if __name__ == "__main__":
    # Permite rodar "python database.py" isoladamente para recriar o banco
    inicializar_banco()
