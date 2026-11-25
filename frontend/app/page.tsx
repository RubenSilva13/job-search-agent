import Link from "next/link";

// A forma de cada vaga que a API devolve em GET /vagas.
// Os nomes têm de ser iguais aos do JSON (os campos do SELECT no api.py).
type Vaga = {
  id: number;
  titulo: string;
  empresa: string;
  localizacao: string | null;
  regime: string | null;
  url: string;
  score: number;
};

const URL_API = "http://127.0.0.1:8000";

export default async function PaginaVagas() {
  // Pede a lista à API. O await espera pela resposta antes de avançar.
  const resposta = await fetch(`${URL_API}/vagas`);

  // Lê o corpo da resposta como JSON. O ": Vaga[]" diz ao TypeScript que é uma lista de Vaga.
  const vagas: Vaga[] = await resposta.json();

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-semibold">Vagas analisadas</h1>

      <ul className="flex flex-col gap-3">
        {vagas.map((vaga) => (
          <li key={vaga.id} className="rounded-lg border border-zinc-300 p-4 dark:border-zinc-700">
            <div className="flex items-start justify-between gap-4">
              <div>
                {/* Link do Next: muda de página sem recarregar tudo */}
                <Link href={`/vagas/${vaga.id}`} className="font-medium hover:underline">
                  {vaga.titulo}
                </Link>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  {vaga.empresa} · {vaga.localizacao} · {vaga.regime}
                </p>
              </div>
              <span className="text-xl font-bold">{vaga.score}/100</span>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
