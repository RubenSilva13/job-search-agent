// O score com a cor do que vale a pena: verde, amarelo ou vermelho.
// Os limites são uma escolha minha: os scores reais andam entre 13 e 75.
function classesDoScore(valor: number): string {
  if (valor >= 55) {
    return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300";
  }
  if (valor >= 35) {
    return "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300";
  }
  return "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300";
}

export default function Score({ valor, grande = false }: { valor: number; grande?: boolean }) {
  const tamanho = grande ? "px-4 py-2 text-2xl" : "px-2.5 py-1 text-base";
  return (
    <span className={`shrink-0 rounded-lg font-bold tabular-nums ${tamanho} ${classesDoScore(valor)}`}>
      {valor}
      <span className="text-xs font-medium opacity-70">/100</span>
    </span>
  );
}
