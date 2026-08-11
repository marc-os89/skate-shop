/*
 * auth.js
 * -------
 * Cuida dos formulários de login e cadastro.
 * Conceito pra explicar: "preventDefault()" impede o comportamento
 * padrão do <form> (que seria recarregar a página), permitindo
 * a gente controlar o envio via JavaScript/fetch.
 */

function mostrarErro(texto) {
  const elemento = document.getElementById("mensagem-erro");
  if (!elemento) return;
  elemento.textContent = texto;
  elemento.classList.add("visivel");
}

const formLogin = document.getElementById("form-login");
if (formLogin) {
  formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const email = document.getElementById("email").value;
    const senha = document.getElementById("senha").value;

    try {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, senha }),
      });
      window.location.href = "index.html";
    } catch (erro) {
      mostrarErro(erro.message);
    }
  });
}

const formCadastro = document.getElementById("form-cadastro");
if (formCadastro) {
  formCadastro.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const nome = document.getElementById("nome").value;
    const email = document.getElementById("email").value;
    const senha = document.getElementById("senha").value;

    try {
      await api("/auth/cadastro", {
        method: "POST",
        body: JSON.stringify({ nome, email, senha }),
      });
      window.location.href = "index.html";
    } catch (erro) {
      mostrarErro(erro.message);
    }
  });
}
