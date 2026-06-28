const VALOR_NUMERO = 15.0; // altere para o valor da sua rifa

let carrinho = [];

const carrinhoDiv = document.getElementById("carrinho");
const listaNumeros = document.getElementById("listaNumeros");
const valorTotal = document.getElementById("valorTotal");

document.querySelectorAll(".numero-disponivel").forEach((numero) => {
  numero.addEventListener("click", () => {
    const id = numero.dataset.id;
    const texto = numero.dataset.numero;

    if (carrinho.find((n) => n.id === id)) {
      carrinho = carrinho.filter((n) => n.id !== id);
      numero.classList.remove("selecionado");
    } else {
      carrinho.push({
        id: id,
        numero: texto,
      });

      numero.classList.add("selecionado");
    }

    atualizarCarrinho();
  });
});

document.getElementById("continuar").addEventListener("click", () => {
  if (carrinho.length === 0) {
    alert("Selecione pelo menos um número.");
    return;
  }

  const ids = carrinho.map((n) => n.id).join(",");

  window.location.href = "/checkout?ids=" + ids;
});

function atualizarCarrinho() {
  if (carrinho.length === 0) {
    carrinhoDiv.style.display = "none";
    return;
  }

  carrinhoDiv.style.display = "block";

  listaNumeros.innerHTML = carrinho
    .map((n) => `<span>${n.numero}</span>`)
    .join(", ");

  valorTotal.innerHTML =
    "R$ " + (carrinho.length * VALOR_NUMERO).toFixed(2).replace(".", ",");
}
