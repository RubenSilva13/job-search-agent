type Dia = { dia: string; execucoes: number; custo: number | null };

// Sobe o máximo para um número redondo (0.0423 -> 0.05), para o eixo ter valores limpos.
function limiteSuperior(maximo: number): number {
  if (maximo <= 0) return 1;
  const potencia = Math.pow(10, Math.floor(Math.log10(maximo)));
  const fracao = maximo / potencia;
  const passo = [1, 2, 2.5, 5, 10].find((candidato) => fracao <= candidato) ?? 10;
  return passo * potencia;
}

// "2026-11-22" -> "22/11"
function diaCurto(dia: string): string {
  const [, mes, numero] = dia.split("-");
  return `${numero}/${mes}`;
}

// Gráfico de colunas do custo por dia. Uma só série, por isso não leva legenda.
// O valor aparece ao passar o rato ou ao focar a coluna com o teclado (Tab).
export default function GraficoCustos({ dias }: { dias: Dia[] }) {
  // A API devolve do dia mais recente para o mais antigo; no gráfico, o tempo corre para a direita.
  const ordenados = [...dias].reverse();

  const maximo = Math.max(...ordenados.map((item) => item.custo ?? 0));
  const topo = limiteSuperior(maximo);
  const casas = topo < 0.1 ? 3 : 2;
  const marcas = [0, topo / 2, topo];

  return (
    <div className="rounded-lg border border-borda bg-superficie p-4" role="group" aria-label="Custo por dia">
      <div className="flex gap-3">
        {/* Eixo vertical: cada valor fica na altura da sua linha */}
        <div className="relative h-40 w-14 shrink-0 text-xs text-suave">
          {marcas.map((valor) => (
            <span
              key={valor}
              className="absolute right-0 translate-y-1/2 tabular-nums"
              style={{ bottom: `${(valor / topo) * 100}%` }}
            >
              ${valor.toFixed(casas)}
            </span>
          ))}
        </div>

        <div className="relative h-40 flex-1">
          {/* Linhas da grelha: finas e discretas */}
          {marcas.map((valor) => (
            <div
              key={valor}
              className="absolute right-0 left-0 border-t border-borda"
              style={{ bottom: `${(valor / topo) * 100}%` }}
            />
          ))}

          {/* As colunas: cada uma ocupa a altura toda, para o rato não ter de acertar numa barra fina */}
          <div className="absolute inset-0 flex">
            {ordenados.map((item) => {
              const custo = item.custo ?? 0;
              // uma coluna com custo nunca fica com menos de 2px de altura
              const altura = custo > 0 ? Math.max((custo / topo) * 100, 1.5) : 0;
              return (
                <div
                  key={item.dia}
                  tabIndex={0}
                  role="img"
                  aria-label={`${diaCurto(item.dia)}: $${custo.toFixed(4)}, ${item.execucoes} análises`}
                  className="group relative flex flex-1 items-end justify-center outline-none"
                >
                  <div
                    className="w-6 rounded-t-[4px] bg-destaque transition-opacity group-hover:opacity-70 group-focus:opacity-70"
                    style={{ height: `${altura}%` }}
                  />
                  <div
                    className="pointer-events-none absolute left-1/2 z-10 hidden -translate-x-1/2 rounded-md bg-foreground px-2 py-1 text-xs whitespace-nowrap text-background group-hover:block group-focus:block"
                    style={{ bottom: `calc(${altura}% + 8px)` }}
                  >
                    <span className="font-semibold">${custo.toFixed(4)}</span>
                    <span className="opacity-70">
                      {" "}
                      · {item.execucoes} {item.execucoes === 1 ? "análise" : "análises"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Eixo horizontal: os dias, alinhados com as colunas */}
      <div className="mt-2 flex gap-3">
        <div className="w-14 shrink-0" />
        <div className="flex flex-1">
          {ordenados.map((item) => (
            <span key={item.dia} className="flex-1 text-center text-xs text-suave">
              {diaCurto(item.dia)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
