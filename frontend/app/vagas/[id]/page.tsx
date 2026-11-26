import Link from "next/link";
import { notFound } from "next/navigation";
import { URL_API_SERVIDOR } from "../../api";
import Etiqueta from "../../Etiqueta";
import Score from "../../Score";
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


// Texto e cores de cada estado de um requisito: a barra do lado esquerdo do cartão e a etiqueta.
const ESTADOS = {
  cumpre: { texto: "Cumpre", barra: "border-l-emerald-500", etiqueta: "text-emerald-700 dark:text-emerald-400" },
  parcial: { texto: "Parcial", barra: "border-l-amber-500", etiqueta: "text-amber-700 dark:text-amber-400" },
  falta: { texto: "Falta", barra: "border-l-red-500", etiqueta: "text-red-700 dark:text-red-400" },
  nao_confirmado: { texto: "Não confirmado", barra: "border-l-stone-400", etiqueta: "text-suave" },
};

export default async function PaginaDetalhe({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  // No Next 16 o params é uma promessa: tem de levar await.
  const { id } = await params;

  const resposta = await fetch(`${URL_API_SERVIDOR}/vagas/${id}`);

  // A API responde 404 quando a vaga não existe ou não tem análise.
  if (resposta.status === 404) {
    notFound();
  }

  const vaga: Vaga = await resposta.json();
  const relatorio = vaga.relatorio;

  return (
    <main className="mx-auto max-w-3xl p-8">
      <Link href="/" className="text-sm text-suave hover:text-foreground">
        ← Todas as vagas
      </Link>

      <div className="mt-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{vaga.titulo}</h1>
          <p className="mt-1 text-suave">{vaga.empresa}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {vaga.localizacao && <Etiqueta>{vaga.localizacao}</Etiqueta>}
            {vaga.regime && <Etiqueta capitalizar>{vaga.regime}</Etiqueta>}
            <a
              href={vaga.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-destaque hover:underline"
            >
              Ver o anúncio ↗
            </a>
          </div>
        </div>
        <Score valor={vaga.score} grande />
      </div>

      <Candidatura
        vagaId={vaga.id}
        estadoInicial={vaga.candidatura_estado}
        notasIniciais={vaga.candidatura_notas}
        dataInicial={vaga.data_candidatura}
      />

      <h2 className="mt-10 mb-2 text-lg font-semibold">A empresa</h2>
      <p className="rounded-lg border border-borda bg-superficie p-4 leading-relaxed">
        {relatorio.resumo_empresa}
      </p>

      <h2 className="mt-10 mb-1 text-lg font-semibold">Requisitos</h2>
      {/* Quantos requisitos há em cada estado, por exemplo: 8 cumpre · 3 parcial · 2 falta */}
      <p className="mb-3 text-sm text-suave">
        {(Object.keys(ESTADOS) as (keyof typeof ESTADOS)[])
          .map((chave) => {
            const quantos = relatorio.requisitos.filter((item) => item.estado === chave).length;
            return `${quantos} ${ESTADOS[chave].texto.toLowerCase()}`;
          })
          .join(" · ")}
      </p>
      <ul className="flex flex-col gap-2">
        {relatorio.requisitos.map((item, posicao) => {
          const estado = ESTADOS[item.estado];
          return (
            <li
              key={posicao}
              className={`rounded-lg border border-l-4 border-borda bg-superficie p-3 ${estado.barra}`}
            >
              <p className={`text-xs font-semibold uppercase tracking-wide ${estado.etiqueta}`}>
                {estado.texto}
              </p>
              <p className="font-medium">{item.requisito}</p>
              {item.evidencia && <p className="mt-1 text-sm text-suave">{item.evidencia}</p>}
            </li>
          );
        })}
      </ul>

      <h2 className="mt-10 mb-2 text-lg font-semibold">Sugestões</h2>
      <ul className="list-disc rounded-lg border border-borda bg-superficie py-4 pr-4 pl-9 leading-relaxed">
        {relatorio.sugestoes.map((sugestao, posicao) => (
          <li key={posicao} className="mb-2 last:mb-0">
            {sugestao}
          </li>
        ))}
      </ul>
    </main>
  );
}
