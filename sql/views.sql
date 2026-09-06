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