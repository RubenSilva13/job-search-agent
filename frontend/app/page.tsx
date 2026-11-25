import Link from "next/link";
import { ESTADOS, textoDoEstado } from "./estados";
import Etiqueta from "./Etiqueta";
import Score from "./Score";

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
      <h1 className="mb-4 text-2xl font-semibold">Vagas analisadas</h1>

      <nav className="mb-6 flex flex-wrap gap-2">
        {FILTROS.map((opcao) => {
          const ativo = opcao.valor === filtro;
          return (
            <Link
              key={opcao.valor}
              href={opcao.valor === "" ? "/" : `/?estado=${opcao.valor}`}
              className={`rounded-full border px-3 py-1 text-sm ${
                ativo
                  ? "border-transparent bg-destaque text-background"
                  : "border-borda bg-superficie text-suave hover:text-foreground"
              }`}
            >
              {opcao.texto}
            </Link>
          );
        })}
      </nav>

      <p className="mb-3 text-sm text-suave">
        {vagas.length} de {todasAsVagas.length} vagas
      </p>

      {vagas.length === 0 && (
        <p className="rounded-lg border border-dashed border-borda p-6 text-center text-sm text-suave">
          Nenhuma vaga neste filtro.
        </p>
      )}

      <ul className="flex flex-col gap-3">
        {vagas.map((vaga) => (
          // relative: o link do título estica-se por todo o cartão (ver o after: abaixo)
          <li
            key={vaga.id}
            className="relative rounded-lg border border-borda bg-superficie p-5 transition-colors hover:border-destaque"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                {/* Link do Next: muda de página sem recarregar tudo */}
                <Link
                  href={`/vagas/${vaga.id}`}
                  className="font-medium text-destaque after:absolute after:inset-0 hover:underline"
                >
                  {vaga.titulo}
                </Link>
                <p className="mt-0.5 text-sm">{vaga.empresa}</p>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {vaga.localizacao && <Etiqueta>{vaga.localizacao}</Etiqueta>}
                  {vaga.regime && <Etiqueta capitalizar>{vaga.regime}</Etiqueta>}
                  {/* O selo só aparece se a vaga já tem candidatura */}
                  {vaga.candidatura_estado && (
                    <span className="rounded-md bg-destaque/10 px-2 py-0.5 text-xs font-medium text-destaque">
                      {textoDoEstado(vaga.candidatura_estado)}
                    </span>
                  )}
                </div>
              </div>
              <Score valor={vaga.score} />
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
