// O Next envolve automaticamente as páginas em <Suspense> e mostra isto enquanto
// os dados da API não chegam. Cobre a lista, o detalhe e os custos.
export default function Loading() {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <p className="text-suave">A carregar...</p>
    </main>
  );
}
