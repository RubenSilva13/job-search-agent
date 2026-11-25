import Link from "next/link";

const URL_API = "http://127.0.0.1:8000";

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

// Um cartão com um número grande e uma legenda.
function Cartao({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div className="rounded-lg border border-zinc-300 p-4 dark:border-zinc-700">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{titulo}</p>
      <p className="text-2xl font-bold">{valor}</p>
    </div>
  );
}

export default async function PaginaCustos() {
  const resposta = await fetch(`${URL_API}/custos`);
  const custos: Custos = await resposta.json();
  const resumo = custos.resumo;

  // Sem execuções registadas não há nada para mostrar.
  if (resumo.execucoes === 0) {
    return (
      <main className="mx-auto max-w-3xl p-8">
        <Link href="/" className="text-sm text-zinc-600 hover:underline dark:text-zinc-400">
          ← Vagas
        </Link>
        <p className="mt-4">Ainda não há execuções registadas. Corre python diario.py primeiro.</p>
      </main>
    );
  }

  // Soma do tempo de todos os passos, para calcular a percentagem de cada tipo.
  const tempoTotal = custos.tempos.reduce((soma, item) => soma + (item.total_ms ?? 0), 0);

  return (
    <main className="mx-auto max-w-3xl p-8">
      <Link href="/" className="text-sm text-zinc-600 hover:underline dark:text-zinc-400">
        ← Vagas
      </Link>
      <h1 className="mt-4 mb-6 text-2xl font-semibold">Custos e tempos</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Cartao titulo="Análises" valor={String(resumo.execucoes)} />
        <Cartao titulo="Custo total" valor={dolares(resumo.custo_total)} />
        <Cartao titulo="Custo médio" valor={dolares(resumo.custo_medio)} />
        <Cartao titulo="Duração média" valor={segundos(resumo.duracao_media_ms)} />
      </div>
      <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
        {resumo.ok} com relatório, {resumo.sem_relatorio} sem relatório, {resumo.erro} com erro ·{" "}
        {resumo.tokens_entrada.toLocaleString("pt-PT")} tokens de entrada,{" "}
        {resumo.tokens_saida.toLocaleString("pt-PT")} de saída. O custo é uma estimativa.
      </p>

      <h2 className="mt-8 mb-2 text-lg font-semibold">Custo por dia (últimos 7 dias com análises)</h2>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-300 dark:border-zinc-700">
            <th className="py-1">Dia</th>
            <th>Análises</th>
            <th>Custo</th>
          </tr>
        </thead>
        <tbody>
          {custos.por_dia.map((linha) => (
            <tr key={linha.dia} className="border-b border-zinc-200 dark:border-zinc-800">
              <td className="py-1">{linha.dia}</td>
              <td>{linha.execucoes}</td>
              <td>{dolares(linha.custo)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="mt-8 mb-2 text-lg font-semibold">Ferramentas (das mais lentas para as mais rápidas)</h2>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-300 dark:border-zinc-700">
            <th className="py-1">Ferramenta</th>
            <th>Chamadas</th>
            <th>Média</th>
            <th>Máx.</th>
            <th>Erros</th>
          </tr>
        </thead>
        <tbody>
          {custos.ferramentas.map((linha) => (
            <tr key={linha.nome} className="border-b border-zinc-200 dark:border-zinc-800">
              <td className="py-1">{linha.nome}</td>
              <td>{linha.chamadas}</td>
              <td>{segundos(linha.media_ms)}</td>
              <td>{segundos(linha.max_ms)}</td>
              <td>{linha.erros}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {tempoTotal > 0 && (
        <>
          <h2 className="mt-8 mb-2 text-lg font-semibold">Onde vai o tempo</h2>
          <ul className="text-sm">
            {[...custos.tempos]
              .sort((a, b) => (b.total_ms ?? 0) - (a.total_ms ?? 0))
              .map((item) => (
                <li key={item.tipo}>
                  {item.tipo}: {segundos(item.total_ms)} ({Math.round(((item.total_ms ?? 0) / tempoTotal) * 100)}%)
                </li>
              ))}
          </ul>
        </>
      )}

      <h2 className="mt-8 mb-2 text-lg font-semibold">As 3 análises mais caras</h2>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-300 dark:border-zinc-700">
            <th className="py-1">Vaga</th>
            <th>Custo</th>
            <th>Tokens</th>
            <th>Tempo</th>
          </tr>
        </thead>
        <tbody>
          {custos.mais_caras.map((linha, posicao) => (
            <tr key={posicao} className="border-b border-zinc-200 dark:border-zinc-800">
              <td className="py-1">{linha.vaga}</td>
              <td>{dolares(linha.custo_estimado)}</td>
              <td>
                {linha.tokens_entrada.toLocaleString("pt-PT")} + {linha.tokens_saida.toLocaleString("pt-PT")}
              </td>
              <td>{segundos(linha.duracao_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
