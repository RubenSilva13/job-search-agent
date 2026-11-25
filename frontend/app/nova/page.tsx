import FormularioNova from "./FormularioNova";

export default function PaginaNova() {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-2 text-2xl font-semibold">Analisar uma vaga</h1>
      <p className="mb-6 text-sm text-suave">
        Cola o link de um anúncio. O agente lê-o, compara-o com o teu GitHub e o teu perfil, pesquisa a
        empresa e entrega o relatório. Demora cerca de 30 segundos e custa menos de 1 cêntimo.
      </p>
      <FormularioNova />
    </main>
  );
}
