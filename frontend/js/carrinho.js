/*
 * carrinho.js
 * -----------
 * Busca os itens do carrinho na API, desenha cada linha e cuida de:
 *   - aumentar/diminuir quantidade
 *   - remover item
 *   - finalizar pedido (checkout)
 */

async function carregarCarrinho() {
  const container = document.getElementById("lista-carrinho");
  const areaTotal = document.getElementById("area-total");

  const { itens, total } = await api("/carrinho");

  if (itens.length === 0) {
    container.innerHTML = `
      <div class="estado-vazio">
        <h3>Seu carrinho está vazio</h3>
        <p>Que tal dar uma olhada no <a href="produtos.html" style="color:var(--cor-destaque);">catálogo</a>?</p>
      </div>`;
    areaTotal.innerHTML = "";
    return;
  }

  container.innerHTML = itens
    .map(
      (item) => `
    <div class="linha-carrinho" data-linha="${item.produto_id}">
      <div class="card-produto__capa" style="background:${item.cor}20; border-radius: var(--raio-padrao); font-size:1.6rem;">
        ${item.icone}
      </div>
      <div>
        <strong>${item.nome}</strong>
        <p class="texto-suave mono">${formatarPreco(item.preco)} / un.</p>
      </div>
      <div class="controle-quantidade">
        <button type="button" data-diminuir="${item.produto_id}">−</button>
        <span>${item.quantidade}</span>
        <button type="button" data-aumentar="${item.produto_id}">+</button>
      </div>
      <span class="mono">${formatarPreco(item.preco * item.quantidade)}</span>
      <button class="botao botao-perigo botao-pequeno" data-remover="${item.produto_id}">Remover</button>
    </div>`
    )
    .join("");

  areaTotal.innerHTML = `
    <div class="resumo-total">
      <span>Total</span>
      <span>${formatarPreco(total)}</span>
    </div>
    <button class="botao botao-primario botao-bloco" id="btn-finalizar">Finalizar pedido</button>
  `;

  document.getElementById("btn-finalizar").addEventListener("click", finalizarPedido);
}

async function alterarQuantidade(produtoId, delta) {
  const linha = document.querySelector(`[data-linha="${produtoId}"]`);
  const quantidadeAtual = Number(linha.querySelector(".controle-quantidade span").textContent);
  const novaQuantidade = quantidadeAtual + delta;

  if (novaQuantidade <= 0) {
    await api(`/carrinho/${produtoId}`, { method: "DELETE" });
  } else {
    await api(`/carrinho/${produtoId}`, {
      method: "PUT",
      body: JSON.stringify({ quantidade: novaQuantidade }),
    });
  }
  atualizarContadorCarrinho();
  carregarCarrinho();
}

async function finalizarPedido() {
  const mensagem = document.getElementById("mensagem-pedido");
  try {
    const resultado = await api("/pedido", { method: "POST" });
    mensagem.textContent = `Pedido #${resultado.pedido_id} confirmado! Total: ${formatarPreco(resultado.total)}. Obrigado pela compra 🛹`;
    atualizarContadorCarrinho();
    carregarCarrinho();
  } catch (erro) {
    mensagem.textContent = "Erro ao finalizar pedido: " + erro.message;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  carregarCarrinho();

  // Delegação de evento: um listener só, no container da lista,
  // detecta cliques em qualquer botão de +/-/remover.
  document.getElementById("lista-carrinho").addEventListener("click", (evento) => {
    const aumentar = evento.target.closest("[data-aumentar]");
    const diminuir = evento.target.closest("[data-diminuir]");
    const remover = evento.target.closest("[data-remover]");

    if (aumentar) alterarQuantidade(Number(aumentar.dataset.aumentar), 1);
    if (diminuir) alterarQuantidade(Number(diminuir.dataset.diminuir), -1);
    if (remover) {
      api(`/carrinho/${remover.dataset.remover}`, { method: "DELETE" }).then(() => {
        atualizarContadorCarrinho();
        carregarCarrinho();
      });
    }
  });
});
