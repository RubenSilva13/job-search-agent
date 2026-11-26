// Onde está a API. Dois endereços, porque quem faz o pedido não é o mesmo:
//
// - o servidor do Next.js (as páginas da lista, do detalhe e dos custos). Dentro do Docker
//   chega à API pelo nome do serviço (http://api:8000), e em local por 127.0.0.1.
// - o browser (o botão das candidaturas e o formulário da nova vaga). Chega à API pelo
//   endereço que a tua máquina vê (http://localhost:8000).
//
// Sem variáveis de ambiente, os dois valem http://127.0.0.1:8000, como até aqui.
export const URL_API_SERVIDOR = process.env.API_URL ?? "http://127.0.0.1:8000";

// NEXT_PUBLIC_ é a convenção do Next.js para variáveis que vão para o browser.
// O valor fica escrito no código na altura do build, por isso não se muda depois.
export const URL_API_BROWSER = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
