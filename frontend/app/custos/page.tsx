
import { URL_API_SERVIDOR } from "../api";
import GraficoCustos from "./GraficoCustos";


// A forma do JSON de GET /custos. Os valores numéricos podem vir a null
// (por exemplo, a média de uma coluna sem valores).
type Custos = {
  resumo: {
    execucoes: number;
    ok: number;
    sem_relatorio: number;
    erro: number;
    tokens_entrada: number;
    tokens_saida: number;
    custo_total: number | null;
    custo_medio: number | null;
    duracao_media_ms: number | null;
  };
  por_dia: { dia: string; execucoes: number; custo: number | null }[];
  ferramentas: {
    nome: string;
    chamadas: number;
    media_ms: number | null;
    max_ms: number | null;
    erros: number;
  }[];
  tempos: { tipo: string; total_ms: number | null }[];
  mais_caras: {
    vaga: string;
    custo_estimado: number | null;
    tokens_entrada: number;
    tokens_saida: number;
    duracao_ms: number | null;
  }[];
};

// Os mesmos formatos do custos.py: dólares com 4 casas, segundos com 1.
function dolares(valor: number | null): string {
  return valor === null ? "-" : `$${valor.toFixed(4)}`;
}

function segundos(milissegundos: number | null): string {
  return milissegundos === null ? "-" : `${(milissegundos / 1000).toFixed(1)} s`;
}

// As classes que se repetem nas tabelas e nos títulos das secções.
const TITULO = "mt-10 mb-1 text-lg font-semibold";
const CARTAO_TABELA = "overflow-hidden rounded-lg border border-borda bg-superficie";
const TH = "px-4 py-2 text-xs font-medium uppercase tracking-wide text-suave";
const TD = "px-4 py-2";

// Um cartão com um número grande e uma legenda.
function Cartao({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div className="rounded-lg border border-borda bg-superficie p-4">
      <p className="text-sm text-suave">{titulo}</p>
      <p className="text-2xl font-bold">{valor}</p>
    </div>
  );
}

export default async function PaginaCustos() {
  const resposta = await fetch(`${URL_API_SERVIDOR}/custos`);
  const custos: Custos = await resposta.json();
  const resumo = custos.resumo;

  // Sem execuções registadas não há nada para mostrar.
  if (resumo.execucoes === 0) {
    return (
      <main className="mx-auto max-w-3xl p-8">
        <p>Ainda não há execuções registadas. Corre python diario.py primeiro.</p>
      </main>
    );
  }

  // Soma do tempo de todos os passos, para calcular a percentagem de cada tipo.
  const tempoTotal = custos.tempos.reduce((soma, item) => soma + (item.total_ms ?? 0), 0);

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-semibold">Custos e tempos</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Cartao titulo="Análises" valor={String(resumo.execucoes)} />
        <Cartao titulo="Custo total" valor={dolares(resumo.custo_total)} />
        <Cartao titulo="Custo médio" valor={dolares(resumo.custo_medio)} />
        <Cartao titulo="Duração média" valor={segundos(resumo.duracao_media_ms)} />
      </div>
      <p className="mt-3 text-sm text-suave">
        {resumo.ok} com relatório, {resumo.sem_relatorio} sem relatório, {resumo.erro} com erro ·{" "}
        {resumo.tokens_entrada.toLocaleString("pt-PT")} tokens de entrada,{" "}
        {resumo.tokens_saida.toLocaleString("pt-PT")} de saída. O custo é uma estimativa.
      </p>

      <h2 className={TITULO}>Custo por dia</h2>
      <p className="mb-3 text-sm text-suave">Últimos {custos.por_dia.length} dias com análises, em dólares.</p>
      <GraficoCustos dias={custos.por_dia} />

      {/* A mesma informação em tabela: mostra os valores exatos sem ser preciso passar o rato */}
      <div className={CARTAO_TABELA + " mt-3"}>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-borda">
              <th className={TH}>Dia</th>
              <th className={TH + " text-right"}>Análises</th>
              <th className={TH + " text-right"}>Custo</th>
            </tr>
          </thead>
          <tbody>
            {custos.por_dia.map((linha) => (
              <tr key={linha.dia} className="border-b border-borda last:border-0">
                <td className={TD}>{linha.dia}</td>
                <td className={TD + " text-right tabular-nums"}>{linha.execucoes}</td>
                <td className={TD + " text-right tabular-nums"}>{dolares(linha.custo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className={TITULO}>Ferramentas</h2>
      <p className="mb-3 text-sm text-suave">Das mais lentas para as mais rápidas.</p>
      <div className={CARTAO_TABELA}>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-borda">
              <th className={TH}>Ferramenta</th>
              <th className={TH + " text-right"}>Chamadas</th>
              <th className={TH + " text-right"}>Média</th>
              <th className={TH + " text-right"}>Máx.</th>
              <th className={TH + " text-right"}>Erros</th>
            </tr>
          </thead>
          <tbody>
            {custos.ferramentas.map((linha) => (
              <tr key={linha.nome} className="border-b border-borda last:border-0">
                <td className={TD}>{linha.nome}</td>
                <td className={TD + " text-right tabular-nums"}>{linha.chamadas}</td>
                <td className={TD + " text-right tabular-nums"}>{segundos(linha.media_ms)}</td>
                <td className={TD + " text-right tabular-nums"}>{segundos(linha.max_ms)}</td>
                <td className={TD + " text-right tabular-nums"}>{linha.erros}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {tempoTotal > 0 && (
        <>
          <h2 className={TITULO}>Onde vai o tempo</h2>
          <p className="mb-3 text-sm text-suave">Parte do tempo total de todas as análises.</p>
          <div className="flex flex-col gap-4 rounded-lg border border-borda bg-superficie p-4">
            {[...custos.tempos]
              .sort((a, b) => (b.total_ms ?? 0) - (a.total_ms ?? 0))
              .map((item) => {
                const percentagem = Math.round(((item.total_ms ?? 0) / tempoTotal) * 100);
                return (
                  <div key={item.tipo}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span className="capitalize">{item.tipo === "modelo" ? "Modelo" : "Ferramentas"}</span>
                      <span className="text-suave tabular-nums">
                        {segundos(item.total_ms)} · {percentagem}%
                      </span>
                    </div>
                    {/* A pista é a parte vazia; o preenchimento é a parte do tempo */}
                    <div className="h-2 rounded-full bg-borda">
                      <div className="h-2 rounded-full bg-destaque" style={{ width: `${percentagem}%` }} />
                    </div>
                  </div>
                );
              })}
          </div>
        </>
      )}

      <h2 className={TITULO}>As 3 análises mais caras</h2>
      <div className={CARTAO_TABELA + " mt-3"}>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-borda">
              <th className={TH}>Vaga</th>
              <th className={TH + " text-right"}>Custo</th>
              <th className={TH + " text-right"}>Tokens</th>
              <th className={TH + " text-right"}>Tempo</th>
            </tr>
          </thead>
          <tbody>
            {custos.mais_caras.map((linha, posicao) => (
              <tr key={posicao} className="border-b border-borda last:border-0">
                <td className={TD}>{linha.vaga}</td>
                <td className={TD + " text-right tabular-nums"}>{dolares(linha.custo_estimado)}</td>
                <td className={TD + " text-right tabular-nums"}>
                  {linha.tokens_entrada.toLocaleString("pt-PT")} + {linha.tokens_saida.toLocaleString("pt-PT")}
                </td>
                <td className={TD + " text-right tabular-nums"}>{segundos(linha.duracao_ms)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
