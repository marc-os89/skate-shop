import sqlite3

conexao = sqlite3.connect("skateshop.db")
conexao.row_factory = sqlite3.Row

cursor = conexao.execute("SELECT * FROM produtos")
for linha in cursor.fetchall():
    print(dict(linha))

conexao.close()
