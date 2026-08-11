/*
 * produtos.js
 * -----------
 * Responsável por buscar produtos na API e "desenhar" os cards no DOM.
 * Esse arquivo é usado em DUAS páginas:
 *   - index.html   -> mostra só os produtos em destaque (#grade-destaques)
 *   - produtos.html -> catálogo completo com filtros (#grade-produtos)
 *
 * Conceito de DOM pra explicar: criamos elementos com document.createElement,
 * setamos seu conteúdo/atributos, e "encaixamos" no HTML com appendChild.
 */

/** Constrói o HTML (como string) de UM card de produto. */
function criarCardProduto(produto) {
  const card = document.createElement("article");
  card.className = "card-produto";
  card.innerHTML = `
    <a href="produto.html?id=${produto.id}" style="color:inherit;">
      <div class="card-produto__capa" style="background:${produto.cor}20;">
        <span>${produto.icone}</span>
      </div>
    </a>
    <div class="card-produto__corpo">
      <span class="texto-suave" style="font-size:0.75rem; text-transform:uppercase;">${produto.categoria}</span>
      <h3><a href="produto.html?id=${produto.id}" style="color:inherit;">${produto.nome}</a></h3>
      <div class="card-produto__rodape">
        <span class="card-produto__preco">${formatarPreco(produto.preco)}</span>
        <button class="botao botao-primario botao-pequeno" data-adicionar="${produto.id}">+ Carrinho</button>
      </div>
    </div>
  `;
  return card;
}

/** Renderiza uma lista de produtos dentro de um container (por id). */
function renderizarProdutos(idContainer, produtos) {
  const container = document.getElementById(idContainer);
  if (!container) return;

  container.innerHTML = "";
  if (produtos.length === 0) {
    container.innerHTML = `
      <div class="estado-vazio" style="grid-column: 1 / -1;">
        <h3>Nenhum produto encontrado</h3>
        <p>Tente outra busca ou categoria.</p>
      </div>`;
    return;
  }

  produtos.forEach((produto) => container.appendChild(criarCardProduto(produto)));

  // Delegação de evento: um único listener no container cuida de todos os botões.
  container.addEventListener("click", async (evento) => {
    const botao = evento.target.closest("[data-adicionar]");
    if (!botao) return;
    evento.preventDefault();
    const produtoId = Number(botao.dataset.adicionar);
    botao.textContent = "Adicionando...";
    try {
      await api("/carrinho", {
        method: "POST",
        body: JSON.stringify({ produto_id: produtoId, quantidade: 1 }),
      });
      botao.textContent = "Adicionado ✓";
      atualizarContadorCarrinho();
      setTimeout(() => (botao.textContent = "+ Carrinho"), 1200);
    } catch (erro) {
      botao.textContent = "Erro, tente de novo";
    }
  });
}

/** Carrega e mostra os produtos em destaque (usado na landing page). */
async function carregarDestaques() {
  try {
    const { produtos } = await api("/produtos?destaque=1");
    renderizarProdutos("grade-destaques", produtos);
  } catch (erro) {
    console.error(erro);
  }
}

/** Lógica completa da página de catálogo: filtros de categoria + busca. */
async function iniciarCatalogo() {
  const containerFiltros = document.getElementById("filtros-categoria");
  const campoBusca = document.getElementById("campo-busca");
  const parametrosURL = new URLSearchParams(window.location.search);
  let categoriaAtual = parametrosURL.get("categoria") || "";

  async function recarregar() {
    const consulta = new URLSearchParams();
    if (categoriaAtual) consulta.set("categoria", categoriaAtual);
    if (campoBusca && campoBusca.value.trim()) consulta.set("busca", campoBusca.value.trim());

    const { produtos } = await api(`/produtos?${consulta.toString()}`);
    renderizarProdutos("grade-produtos", produtos);

    // Atualiza qual botão de filtro está "ativo" visualmente
    document.querySelectorAll(".filtro").forEach((botao) => {
      botao.classList.toggle("ativo", botao.dataset.categoria === categoriaAtual);
    });
  }

  if (containerFiltros) {
    containerFiltros.addEventListener("click", (evento) => {
      const botao = evento.target.closest(".filtro");
      if (!botao) return;
      categoriaAtual = botao.dataset.categoria;
      recarregar();
    });
  }

  if (campoBusca) {
    let temporizador;
    campoBusca.addEventListener("input", () => {
      clearTimeout(temporizador);
      temporizador = setTimeout(recarregar, 300); // "debounce" simples
    });
  }

  recarregar();
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("grade-destaques")) carregarDestaques();
  if (document.getElementById("grade-produtos")) iniciarCatalogo();
});
