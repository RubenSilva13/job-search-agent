import Link from "next/link";
import { notFound } from "next/navigation";
import Candidatura from "./Candidatura";

type Requisito = {
  requisito: string;
  estado: "cumpre" | "parcial" | "falta" | "nao_confirmado";
  evidencia: string | null;
};

type Relatorio = {
  resumo_empresa: string;
  sugestoes: string[];
  requisitos: Requisito[];
};

// A forma do JSON de GET /vagas/{id}.
type Vaga = {
  id: number;
  titulo: string;
  empresa: string;
  localizacao: string | null;
  regime: string | null;
  url: string;
  score: number;
  relatorio: Relatorio;
  candidatura_estado: string | null;
  candidatura_notas: string | null;
  data_candidatura: string | null;
};

const URL_API = "http://127.0.0.1:8000";

// Texto e cor de cada estado de um requisito.
const ESTADOS = {
  cumpre: { icone: "✅", texto: "Cumpre" },
  parcial: { icone: "🟡", texto: "Parcial" },
  falta: { icone: "❌", texto: "Falta" },
  nao_confirmado: { icone: "❔", texto: "Não confirmado" },
};

export default async function PaginaDetalhe({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  // No Next 16 o params é uma promessa: tem de levar await.
  const { id } = await params;

  const resposta = await fetch(`${URL_API}/vagas/${id}`);

  // A API responde 404 quando a vaga não existe ou não tem análise.
  if (resposta.status === 404) {
    notFound();
  }

  const vaga: Vaga = await resposta.json();
  const relatorio = vaga.relatorio;

  return (
    <main className="mx-auto max-w-3xl p-8">
      <Link href="/" className="text-sm text-zinc-600 hover:underline dark:text-zinc-400">
        ← Todas as vagas
      </Link>

      <div className="mt-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{vaga.titulo}</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            {vaga.empresa} · {vaga.localizacao} · {vaga.regime}
          </p>
          <a href={vaga.url} target="_blank" rel="noopener noreferrer" className="text-sm underline">
            Ver o anúncio
          </a>
        </div>
        <span className="text-3xl font-bold">{vaga.score}/100</span>
      </div>

      <Candidatura
        vagaId={vaga.id}
        estadoInicial={vaga.candidatura_estado}
        notasIniciais={vaga.candidatura_notas}
        dataInicial={vaga.data_candidatura}
      />

      <h2 className="mt-8 mb-2 text-lg font-semibold">A empresa</h2>
      <p>{relatorio.resumo_empresa}</p>

      <h2 className="mt-8 mb-2 text-lg font-semibold">Requisitos</h2>
      <ul className="flex flex-col gap-3">
        {relatorio.requisitos.map((item, posicao) => {
          const estado = ESTADOS[item.estado];
          return (
            <li key={posicao} className="rounded-lg border border-zinc-300 p-3 dark:border-zinc-700">
              <p className="font-medium">
                {estado.icone} {item.requisito} <span className="text-sm font-normal">({estado.texto})</span>
              </p>
              {item.evidencia && (
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{item.evidencia}</p>
              )}
            </li>
          );
        })}
      </ul>

      <h2 className="mt-8 mb-2 text-lg font-semibold">Sugestões</h2>
      <ul className="list-disc pl-5">
        {relatorio.sugestoes.map((sugestao, posicao) => (
          <li key={posicao}>{sugestao}</li>
        ))}
      </ul>
    </main>
  );
}
