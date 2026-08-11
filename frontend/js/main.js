/*
 * main.js
 * -------
 * Código compartilhado por TODAS as páginas: fica incluído em todo HTML.
 * Aqui moram:
 *   - api(): função central que conversa com o backend (fetch + JSON)
 *   - atualizarContadorCarrinho(): atualiza o número no ícone do carrinho
 *   - marcarLinkAtivo(): destaca o item de menu da página atual
 *
 * Conceito de DOM pra explicar: document.querySelector busca um elemento
 * no HTML já carregado, e a gente muda seu conteúdo/estilo via JS.
 */

const BASE_API = "/api";

/**
 * Função central de chamadas à API.
 * `credentials: "include"` é o que garante que o cookie de sessão
 * (token_sessao) seja enviado em toda requisição.
 */
async function api(caminho, opcoes = {}) {
  const resposta = await fetch(BASE_API + caminho, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    throw new Error(dados.erro || "Ocorreu um erro na requisição");
  }
  return dados;
}

function formatarPreco(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/** Atualiza a bolinha vermelha com a quantidade de itens no carrinho. */
async function atualizarContadorCarrinho() {
  const elemento = document.querySelector("[data-contador-carrinho]");
  if (!elemento) return;
  try {
    const { itens } = await api("/carrinho");
    const total = itens.reduce((soma, item) => soma + item.quantidade, 0);
    elemento.textContent = total;
    elemento.style.display = total > 0 ? "flex" : "none";
  } catch (erro) {
    console.error("Não foi possível carregar o carrinho:", erro);
  }
}

/** Destaca no menu o link correspondente à página atual. */
function marcarLinkAtivo() {
  const paginaAtual = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-links a[data-pagina]").forEach((link) => {
    if (link.dataset.pagina === paginaAtual) {
      link.style.color = "var(--cor-destaque-2)";
    }
  });
}

/** Mostra/some a área de "Admin" e "Minha conta" no header conforme login. */
async function atualizarAreaUsuario() {
  const areaLogin = document.querySelector("[data-area-nao-logado]");
  const areaLogado = document.querySelector("[data-area-logado]");
  const linkAdmin = document.querySelector("[data-link-admin]");
  const nomeUsuario = document.querySelector("[data-nome-usuario]");
  if (!areaLogin && !areaLogado) return;

  try {
    const { usuario } = await api("/auth/eu");
    if (usuario) {
      if (areaLogin) areaLogin.style.display = "none";
      if (areaLogado) areaLogado.style.display = "flex";
      if (nomeUsuario) nomeUsuario.textContent = usuario.nome.split(" ")[0];
      if (linkAdmin) linkAdmin.style.display = usuario.papel === "admin" ? "inline" : "none";
    } else {
      if (areaLogin) areaLogin.style.display = "flex";
      if (areaLogado) areaLogado.style.display = "none";
    }
  } catch (erro) {
    console.error("Não foi possível verificar login:", erro);
  }
}

function configurarBotaoLogout() {
  const botao = document.querySelector("[data-botao-logout]");
  if (!botao) return;
  botao.addEventListener("click", async () => {
    await api("/auth/logout", { method: "POST" });
    window.location.href = "index.html";
  });
}

// Roda em toda página assim que o HTML termina de carregar.
document.addEventListener("DOMContentLoaded", () => {
  marcarLinkAtivo();
  atualizarContadorCarrinho();
  atualizarAreaUsuario();
  configurarBotaoLogout();
});
