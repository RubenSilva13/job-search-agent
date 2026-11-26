"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { URL_API_BROWSER } from "../api";

const PAUSA_MS = 2000;

// Espera um tempo (em milissegundos) dentro de uma função async.
function esperar(milissegundos: number) {
  return new Promise((resolver) => setTimeout(resolver, milissegundos));
}

export default function FormularioNova() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [aAnalisar, setAAnalisar] = useState(false);
  const [segundos, setSegundos] = useState(0);
  const [erro, setErro] = useState("");

  // Se saíres da página a meio, a espera pára (o agente continua a correr na API).
  const aberta = useRef(true);
  useEffect(() => {
    aberta.current = true;
    return () => {
      aberta.current = false;
    };
  }, []);

  async function analisar() {
    setErro("");
    setAAnalisar(true);
    setSegundos(0);

    try {
      // 1. Pede à API para arrancar a análise. Responde logo com um id.
      const pedido = await fetch(`${URL_API_BROWSER}/analises`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (!pedido.ok) {
        const corpo = await pedido.json().catch(() => null);
        setErro(corpo?.detail ?? "Não foi possível arrancar a análise.");
        setAAnalisar(false);
        return;
      }
      const { id } = await pedido.json();

      // 2. Pergunta de 2 em 2 segundos como vai, até estar pronta ou falhar.
      const inicio = Date.now();
      while (aberta.current) {
        await esperar(PAUSA_MS);
        setSegundos(Math.round((Date.now() - inicio) / 1000));

        const resposta = await fetch(`${URL_API_BROWSER}/analises/${id}`);
        const analise = await resposta.json();

        if (analise.estado === "pronta") {
          router.push(`/vagas/${analise.vaga_id}`);
          return;
        }
        if (analise.estado === "erro") {
          setErro(analise.mensagem ?? "A análise falhou.");
          setAAnalisar(false);
          return;
        }
      }
    } catch {
      // erro de rede: a API está desligada
      setErro("A API não responde. Está ligada?");
      setAAnalisar(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm">
        Link da vaga
        <input
          type="url"
          value={url}
          onChange={(evento) => setUrl(evento.target.value)}
          disabled={aAnalisar}
          placeholder="https://..."
          className="rounded border border-borda bg-superficie p-2"
        />
      </label>

      <div className="flex items-center gap-3">
        <button
          onClick={analisar}
          disabled={url.trim() === "" || aAnalisar}
          className="rounded bg-foreground px-4 py-2 text-sm text-background disabled:opacity-40"
        >
          {aAnalisar ? "A analisar..." : "Analisar"}
        </button>
        {aAnalisar && <span className="text-sm">{segundos} s (costuma demorar cerca de 30 s)</span>}
      </div>

      {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
    </div>
  );
}
