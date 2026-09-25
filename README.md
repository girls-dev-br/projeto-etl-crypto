# 🪙 Pipeline de ETL & Analytics de Criptomoedas

Pipeline completo de Engenharia e Business Analytics (Extract, Transform, Load) que extrai dados históricos de criptoativos via API, realiza o tratamento e modelagem dimensional em um banco de dados relacional e entrega insights estratégicos em um painel interativo no Power BI.

---

## 📊 Business Intelligence & Dashboard Interativo (Power BI)

A camada analítica do projeto foi estruturada no **Microsoft Power BI**, consumindo diretamente as views modeladas no banco de dados analítico. O painel foi concebido para atender tanto à análise tática quanto à tomada de decisão operacional sobre o mercado de criptoativos, com foco principal em **Bitcoin (BTC)** e **Ethereum (ETH)**.

---

### 🧠 Modelagem Semântica e Relacionamentos

Para garantir integridade analítica e evitar a necessidade de filtros redundantes na interface, o modelo semântico foi consolidado conectando as views analíticas em formato de estrela/floco adaptado:

* **Tabela Central de Cotações:** `vw_12_meses_com_projecao` atua como hub relacional primário para as séries temporais.
* **Propagação de Filtro Bidirecional:** Relações com cardinalidade muitos-para-muitos (`*:*`) e filtro cruzado bidirecional ativo conectam as tabelas auxiliares (`vw_analitica_dia_semana`, `vw_analitica_resumo_mensal` e `vw_projecoes_5_dias`).
* **Sincronismo Global:** Um seletor de ativo unificado comanda instantaneamente todos os visuais da página (preços, projeções, ranges e volatilidade).

---

### 🖥️ Estrutura e Métricas do Painel

O dashboard está organizado em quatro quadrantes de análise contínua:

#### 1. Cabeçalho Executivo e KPIs de Topo
* **Seletor de Moeda:** Alternância rápida entre **Bitcoin** e **Ethereum**.
* **Preço Médio BRL / USD:** Cartões de destaque que consolidam o preço médio registrado no período, permitindo a leitura instantânea tanto no contexto nacional (conversão cambial) quanto internacional (dólar).
* **Navegador de Moedas (Alternância Dinâmica):** Mecanismo via Bookmarks que permite alternar os gráficos entre as unidades monetárias (BRL) e (USD) de forma limpa e sem duplicar páginas.

#### 2. Tendência Histórica & Análise Técnica
* **Cotação Histórica Diária:** Curva de preços contínua cobrindo o histórico de negociação de 12 meses.
* **Médias Móveis e Tendência:** Linha temporal com sobreposição de preço diário, fornecendo sinalização de tendências e atenuação de ruídos de curto prazo.
* **Projeção Preditiva (5 Dias):** Gráfico de linha suavizado com preenchimento em degradê, alimentado pela view `vw_projecoes_5_dias`, apresentando a estimativa de preço para as datas subsequentes.

#### 3. Padrões de Mercado & Sazonalidade
* **Média por Dia da Semana:** Gráfico de colunas clusterizadas categorizado por dia da semana (`dia_semana`), isolando o comportamento de liquidez e precificação nos dias úteis vs. finais de semana.
* **Banda de Preço (Range Histórico Mín/Máx):** Análise de volatilidade mensal comparando as colunas `preco_min` e `preco_max` para mapear os tetos e pisos históricos de suporte e resistência do ativo.

#### 4. Indicadores de Risco e Liquidez
* **Índice de Liquidez:** Medidor em rosca baseado no volume total acumulado/médio negociado (`volume_total_usd`).
* **Volatilidade Diária:** Identificação de picos de estresse no ativo através da distribuição da variação percentual diária (`variacao_percentual_diaria`).

---

![Dashboard Crypto](https://githubusercontent.com)

---

## 🎯 2. Escopo do Projeto & Solução de Negócio
O objetivo principal deste projeto é monitorar e prospectar o comportamento dos dois principais criptoativos do mercado global: **Bitcoin (BTC)** e **Ethereum (ETH)**. 

A solução resolve o problema de consolidação de dados fragmentados, centralizando históricos e projeções em uma única base de dados estruturada para análise macroeconômica e tomada de decisão corporativa utilizando a moeda padrão internacional (**Dólar Americano - USD**).

## 🛠️ 3. Tecnologias Utilizadas
* **Linguagem Principal:** Python 3 (Scripts de automação)
* **Manipulação de Dados:** Pandas
* **Carga e ORM:** SQLAlchemy
* **Fonte de Dados:** CoinGecko API (Dados públicos de mercado)
* **Banco de Dados (Data Warehouse):** PostgreSQL hospedado em nuvem (NeonDB)
* **Business Intelligence:** Power BI Desktop (Modelagem e UX/UI)

## 🗃️ 4. Modelagem do Banco & Camada Semântica (Views SQL)
Para alimentar o dashboard de forma otimizada e performática, o modelo de BI consome dados refinados diretamente de 5 Views SQL estratégicas criadas no banco de dados:

1. `public.vw_12_meses_com_projecao`: Consolida o histórico temporal das cotações de fechamento diário do último ano.
2. `public.vw_analitica_dia_semana`: Calcula o preço médio e volume médio negociado por cada dia da semana para identificar padrões de volatilidade.
3. `public.vw_projecoes_5_dias`: Armazena os cálculos matemáticos de tendência futura para o curto prazo.
4. `public.vw_fato_cotacoes_analitica`: Tabela fato principal do modelo com métricas de volume spot e capitalização de mercado (Market Cap).
5. `public.vw_analitica_resumo_mensal`: Agrupa os fechamentos consolidados por mês e ano (Média, Máxima e Mínima histórica).


## Estrutura do projeto
```
projeto-etl-crypto/
├── sql/            # scripts de criação de tabelas e views
├── src/            # código fonte do ETL
├── tests/          # testes automatizados
├── docs/           # documentação adicional
├── config/         # configurações do projeto
├── requirements.txt
└── .env.exemplo    # modelo de variáveis de ambiente
```

## Como rodar o projeto

1. Clone o repositório
```bash
git clone https://github.com/girls-dev-br/projeto-etl-crypto.git
cd projeto-etl-crypto
```

2. Crie e ative o ambiente virtual
```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
```

3. Instale as dependências
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente
```bash
cp .env.exemplo .env
# preencha o .env com suas próprias credenciais
```

5. Execute o projeto
```bash
python src/main.py
```

## 📸 Demonstração

O pipeline foi validado em ambiente de desenvolvimento, cobrindo desde a coleta bruta até a estruturação analítica final.

### 1. Extração e Carga Incremental (Staging)
* **Processamento Bruto:** Coleta automatizada de dados históricos diretamente da API CoinGecko para a tabela `stg_cotacoes`.
![Extração Bruta](./docs/fotos-processo/extracao_bruta.jpeg)

* **Automação de Carga:** Script executado via agendador de tarefas garantindo a carga incremental dos últimos 12 meses mais projeções.
![Extração Automatizada](./docs/fotos-processo/extracao_auto.jpeg)

### 2. Camada Semântica & Modelagem Relacional
Para alimentar o ambiente do Power BI, o banco consome os dados transformados por meio das 5 views estruturadas:
* `public.vw_12_meses_com_projecao`
* `public.vw_analitica_dia_semana`
* `public.vw_projecoes_5_dias`
* `public.vw_fato_cotacoes_analitica`
* `public.vw_analitica_resumo_mensal`

### 3. Execução do Pipeline ETL

![Execução do Pipeline ETL](docs/fotos-processo/Pipeline.jpeg)

*Registo de logs do terminal demonstrando o fluxo completo de dados:*
- **Extração:** Verificação de carga incremental e validação de dados recentes da API.
- **Transformação:** Aplicação de regras de negócio, validação de 1.548 registos e ausência de falhas na camada *stage*.
- **Carga (Load):** Povoamento com sucesso do esquema em estrela (`dim_fiat`, `dim_moeda`, `dim_tempo` e `fato_cotacoes`) no Neon PostgreSQL.
---

## 👩‍💻 Autoras

Unimos nossas habilidades para construir esta solução de ponta a ponta. Conecte-se conosco:

### 👥 Autorasi

### 👥 Autorasi

| Autora | LinkedIn | GitHub |
| :--- | :---: | :---: |
| **Paula Carvalho** | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/paula-carvalho-390147108/) | [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/paulahcarvalho) |
| **Bianca Pena** | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com) | [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/BiaPena-br) |
| **Sara Trindade** | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sara0333/) | [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/saradataeng) |
| **Paula Cristine** | `-` | [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/paulinhacelebrai) |
