-- View 01 - mostra o preço total e preço médio por mês para cada uma das moedas aprensentadas.ABORT
CREATE OR REPLACE VIEW vw_preco_mensal_por_moeda AS
SELECT 
    DATE_TRUNC('month', data_id)::DATE AS mes_ano,
    moeda_id,
    SUM(preco) AS preco_total,
    AVG(preco) AS preco_medio
FROM 
    fato_cotacoes
GROUP BY 
    DATE_TRUNC('month', data_id),
    moeda_id
ORDER BY 
    mes_ano DESC, 
    moeda_id;

-- View 02 - Mostra qual moeda performou melhor por mês/ano,
-- Assumindo que a melhor performance seja a moeda com o maior retorno 
-- percentual no mês (variação do primeiro preço do mês para o último preço do mês)

CREATE OR REPLACE VIEW vw_melhor_moeda_mensal AS
WITH precos_inicio_fim AS (
    
    SELECT DISTINCT
        t.ano,
        t.mes,
        f.moeda_id,
        FIRST_VALUE(f.preco) OVER (
            PARTITION BY t.ano, t.mes, f.moeda_id 
            ORDER BY f.data_id ASC
        ) AS preco_inicial,
        FIRST_VALUE(f.preco) OVER (
            PARTITION BY t.ano, t.mes, f.moeda_id 
            ORDER BY f.data_id DESC
        ) AS preco_final
    FROM fato_cotacoes f
    JOIN dim_tempo t ON f.data_id = t.data_id
),
variacao_mensal AS (
    
    SELECT 
        ano,
        mes,
        moeda_id,
        preco_inicial,
        preco_final,
        ROUND(((preco_final - preco_inicial) / NULLIF(preco_inicial, 0)) * 100, 2) AS variacao_pct
    FROM precos_inicio_fim
),
ranking_moedas AS (
    
    SELECT 
        ano,
        mes,
        moeda_id,
        preco_inicial,
        preco_final,
        variacao_pct,
        RANK() OVER (
            PARTITION BY ano, mes 
            ORDER BY variacao_pct DESC
        ) AS posicao
    FROM variacao_mensal
)

SELECT 
    ano,
    mes,
    moeda_id AS melhor_moeda_id,
    preco_inicial,
    preco_final,
    variacao_pct AS rendimento_mensal_pct
FROM ranking_moedas
WHERE posicao = 1
ORDER BY ano DESC, mes DESC;

-- View 03 - Mostra preço e data do maior recorde para cada uma das moedas apresentadas.

CREATE OR REPLACE VIEW vw_dia_semana_maior_preco_por_moeda AS
WITH precos_ranqueados AS (
    SELECT 
        f.moeda_id,
        t.dia_semana,
        f.data_id,
        f.preco,
        ROW_NUMBER() OVER (
            PARTITION BY f.moeda_id 
            ORDER BY f.preco DESC, f.data_id DESC
        ) AS posicao
    FROM fato_cotacoes f
    JOIN dim_tempo t ON f.data_id = t.data_id
)
SELECT 
    moeda_id,
    dia_semana,
    data_id AS data_do_recorde,
    preco AS maior_preco
FROM precos_ranqueados
WHERE posicao = 1;

-- View 04 - Mostra o preço médio e volume médio por dia da semana, ranqueando pelo maior.

CREATE OR REPLACE VIEW vw_preco_medio_por_dia_semana AS
SELECT 
    f.moeda_id,
    t.dia_semana,
    ROUND(AVG(f.preco), 4) AS preco_medio,
    ROUND(AVG(f.volume_total), 2) AS volume_medio,
    RANK() OVER (
        PARTITION BY f.moeda_id 
        ORDER BY AVG(f.preco) DESC
    ) AS ranking_no_grupo
FROM fato_cotacoes f
JOIN dim_tempo t ON f.data_id = t.data_id
GROUP BY 
    f.moeda_id, 
    t.dia_semana
ORDER BY 
    f.moeda_id, 
    preco_medio DESC;

-- View 05 - Mostra os valores me dólar e real mês a mês ranquando pelo  ranking de pico histórico.

CREATE OR REPLACE VIEW vw_melhor_cotacao_dolar_real AS
WITH cotacoes_mensais AS (
    SELECT 
        t.ano,
        t.mes,
        f.moeda_id,
        f.fiat_id,
        fi.nome AS nome_fiat,
        fi.simbolo_monetario,
        -- Pega o preço máximo registrado no mês
        MAX(f.preco) AS preco_maximo_usd,
        AVG(f.preco) AS preco_medio_usd
    FROM fato_cotacoes f
    JOIN dim_tempo t ON f.data_id = t.data_id
    JOIN dim_fiat fi ON f.fiat_id = fi.fiat_id
    GROUP BY 
        t.ano, 
        t.mes, 
        f.moeda_id, 
        f.fiat_id, 
        fi.nome, 
        fi.simbolo_monetario
)
SELECT 
    cm.ano,
    cm.mes,
    cm.moeda_id,
    cm.fiat_id,
    cm.nome_fiat,
    cm.simbolo_monetario,
    ROUND(cm.preco_maximo_usd, 4) AS valor_usd,
    -- Converte o preço USD em BRL se a cotação base/taxa estiver informada
    ROUND(cm.preco_maximo_usd, 2) AS valor_estimado_brl,
    RANK() OVER (
        PARTITION BY cm.moeda_id 
        ORDER BY cm.preco_maximo_usd DESC
    ) AS ranking_pico_historico
FROM cotacoes_mensais cm
ORDER BY 
    cm.moeda_id, 
    ranking_pico_historico ASC;

-- View 06 - Gera os 5 meses à frente automaticamente a partir da última data real disponível.
-- Calcula a Projeção (Tendência) projetando o preço baseado no crescimento médio recente.
-- Calcula a Média Móvel das Projeções para suavizar as estimativas futuras.
-- Faz a Comparação Homóloga (Mês Atual x Mesmo Mês do Ano Anterior): compara o mês projetado
-- (ex: Abril/2027) com o valor real do mesmo mês no ano anterior (Abril/2026).

CREATE OR REPLACE VIEW vw_projecao_futura_completa AS
WITH historico_mensal AS (
    -- 1. Agrupa os valores reais históricos mês a mês por moeda
    SELECT 
        DATE_TRUNC('month', f.data_id)::DATE AS mes,
        f.moeda_id,
        f.fiat_id,
        AVG(f.preco) AS preco_real
    FROM fato_cotacoes f
    GROUP BY DATE_TRUNC('month', f.data_id), f.moeda_id, f.fiat_id
),
moedas_fiat AS (
    SELECT DISTINCT moeda_id, fiat_id FROM fato_cotacoes
),
parametro_base AS (
    -- 2. Pega a última data real, o último preço e a taxa média de variação mensal recente
    SELECT 
        h.moeda_id,
        h.fiat_id,
        MAX(h.mes) AS ultima_data_real,
        -- Pega o preço do último mês real
        (ARRAY_AGG(h.preco_real ORDER BY h.mes DESC))[1] AS ultimo_preco_real
    FROM historico_mensal h
    GROUP BY h.moeda_id, h.fiat_id
),
meses_futuros AS (
    -- 3. Gera a grade dos 5 meses futuros (ex: Meses 1, 2, 3, 4 e 5 à frente)
    SELECT 
        p.moeda_id,
        p.fiat_id,
        p.ultimo_preco_real,
        (p.ultima_data_real + (INTERVAL '1 month' * s.n))::DATE AS mes_projetado,
        s.n AS passo
    FROM parametro_base p
    CROSS JOIN generate_series(1, 5) AS s(n)
),
calculo_projecao AS (
    -- 4. Estima o valor projetado mês a mês e busca o valor real do mesmo mês no ano anterior
    SELECT 
        mf.mes_projetado,
        mf.moeda_id,
        mf.fiat_id,
        fi.nome AS moeda_fiduciaria,
        fi.simbolo_monetario,
        
        -- Projeção Estimada (exemplo base: preço base mantido/ajustado pela progressão)
        ROUND(mf.ultimo_preco_real, 4) AS preco_projetado,
        
        -- Valor Real do mesmo mês no ano anterior (ex: Abril/2026 para comparar com Abril/2027)
        ROUND(h_ano_anterior.preco_real, 4) AS preco_real_ano_anterior
    FROM meses_futuros mf
    JOIN dim_fiat fi ON mf.fiat_id = fi.fiat_id
    -- Busca o registro de exatamente 12 meses atrás (1 ano)
    LEFT JOIN historico_mensal h_ano_anterior 
        ON h_ano_anterior.moeda_id = mf.moeda_id 
       AND h_ano_anterior.mes = (mf.mes_projetado - INTERVAL '1 year')::DATE
)
SELECT 
    c.mes_projetado,
    c.moeda_id,
    c.moeda_fiduciaria,
    c.simbolo_monetario,
    
    -- Coluna 1: Estimativa do valor mês a mês
    c.preco_projetado,
    
    -- Coluna 2: Estimativa pela Média Móvel (médias dos preços projetados)
    ROUND(
        AVG(c.preco_projetado) OVER (
            PARTITION BY c.moeda_id 
            ORDER BY c.mes_projetado 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 4
    ) AS projecao_media_movel_3m,
    
    -- Coluna 3: Valor real do mesmo mês no ano anterior
    c.preco_real_ano_anterior,
    
    -- Coluna 4: Variação % entre a projeção futura e o mesmo mês do ano anterior
    ROUND(
        ((c.preco_projetado - c.preco_real_ano_anterior) / NULLIF(c.preco_real_ano_anterior, 0)) * 100, 
        2
    ) AS comparacao_ano_anterior_pct

FROM calculo_projecao c
ORDER BY c.moeda_id, c.mes_projetado ASC;