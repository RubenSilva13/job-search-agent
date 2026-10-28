CREATE TABLE IF NOT EXISTS perfil (
    -- o CHECK obriga a que o id seja sempre 1: só pode existir uma linha
    id                INTEGER PRIMARY KEY CHECK (id = 1),
    nome              TEXT NOT NULL,
    localizacao       TEXT,
    disponibilidade   TEXT,
    resumo            TEXT
);


CREATE TABLE IF NOT EXISTS formacao (
    -- GENERATED ALWAYS AS IDENTITY: o PostgreSQL numera as linhas sozinho (1, 2, 3...)
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    curso             TEXT NOT NULL,
    instituicao       TEXT NOT NULL,
    grau              TEXT,
    ano_inicio        INTEGER,
    ano_fim           INTEGER,
    estado            TEXT NOT NULL CHECK (estado IN ('concluido', 'em_curso'))
);


CREATE TABLE IF NOT EXISTS linguas (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lingua            TEXT NOT NULL UNIQUE,
    nivel             TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS experiencia (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    funcao            TEXT NOT NULL,
    empresa           TEXT NOT NULL,
    ano_inicio        INTEGER,
    ano_fim           INTEGER,
    descricao         TEXT
);


CREATE TABLE IF NOT EXISTS competencias (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo              TEXT NOT NULL CHECK (tipo IN ('linguagem', 'ferramenta', 'soft_skill')),
    -- o nome e o nível ficam em colunas separadas: "Python" e "bom domínio"
    nome              TEXT NOT NULL,
    nivel             TEXT,
    -- a prova da competência, por exemplo a publicação numa soft skill
    evidencia         TEXT,
    -- não pode haver duas competências iguais do mesmo tipo
    UNIQUE (tipo, nome)
);


-- ---------------------------------------------------------------------------
-- AS VAGAS E O QUE SE FAZ COM ELAS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vagas (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titulo            TEXT NOT NULL,
    empresa           TEXT NOT NULL,
    localizacao       TEXT,
    -- o link é único: a mesma vaga não entra duas vezes
    url               TEXT NOT NULL UNIQUE,
    descricao         TEXT,
    -- de onde veio a vaga (por exemplo, 'manual' ou o nome da fonte)
    fonte             TEXT,
    encontrada_em     TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- O que o agente produz sobre uma vaga. Uma vaga pode ter várias análises,
-- por exemplo depois de atualizares o perfil.
CREATE TABLE IF NOT EXISTS analises (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- chave estrangeira: aponta para o id de uma vaga.
    -- ON DELETE CASCADE: se a vaga for apagada, as análises dela também são
    vaga_id           INTEGER NOT NULL REFERENCES vagas (id) ON DELETE CASCADE,
    score             INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    -- o relatório completo, tal como o Pydantic o devolve (JSON)
    relatorio         JSONB NOT NULL,
    criada_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- Uma decisão tua sobre uma vaga. O agente nunca se candidata sozinho.
CREATE TABLE IF NOT EXISTS candidaturas (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- UNIQUE: no máximo uma candidatura por vaga
    vaga_id           INTEGER NOT NULL UNIQUE REFERENCES vagas (id) ON DELETE CASCADE,
    estado            TEXT NOT NULL DEFAULT 'por_candidatar'
                      CHECK (estado IN ('por_candidatar', 'candidatado', 'entrevista',
                                        'oferta', 'recusada', 'desistiu')),
    data_candidatura  DATE,
    notas             TEXT
);
