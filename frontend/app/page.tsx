import Link from "next/link";
import { ESTADOS, textoDoEstado } from "./estados";

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
  candidatura_estado: string | null;
};

const URL_API = "http://127.0.0.1:8000";

// Os filtros: "todas" (sem parâmetro), "sem" (vagas sem candidatura) e cada estado.
const FILTROS = [
  { valor: "", texto: "Todas" },
  { valor: "sem", texto: "Sem candidatura" },
  ...ESTADOS,
];

export default async function PaginaVagas({
  searchParams,
}: {
  searchParams: Promise<{ estado?: string }>;
}) {
  // O que vem depois do ? no endereço: /?estado=candidatado dá { estado: "candidatado" }.
  const { estado: filtro = "" } = await searchParams;

  // Pede a lista à API. O await espera pela resposta antes de avançar.
  const resposta = await fetch(`${URL_API}/vagas`);

  // Lê o corpo da resposta como JSON. O ": Vaga[]" diz ao TypeScript que é uma lista de Vaga.
  const todasAsVagas: Vaga[] = await resposta.json();

  // Aplica o filtro escolhido.
  const vagas = todasAsVagas.filter((vaga) => {
    if (filtro === "") return true;
    if (filtro === "sem") return vaga.candidatura_estado === null;
    return vaga.candidatura_estado === filtro;
  });

  return (
    <main className="mx-auto max-w-3xl p-8">
      <div className="mb-4 flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold">Vagas analisadas</h1>
        <Link href="/custos" className="text-sm underline">
          Custos
        </Link>
      </div>

      <nav className="mb-6 flex flex-wrap gap-2">
        {FILTROS.map((opcao) => {
          const ativo = opcao.valor === filtro;
          return (
            <Link
              key={opcao.valor}
              href={opcao.valor === "" ? "/" : `/?estado=${opcao.valor}`}
              className={`rounded-full border px-3 py-1 text-sm ${
                ativo
                  ? "border-transparent bg-foreground text-background"
                  : "border-zinc-300 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-900"
              }`}
            >
              {opcao.texto}
            </Link>
          );
        })}
      </nav>

      <p className="mb-3 text-sm text-zinc-600 dark:text-zinc-400">
        {vagas.length} de {todasAsVagas.length} vagas
      </p>

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
                {/* O selo só aparece se a vaga já tem candidatura */}
                {vaga.candidatura_estado && (
                  <span className="mt-2 inline-block rounded-full bg-zinc-200 px-2 py-0.5 text-xs font-medium dark:bg-zinc-800">
                    {textoDoEstado(vaga.candidatura_estado)}
                  </span>
                )}
              </div>
              <span className="text-xl font-bold">{vaga.score}/100</span>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
