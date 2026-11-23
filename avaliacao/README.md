# Avaliação do agente

Compara o score do agente com notas que dei à mão, para saber se o score serve e quanto oscila.
Os resultados e a leitura deles estão na secção Avaliação do [README principal](../README.md).

## Ficheiros

| Ficheiro | O que é |
|---|---|
| `preparar_casos.py` | Escolhe as vagas e gera os ficheiros para as classificar (modo principal e `--teste`) |
| `notas.csv` | As minhas notas das 24 vagas de desenvolvimento (`serve`, `talvez`, `nao`) |
| `notas_teste.csv` | As minhas notas das 15 vagas de teste: `nota` e `cobertura` (`alta`, `media`, `baixa`) |
| `avaliar.py` | Corre as análises e calcula as métricas |
| `resultados.jsonl`, `resultados_teste.jsonl` | Uma linha por análise: score, estados dos requisitos, tokens, custo, tempo |
| `resumo.md`, `resumo_teste.md` | As métricas, geradas por `avaliar.py --resumo` |
| `casos.md`, `casos_teste.md` | O texto completo dos anúncios, para os ler. **Não estão no repositório**: são texto de terceiros (ITJobs) e os termos de uso da fonte não estão confirmados |

## Como se corre

```bash
# 1. conjunto de desenvolvimento (24 vagas)
python avaliacao/preparar_casos.py            # gera casos.md e notas.csv
# ... ler casos.md e preencher a coluna nota de notas.csv, sem correr o agente ...
python avaliacao/avaliar.py --so 2 --reps 1   # piloto com 2 vagas, para ver se tudo vem preenchido
python avaliacao/avaliar.py --reps 3          # a avaliação completa (cerca de 35 cêntimos)
python avaliacao/avaliar.py --resumo          # calcula as métricas, não gasta nada

# 2. conjunto de teste (15 vagas que o agente nunca analisou)
python avaliacao/preparar_casos.py --teste
python avaliacao/avaliar.py --conjunto teste --reps 3
python avaliacao/avaliar.py --conjunto teste --resumo
```

Precisa da base de dados a correr (o Docker aberto) e da chave da API da Anthropic. Cada análise é
escrita em `resultados*.jsonl` logo que acaba, por isso uma interrupção não perde o que já correu e
voltar a correr só faz o que falta. As falhas de rede vão para `erros*.jsonl` e repetem-se.

## O que cada métrica diz

- **Correlação de ordem (Spearman):** as vagas com nota melhor tendem a ter score maior? De 0 (ao
  acaso) a 1 (mesma ordem). Com 24 vagas, por puro acaso o valor fica entre −0,40 e +0,39.
- **Separação serve / nao:** em que fração dos pares (uma vaga `serve`, uma `nao`) a `serve` tem o
  score maior. 0,50 é o acaso, 1 é perfeita.
- **Oscilação:** diferença entre o maior e o menor score da mesma vaga em 3 repetições.
- **Intervalo de 95%:** calculado por reamostragem das vagas. Quando inclui o zero, a correlação não
  se distingue do acaso. Com poucas vagas o intervalo da separação pode colapsar e parecer certeza.

## Regras que se aprenderam a fazer isto

- **Classificar às cegas.** Ler as vagas sem ver nenhum score nem relatório do agente, senão a nota
  deixa de ser independente.
- **O conjunto fecha-se quando há notas.** `preparar_casos.py` lê os ids de `notas.csv` e já não
  escolhe outra vez. A base de dados ganha vagas todos os dias, e uma nova escolha daria outro
  conjunto e quebraria a ligação entre as notas e o `casos.md`.
- **O conjunto de teste usa-se uma só vez.** Só com vagas que o agente nunca analisou, e sem mexer
  no agente depois de classificar. Quando se vêem os resultados, o conjunto fica "queimado": ajustar
  o agente a pensar nele deixaria de medir. Uma melhoria nova confirma-se com vagas novas
  (`recolher_e_guardar(100, pagina)` vai buscar páginas mais antigas do ITJobs).
- **Escrever como se vai ler os resultados antes de os ver.** Um intervalo que toca o zero é "sem
  conclusão", e não "não funciona" nem "funciona".

## Limites

- Um só avaliador (eu), e poucas vagas: poucos `nao` e poucos `serve`.
- O score mede a **cobertura comprovada** do que o anúncio pede. A minha nota mistura o interesse e
  a vontade de aprender o que falta. As duas colunas do conjunto de teste correlacionam-se 0,70, por
  isso não se conseguem separar bem.
- Não se consegue reproduzir exatamente sem a base de dados com as mesmas vagas, porque o texto dos
  anúncios não está no repositório.
