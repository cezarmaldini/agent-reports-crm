-- Habilita pgvector
create extension if not exists vector;

-- Cria tabela de documentos vetoriais
create table reports_crm (
  id uuid primary key,
  content text,
  metadata jsonb,
  embedding vector(768) -- mesma dimensão do modelo usado
);

-- Índice para busca rápida
create index on reports_crm
using ivfflat (embedding vector_l2_ops) with (lists = 100);

-- Função de busca semântica
create or replace function match_reports_crm(
  query_embedding vector(768),
  match_count int default 3
)
returns table(id uuid, content text, metadata jsonb, similarity float)
language sql stable as $$
  select
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) as similarity
  from reports_crm
  where embedding is not null
  order by embedding <-> query_embedding
  limit match_count;
$$;
