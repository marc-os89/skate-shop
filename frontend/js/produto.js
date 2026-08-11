/*
 * produto.js
 * ----------
 * Lê o "id" da URL (?id=5), busca aquele produto na API
 * e monta a página de detalhe dinamicamente.
 *
 * Conceito pra explicar: URLSearchParams é uma forma nativa do JS
 * de ler parâmetros de query string sem fazer parsing manual.
 */

async function carregarProduto() {
  const parametros = new URLSearchParams(window.location.search);
  const produtoId = parametros.get("id");
  const container = document.getElementById("conteudo-produto");

  if (!produtoId) {
    container.innerHTML = "<p>Produto não especificado.</p>";
    return;
  }

  try {
    const { produto } = await api(`/produtos/${produtoId}`);

    container.innerHTML = `
      <div class="card-produto__capa" style="background:${produto.cor}20; border-radius: var(--raio-deck); font-size:8rem; aspect-ratio:1;">
        ${produto.icone}
      </div>
      <div>
        <span class="sticker">${produto.categoria === "roupa" ? "Vestuário" : "Equipamento"}</span>
        <h1 style="font-size:2.2rem; margin-block:16px 8px;">${produto.nome}</h1>
        <p class="texto-suave" style="margin-bottom:20px;">${produto.descricao}</p>
        <p class="mono" style="font-size:2rem; margin-bottom:8px;">${formatarPreco(produto.preco)}</p>
        <p class="texto-suave" style="margin-bottom:24px;">
          ${produto.estoque > 0 ? `${produto.estoque} em estoque` : "Fora de estoque"}
        </p>

        <div style="display:flex; align-items:center; gap:16px;">
          <div class="controle-quantidade">
            <button type="button" id="btn-diminuir">−</button>
            <span id="valor-quantidade">1</span>
            <button type="button" id="btn-aumentar">+</button>
          </div>
          <button class="botao botao-primario" id="btn-adicionar-detalhe" ${produto.estoque === 0 ? "disabled" : ""}>
            Adicionar ao carrinho
          </button>
        </div>
        <p id="mensagem-detalhe" class="texto-suave" style="margin-top:12px;"></p>
      </div>
    `;

    let quantidade = 1;
    const valorQuantidade = document.getElementById("valor-quantidade");

    document.getElementById("btn-aumentar").addEventListener("click", () => {
      quantidade = Math.min(quantidade + 1, produto.estoque);
      valorQuantidade.textContent = quantidade;
    });

    document.getElementById("btn-diminuir").addEventListener("click", () => {
      quantidade = Math.max(quantidade - 1, 1);
      valorQuantidade.textContent = quantidade;
    });

    document.getElementById("btn-adicionar-detalhe").addEventListener("click", async () => {
      const mensagem = document.getElementById("mensagem-detalhe");
      try {
        await api("/carrinho", {
          method: "POST",
          body: JSON.stringify({ produto_id: produto.id, quantidade }),
        });
        mensagem.textContent = "Adicionado ao carrinho ✓";
        atualizarContadorCarrinho();
      } catch (erro) {
        mensagem.textContent = "Erro ao adicionar: " + erro.message;
      }
    });
  } catch (erro) {
    container.innerHTML = `<p>Não foi possível carregar este produto.</p>`;
  }
}

document.addEventListener("DOMContentLoaded", carregarProduto);
