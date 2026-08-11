# Concreto Skate Shop — projeto de exemplo (System Development)

E-commerce simples de roupas e equipamentos de skate, feito para servir de
exemplo em aula: **HTML + CSS + JavaScript puro** no front-end, **Python
(`http.server`, sem framework)** no back-end, e **SQLite** como banco.

## Como rodar

Requisito: Python 3.10+ instalado (não precisa instalar nada com pip —
tudo aqui usa só a biblioteca padrão).

```bash
cd backend
python server.py
```

Abra **http://localhost:8000** no navegador. O banco (`skateshop.db`) é
criado automaticamente na primeira execução, já com produtos de exemplo.

**Login de administrador de teste:**
- email: `admin@skateshop.com`
- senha: `admin123`

## Estrutura de pastas

```
skate-shop/
├── backend/
│   ├── server.py       ← servidor HTTP + todas as rotas da API
│   └── database.py     ← criação das tabelas e dados de exemplo (seed)
│
└── frontend/
    ├── index.html       ← landing page
    ├── produtos.html    ← catálogo (com filtro de categoria e busca)
    ├── produto.html     ← página de um produto (lida o ?id= da URL)
    ├── carrinho.html    ← carrinho de compras
    ├── login.html / cadastro.html
    ├── admin.html       ← painel administrativo (CRUD de produtos)
    ├── css/style.css    ← toda a estilização do site
    └── js/
        ├── main.js      ← código compartilhado (fetch à API, contador do carrinho...)
        ├── produtos.js  ← renderiza cards de produto (landing + catálogo)
        ├── produto.js   ← página de detalhe de 1 produto
        ├── carrinho.js  ← lógica do carrinho
        ├── auth.js      ← login e cadastro
        └── admin.js     ← CRUD de produtos no painel admin
```

## Conceitos para explorar em aula

- **HTML como estrutura**: cada `.html` é só a "casca" da página. Repare
  que o cabeçalho (`<header>`) se repete em todas as páginas — ótimo
  gancho para falar sobre a falta de componentização no HTML puro
  (e por que frameworks como React resolvem isso depois).
- **CSS com variáveis (`:root`)**: em `style.css`, todo o sistema de cores
  e tipografia fica centralizado em `--variaveis`. Mudar uma cor ali
  muda o site inteiro — bom exemplo de manutenibilidade.
- **JS e o DOM**: `produtos.js` mostra `document.createElement`,
  `innerHTML`, `appendChild` — como o JavaScript "desenha" HTML depois
  que a página já carregou, a partir de dados vindos de uma API.
- **Delegação de eventos**: em vez de um listener por botão, colocamos
  um único listener no container e verificamos o alvo do clique
  (`evento.target.closest(...)`). Vale explicar por quê (elementos criados
  dinamicamente não existiam ainda quando a página carregou).
- **Requisições assíncronas (fetch/async/await)**: `main.js` centraliza
  toda comunicação com o back-end na função `api()`. Bom lugar para
  explicar Promises, `async/await`, e o ciclo requisição → resposta → JSON.
- **HTTP "na unha"**: como não usamos framework nenhum no backend,
  `server.py` mostra literalmente como um servidor decide o que fazer
  com cada verbo HTTP (GET/POST/PUT/DELETE) e cada caminho — ótimo para
  depois comparar com o que o Flask/Django fariam por baixo dos panos.
- **Sessão via cookie**: o carrinho funciona sem login porque cada
  visitante recebe um `token_sessao` (cookie) na primeira visita.
  Bom gancho para explicar a diferença entre autenticação e sessão.
- **SQL na prática**: `database.py` tem o `CREATE TABLE` de cada entidade
  e mostra chaves estrangeiras (`REFERENCES`) entre carrinho e produtos.

## Limitações intencionais (deixe claro para a turma)

Este projeto é **didático**, não pronto para produção:
- Senhas usam SHA-256 + salt simples (produção usaria bcrypt/argon2).
- Sessões ficam em memória (reiniciar o servidor desloga todo mundo).
- Não há HTTPS, nem proteção contra CSRF.
- Não há pagamento real — o "checkout" só registra o pedido no banco.

Esses pontos, inclusive, são ótimos disparadores de discussão sobre
segurança e arquitetura com a turma.
