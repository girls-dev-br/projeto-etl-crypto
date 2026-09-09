CREATE OR REPLACE VIEW public.vw_12_meses_com_projecao AS
WITH cotacoes_usd AS (
    SELECT 
        data_id,
        moeda_id,
        preco AS preco_usd,
        market_cap AS market_cap_usd,
        volume_total AS volume_total_usd
    FROM public.fato_cotacoes
    WHERE fiat_id = 'usd' AND preco > 0
),
cotacoes_brl AS (
    SELECT 
        data_id,
        moeda_id,
        preco AS preco_brl,
        market_cap AS market_cap_brl,
        volume_total AS volume_total_brl
    FROM public.fato_cotacoes
    WHERE fiat_id = 'brl' AND preco > 0
),
historico_12m AS (
    SELECT 
        u.data_id AS data_referencia,
        t.ano,
        t.mes,
        t.nome_mes,
        t.dia_semana,
        m.moeda_id,
        m.nome AS criptomoeda,
        m.simbolo AS simbolo,
        ROUND(u.preco_usd, 2) AS preco_usd,
        ROUND(b.preco_brl, 2) AS preco_brl,
        u.market_cap_usd,
        u.volume_total_usd,
        ROUND((b.preco_brl / NULLIF(u.preco_usd, 0)), 4) AS taxa_cambio_usd_brl,
        ROUND((((u.preco_usd - LAG(u.preco_usd) OVER (PARTITION BY u.moeda_id ORDER BY u.data_id)) / NULLIF(LAG(u.preco_usd) OVER (PARTITION BY u.moeda_id ORDER BY u.data_id), 0)) * 100), 2) AS variacao_percentual_diaria,
        ROUND(AVG(u.preco_usd) OVER (PARTITION BY u.moeda_id ORDER BY u.data_id ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS media_movel_7d_usd,
        'REAL' AS tipo_registro
    FROM cotacoes_usd u
    JOIN public.dim_moeda m ON u.moeda_id = m.moeda_id
    JOIN public.dim_tempo t ON u.data_id = t.data_id
    LEFT JOIN cotacoes_brl b ON u.data_id = b.data_id AND u.moeda_id = b.moeda_id
    WHERE u.data_id >= (SELECT MAX(data_id) - INTERVAL '12 months' FROM public.fato_cotacoes)
),
projecao_5d AS (
    SELECT 
        fp.data_projecao AS data_referencia,
        t.ano,
        t.mes,
        t.nome_mes,
        t.dia_semana,
        m.moeda_id,
        m.nome AS criptomoeda,
        m.simbolo AS simbolo,
        ROUND(fp.preco_projetado, 2) AS preco_usd,
        ROUND(fp.preco_projetado * 5.50, 2) AS preco_brl,
        NULL::NUMERIC(24, 2) AS market_cap_usd,
        NULL::NUMERIC(24, 2) AS volume_total_usd,
        5.5000::NUMERIC AS taxa_cambio_usd_brl,
        NULL::NUMERIC AS variacao_percentual_diaria,
        NULL::NUMERIC AS media_movel_7d_usd,
        'PROJECAO' AS tipo_registro
    FROM public.fato_projecoes fp
    JOIN public.dim_moeda m ON fp.moeda_id = m.moeda_id
    LEFT JOIN public.dim_tempo t ON fp.data_projecao = t.data_id
)
SELECT * FROM historico_12m
UNION ALL
SELECT * FROM projecao_5d;

CREATE OR REPLACE VIEW public.vw_projecoes_5_dias AS
SELECT 
    fp.data_projecao AS data_projetada,
    m.nome AS criptomoeda,
    m.simbolo AS simbolo,
    ROUND(fp.preco_projetado, 2) AS preco_usd,
    ROUND(fp.preco_projetado * 5.50, 2) AS preco_brl,
    '$ ' || TO_CHAR(ROUND(fp.preco_projetado, 2), 'FM999G999D00') AS preco_usd_formatado,
    'R$ ' || TO_CHAR(ROUND(fp.preco_projetado * 5.50, 2), 'FM999G999D00') AS preco_brl_formatado
FROM public.fato_projecoes fp
JOIN public.dim_moeda m ON fp.moeda_id = m.moeda_id;

CREATE OR REPLACE VIEW public.vw_analitica_resumo_mensal AS
SELECT 
    t.ano,
    t.mes,
    t.nome_mes,
    m.moeda_id,
    m.simbolo AS simbolo_moeda,
    ROUND(AVG(f_usd.preco), 4) AS preco_medio_usd,
    ROUND(MIN(f_usd.preco), 4) AS preco_min_usd,
    ROUND(MAX(f_usd.preco), 4) AS preco_max_usd,
    ROUND(SUM(f_usd.volume_total), 2) AS volume_total_usd,
    ROUND(AVG(f_brl.preco), 4) AS preco_medio_brl,
    ROUND(MIN(f_brl.preco), 4) AS preco_min_brl,
    ROUND(MAX(f_brl.preco), 4) AS preco_max_brl
FROM public.fato_cotacoes f_usd
JOIN public.dim_moeda m ON f_usd.moeda_id = m.moeda_id
JOIN public.dim_tempo t ON f_usd.data_id = t.data_id
LEFT JOIN public.fato_cotacoes f_brl 
    ON f_usd.data_id = f_brl.data_id 
   AND f_usd.moeda_id = f_brl.moeda_id 
   AND f_brl.fiat_id = 'brl'
WHERE f_usd.fiat_id = 'usd'
  AND f_usd.preco > 0
GROUP BY t.ano, t.mes, t.nome_mes, m.moeda_id, m.simbolo;

CREATE OR REPLACE VIEW public.vw_analitica_dia_semana AS
SELECT 
    t.dia_semana,
    m.nome AS criptomoeda,
    m.simbolo AS simbolo,
    ROUND(AVG(f.preco), 2) AS preco_medio_usd,
    ROUND(AVG(f.volume_total), 2) AS volume_medio_usd
FROM public.fato_cotacoes f
JOIN public.dim_moeda m ON f.moeda_id = m.moeda_id
JOIN public.dim_tempo t ON f.data_id = t.data_id
WHERE f.fiat_id = 'usd'
GROUP BY t.dia_semana, m.nome, m.simbolo;