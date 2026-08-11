/*
 * admin.js
 * --------
 * Painel administrativo: só carrega os dados se a API confirmar que
 * o usuário logado tem papel = "admin". Depois disso, permite
 * criar, editar e excluir produtos (CRUD completo).
 *
 * Conceito pra explicar: aqui reaproveitamos o MESMO formulário
 * (#form-produto) tanto para criar quanto para editar -- só mudamos
 * se ele faz um POST (criar) ou PUT (editar), dependendo se já existe
 * um id preenchido no campo escondido #produto-id.
 */

const modal = document.getElementById("modal-produto");
const formProduto = document.getElementById("form-produto");

function abrirModal(produto = null) {
  formProduto.reset();
  document.getElementById("titulo-modal").textContent = produto ? "Editar produto" : "Novo produto";
  document.getElementById("produto-id").value = produto ? produto.id : "";
  if (produto) {
    document.getElementById("produto-nome").value = produto.nome;
    document.getElementById("produto-descricao").value = produto.descricao;
    document.getElementById("produto-preco").value = produto.preco;
    document.getElementById("produto-categoria").value = produto.categoria;
    document.getElementById("produto-estoque").value = produto.estoque;
    document.getElementById("produto-icone").value = produto.icone;
    document.getElementById("produto-cor").value = produto.cor;
    document.getElementById("produto-destaque").checked = !!produto.destaque;
  }
  modal.style.display = "flex";
}

function fecharModal() {
  modal.style.display = "none";
}

function linhaTabela(produto) {
  return `
    <tr data-linha-produto="${produto.id}">
      <td style="font-size:1.4rem;">${produto.icone}</td>
      <td>${produto.nome}</td>
      <td>${produto.categoria}</td>
      <td class="mono">${formatarPreco(produto.preco)}</td>
      <td>${produto.estoque}</td>
      <td>${produto.destaque ? "✅" : "—"}</td>
      <td style="display:flex; gap:8px;">
        <button class="botao botao-secundario botao-pequeno" data-editar="${produto.id}">Editar</button>
        <button class="botao botao-perigo botao-pequeno" data-excluir="${produto.id}">Excluir</button>
      </td>
    </tr>`;
}

async function carregarTabelaProdutos() {
  const { produtos } = await api("/produtos");
  document.getElementById("corpo-tabela-produtos").innerHTML = produtos.map(linhaTabela).join("");
  window._produtosCache = produtos; // guardamos em memória pra reabrir no modal de edição sem nova chamada
}

async function iniciarAdmin() {
  const { usuario } = await api("/auth/eu");

  if (!usuario || usuario.papel !== "admin") {
    document.getElementById("bloqueio-admin").style.display = "block";
    return;
  }

  document.getElementById("painel-admin").style.display = "block";
  carregarTabelaProdutos();
}

document.getElementById("btn-novo-produto")?.addEventListener("click", () => abrirModal());
document.getElementById("btn-cancelar-modal")?.addEventListener("click", fecharModal);

document.getElementById("corpo-tabela-produtos")?.addEventListener("click", async (evento) => {
  const botaoEditar = evento.target.closest("[data-editar]");
  const botaoExcluir = evento.target.closest("[data-excluir]");

  if (botaoEditar) {
    const produto = window._produtosCache.find((p) => p.id === Number(botaoEditar.dataset.editar));
    abrirModal(produto);
  }

  if (botaoExcluir) {
    const confirmou = confirm("Tem certeza que deseja excluir este produto?");
    if (!confirmou) return;
    await api(`/produtos/${botaoExcluir.dataset.excluir}`, { method: "DELETE" });
    carregarTabelaProdutos();
  }
});

formProduto?.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("produto-id").value;

  const corpo = {
    nome: document.getElementById("produto-nome").value,
    descricao: document.getElementById("produto-descricao").value,
    preco: Number(document.getElementById("produto-preco").value),
    categoria: document.getElementById("produto-categoria").value,
    estoque: Number(document.getElementById("produto-estoque").value),
    icone: document.getElementById("produto-icone").value,
    cor: document.getElementById("produto-cor").value,
    destaque: document.getElementById("produto-destaque").checked ? 1 : 0,
  };

  try {
    if (id) {
      await api(`/produtos/${id}`, { method: "PUT", body: JSON.stringify(corpo) });
    } else {
      await api("/produtos", { method: "POST", body: JSON.stringify(corpo) });
    }
    fecharModal();
    carregarTabelaProdutos();
  } catch (erro) {
    alert("Erro ao salvar produto: " + erro.message);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("painel-admin")) iniciarAdmin();
});
