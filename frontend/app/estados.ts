// Os estados de uma candidatura. Os valores são os do CHECK da tabela candidaturas;
// o texto é o que se mostra. Usado na lista (selo e filtro) e no detalhe (select).
export const ESTADOS = [
  { valor: "por_candidatar", texto: "Por candidatar" },
  { valor: "candidatado", texto: "Candidatado" },
  { valor: "entrevista", texto: "Entrevista" },
  { valor: "oferta", texto: "Oferta" },
  { valor: "recusada", texto: "Recusada" },
  { valor: "desistiu", texto: "Desisti" },
];

// Devolve o texto de um estado, ou o próprio valor se não o conhecer.
export function textoDoEstado(valor: string): string {
  const estado = ESTADOS.find((item) => item.valor === valor);
  return estado ? estado.texto : valor;
}
