"use client";

import { useState } from "react";
import { URL_API_BROWSER } from "../../api";
import { ESTADOS } from "../../estados";


type Props = {
  vagaId: number;
  estadoInicial: string | null;
  notasIniciais: string | null;
  dataInicial: string | null;
};

export default function Candidatura({ vagaId, estadoInicial, notasIniciais, dataInicial }: Props) {
  // Cada useState guarda um valor que pode mudar e a função para o mudar.
  // Quando se chama a função, o React volta a desenhar o componente.
  const [estado, setEstado] = useState(estadoInicial ?? "");
  const [notas, setNotas] = useState(notasIniciais ?? "");
  const [data, setData] = useState(dataInicial);
  const [mensagem, setMensagem] = useState("");
  const [aGuardar, setAGuardar] = useState(false);

  async function guardar() {
    setAGuardar(true);
    setMensagem("");
    try {
      const resposta = await fetch(`${URL_API_BROWSER}/vagas/${vagaId}/candidatura`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        // notas vazias vão como null, para a base de dados não guardar texto vazio
        body: JSON.stringify({ estado, notas: notas.trim() === "" ? null : notas }),
      });
      if (!resposta.ok) {
        setMensagem("Não foi possível guardar.");
        return;
      }
      const candidatura = await resposta.json();
      setData(candidatura.data_candidatura);
      setMensagem("Guardado.");
    } catch {
      // erro de rede: a API está desligada
      setMensagem("A API não responde. Está ligada?");
    } finally {
      setAGuardar(false);
    }
  }

  return (
    <section className="mt-8 rounded-lg border border-borda bg-superficie p-4">
      <h2 className="mb-3 text-lg font-semibold">Candidatura</h2>

      <div className="flex flex-col gap-3">
        <label className="flex flex-col gap-1 text-sm">
          Estado
          <select
            value={estado}
            onChange={(evento) => setEstado(evento.target.value)}
            className="rounded border border-borda bg-superficie p-2"
          >
            <option value="" disabled>
              Sem estado
            </option>
            {ESTADOS.map((opcao) => (
              <option key={opcao.valor} value={opcao.valor}>
                {opcao.texto}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Notas
          <textarea
            value={notas}
            onChange={(evento) => setNotas(evento.target.value)}
            rows={3}
            className="rounded border border-borda bg-superficie p-2"
          />
        </label>

        {data && <p className="text-sm text-suave">Candidatura feita em {data}</p>}

        <div className="flex items-center gap-3">
          <button
            onClick={guardar}
            disabled={estado === "" || aGuardar}
            className="rounded bg-foreground px-4 py-2 text-sm text-background disabled:opacity-40"
          >
            {aGuardar ? "A guardar..." : "Guardar"}
          </button>
          {mensagem && <span className="text-sm">{mensagem}</span>}
        </div>
      </div>
    </section>
  );
}
