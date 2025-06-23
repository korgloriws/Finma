import sqlite3
import pandas as pd
import yfinance as yf
from datetime import date, datetime
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table  
import plotly.express as px
from dash_table.Format import Format, Symbol
from complete_b3_logos_mapping import add_logo_column_to_data, get_table_columns_with_logo

def init_db():
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carteira (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            nome_completo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_atual REAL NOT NULL,
            valor_total REAL NOT NULL,
            data_adicao TEXT NOT NULL,
            tipo TEXT DEFAULT 'Desconhecido',
            dy REAL,
            pl REAL,
            pvp REAL,
            roe REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_carteira (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            valor_total REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            ticker TEXT NOT NULL,
            nome_completo TEXT,
            quantidade REAL NOT NULL,
            preco REAL NOT NULL,
            tipo TEXT NOT NULL -- 'compra' ou 'venda'
        )
    ''')
    conn.commit()
    conn.close()


init_db()

def obter_cotacao_dolar():
    try:
        cotacao = yf.Ticker("BRL=X").info.get("regularMarketPrice")
        return cotacao if cotacao else 5.0
    except:
        return 5.0



cotacao_global_brl = obter_cotacao_dolar()

def obter_informacoes_ativo(ticker):
    try:
        acao = yf.Ticker(ticker)
        info = acao.info
        preco_atual = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")

        tipo_map = {
            "EQUITY": "Ação",
            "ETF": "FII",
            "CRYPTOCURRENCY": "Criptomoeda",
        }
        tipo_raw = info.get("quoteType", "Desconhecido")
        tipo = tipo_map.get(tipo_raw, "Desconhecido")

        if preco_atual is None:
            return None

        if tipo == "Criptomoeda":
            preco_atual *= cotacao_global_brl

        return {
            "ticker": ticker.upper(),
            "nome_completo": info.get("longName", "Desconhecido"),
            "preco_atual": preco_atual,
            "tipo": tipo,
            "pl": info.get("trailingPE"),
            "pvp": info.get("priceToBook"),
            "dy": info.get("dividendYield"),
            "roe": info.get("returnOnEquity"),
        }
    except Exception as e:
        print(f"Erro ao obter informações de {ticker}: {e}")
        return None


def adicionar_ou_atualizar_ativo(ticker, nome_completo, quantidade, preco_atual, tipo, dy, pl, pvp, roe):
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT id, quantidade FROM carteira WHERE ticker = ?", (ticker,))
    existente = cursor.fetchone()

    if existente:
        id_existente, qtd_existente = existente
        nova_qtd = qtd_existente + quantidade
        novo_valor_total = nova_qtd * preco_atual
        cursor.execute("""
            UPDATE carteira
            SET quantidade = ?, preco_atual = ?, valor_total = ?, tipo = ?,
                dy = ?, pl = ?, pvp = ?, roe = ?
            WHERE id = ?
        """, (nova_qtd, preco_atual, novo_valor_total, tipo,
              dy, pl, pvp, roe, id_existente))
    else:
        valor_total = preco_atual * quantidade
        cursor.execute("""
            INSERT INTO carteira 
                (ticker, nome_completo, quantidade, preco_atual, valor_total, 
                 data_adicao, tipo, dy, pl, pvp, roe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ticker, nome_completo, quantidade, preco_atual, valor_total,
              date.today(), tipo, dy, pl, pvp, roe))

    conn.commit()
    conn.close()
    salvar_historico()

    registrar_movimentacao(
        data=date.today().isoformat(),
        ticker=ticker,
        nome_completo=nome_completo,
        quantidade=quantidade,
        preco=preco_atual,
        tipo='compra'
    )



def atualizar_ativo(id, quantidade):
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT preco_atual FROM carteira WHERE id = ?", (id,))
    preco_atual = cursor.fetchone()[0]
    valor_total = preco_atual * quantidade
    cursor.execute("UPDATE carteira SET quantidade = ?, valor_total = ? WHERE id = ?", (quantidade, valor_total, id))
    conn.commit()
    conn.close()
    salvar_historico()


def remover_ativo(id):
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT ticker, nome_completo, quantidade, preco_atual FROM carteira WHERE id = ?", (id,))
    ativo = cursor.fetchone()
    if ativo:
        ticker, nome_completo, quantidade, preco_atual = ativo
    else:
        ticker = nome_completo = quantidade = preco_atual = None
    cursor.execute("DELETE FROM carteira WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    salvar_historico()

    if ativo:
        registrar_movimentacao(
            data=date.today().isoformat(),
            ticker=ticker,
            nome_completo=nome_completo,
            quantidade=quantidade,
            preco=preco_atual,
            tipo='venda'
        )


def consultar_carteira():
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM carteira", conn)
    conn.close()

 

    return df.to_dict("records")



def salvar_historico():
    df = pd.DataFrame(consultar_carteira())
    valor_total = df['valor_total'].sum() if not df.empty else 0
    data_hoje = date.today().isoformat()

    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historico_carteira WHERE data = ?", (data_hoje,))
    existe = cursor.fetchone()
    if existe:
        cursor.execute("UPDATE historico_carteira SET valor_total = ? WHERE data = ?", (valor_total, data_hoje))
    else:
        cursor.execute("INSERT INTO historico_carteira (data, valor_total) VALUES (?, ?)", (data_hoje, valor_total))
    conn.commit()
    conn.close()


def consultar_historico(periodo):
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM historico_carteira", conn)
    conn.close()
    df['data'] = pd.to_datetime(df['data'])

    hoje = pd.to_datetime(date.today())
    if periodo == 'semanal':
        inicio = hoje - pd.DateOffset(weeks=1)
    elif periodo == 'mensal':
        inicio = hoje - pd.DateOffset(months=1)
    elif periodo == 'semestral':
        inicio = hoje - pd.DateOffset(months=6)
    elif periodo == 'anual':
        inicio = hoje - pd.DateOffset(years=1)
    else:
        # Default: mostrar tudo
        inicio = df['data'].min() if not df.empty else hoje

    return df[df['data'] >= inicio]

def editar_tipo(id, novo_tipo):
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE carteira SET tipo = ? WHERE id = ?", (novo_tipo, id))
    conn.commit()
    conn.close()




def layout():
    return dbc.Container([
        html.H3("Carteira de Investimentos", className="text-center my-4"),
        dcc.Store(id="carteira-ocultar-valor", data={"oculto": True}),
        dbc.Tabs(
            id="carteira-tabs",
            active_tab="carteira-aba-ativos",
            children=[
                dbc.Tab(label="📋 Ativos", tab_id="carteira-aba-ativos"),
                dbc.Tab(label="📈 Gráficos", tab_id="carteira-aba-graficos"),
                dbc.Tab(label="💰 Proventos", tab_id="carteira-aba-proventos"),
                dbc.Tab(label="🤖 Insights", tab_id="carteira-aba-ia"),
                dbc.Tab(label="🔄 Movimentações", tab_id="carteira-aba-movimentacoes"),
            ]
        ),
        dcc.Interval(id="carteira-atualizador", interval=3000, n_intervals=0),
        html.Div(id="carteira-conteudo")
    ], fluid=True)

def registrar_callbacks(app):
    from pages.ia import gerar_insights

    @app.callback(
        Output("carteira-conteudo", "children"),
        [Input("carteira-tabs", "active_tab"), Input("switch-darkmode", "value")]
    )
    def carteira_renderizar_abas(aba, is_dark):
        style_header_dark = {
            'backgroundColor': '#202124',
            'color': '#E4E6EB',
            'border': '1px solid #3A3B3C'
        }
        style_data_dark = {
            'backgroundColor': '#242526',
            'color': '#E4E6EB',
            'border': '1px solid #3A3B3C'
        }
        style_header_light = {
            'backgroundColor': '#f8f9fa',
            'color': '#222',
            'border': '1px solid #dee2e6'
        }
        style_data_light = {
            'backgroundColor': '#fff',
            'color': '#222',
            'border': '1px solid #dee2e6'
        }
        style_header = style_header_dark if is_dark else style_header_light
        style_data = style_data_dark if is_dark else style_data_light
        if aba == "carteira-aba-ativos":
            tipos_ativos = ['Ação', 'FII', 'Criptomoeda', 'BDR', 'Fixa']
            df_carteira = pd.DataFrame(consultar_carteira())
            accordions = []
            for tipo in tipos_ativos:
                df_tipo = df_carteira[df_carteira['tipo'] == tipo] if not df_carteira.empty else pd.DataFrame()
                total_tipo = df_tipo['valor_total'].sum() if not df_tipo.empty else 0
                
                # Processa dados com logos
                data_with_logos = []
                if not df_tipo.empty:
                    data_with_logos = add_logo_column_to_data(df_tipo.to_dict('records'))
                
                # Define colunas com logo
                base_columns = [
                    {'name': 'Ticker', 'id': 'ticker', 'presentation': 'markdown'},
                    {'name': 'Nome Completo', 'id': 'nome_completo'},
                    {'name': 'Quantidade', 'id': 'quantidade', 'editable': True},
                    {'name': 'Preço Atual', 'id': 'preco_atual'},
                    {'name': 'Valor Total', 'id': 'valor_total'},
                    {'name': 'DY', 'id': 'dy'},
                    {'name': 'P/L', 'id': 'pl'},
                    {'name': 'P/VP', 'id': 'pvp'},
                    {'name': 'ROE', 'id': 'roe'},
                    {'name': 'Tipo', 'id': 'tipo', 'editable': True}
                ]
                columns_with_logo = get_table_columns_with_logo(base_columns)
                
                tabela = dash_table.DataTable(
                    id=f'tabela-carteira-{tipo.lower()}',
                    columns=columns_with_logo,
                    data=data_with_logos,
                    editable=True,
                    row_deletable=True,
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    style_header=style_header,
                    style_data=style_data,
                    markdown_options={"html": True}
                )
                accordions.append(
                    dbc.AccordionItem(
                        tabela,
                        title=f"{tipo} - Total: R$ {total_tipo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    )
                )
            return html.Div([
                html.H4("Gerenciamento de Ativos", className="mb-2 text-center"),
                html.H5(id="carteira-valor-total", className="text-success text-center mb-3"),
                dbc.Row([
                    dbc.Col(dcc.Input(id='carteira-input-ticker', type='text', placeholder='Ticker...', className='form-control'), xs=12, sm=6, md=4),
                    dbc.Col(dcc.Input(id='carteira-input-quantidade', type='number', placeholder='Quantidade', className='form-control'), xs=12, sm=6, md=4),
                    dbc.Col(html.Button('Adicionar', id='carteira-botao-adicionar', className='btn btn-primary w-100'), xs=12, sm=12, md=4),
                ], className="mb-4"),
                html.Div(id='carteira-mensagem-status', className='text-danger mt-2 text-center'),
                dbc.Accordion(accordions, always_open=True, id="carteira-lista-ativos")
            ])

        elif aba == "carteira-aba-graficos":
            return html.Div([
                html.Label("Período:"),
                dcc.Dropdown(
                    id="carteira-filtro-periodo",
                    options=[
                        {"label": "Semanal", "value": "semanal"},
                        {"label": "Mensal", "value": "mensal"},
                        {"label": "Semestral", "value": "semestral"},
                        {"label": "Anual", "value": "anual"},
                    ],
                    value="mensal",
                    clearable=False,
                    style={"width": "300px"}
                ),
                dcc.Graph(id="grafico-evolucao"),
                dcc.Graph(id="grafico-por-tipo"),
                dcc.Graph(id="grafico-por-ativo"),
                dcc.Graph(id="grafico-top-posicoes"),
                dcc.Graph(id="grafico-positivo-negativo"),
            ])

        elif aba == "carteira-aba-ia":
            try:
                print("[DEBUG] Renderizando aba de insights...")
                insights = gerar_insights() or ["Nenhum insight disponível."]

                principais = []
                secundarios = []
                for item in insights:
                    if any(x in item for x in ["variou", "concentrada", "maior posição"]):
                        principais.append(item)
                    else:
                        secundarios.append(item)

                cards_principais = [
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="bi bi-bar-chart-line-fill me-2", style={"fontSize": "2.2rem", "color": "#0d6efd"}),
                                    html.Span(item, style={"fontSize": "1.25rem", "fontWeight": 600, "color": "#222"})
                                ], className="d-flex align-items-center"),
                            ]),
                            style={
                                "background": "#fff",
                                "borderRadius": "18px",
                                "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
                                "minHeight": "110px",
                                "border": "1px solid #e9ecef",
                                "marginBottom": "8px",
                            },
                            className="h-100 animate__animated animate__fadeInUp"
                        ),
                        style={"gridColumn": "span 2", "padding": "8px"},
                        className="insight-card-col"
                    ) for item in principais
                ]

                cards_secundarios = [
                    html.Div(
                        dbc.Card(
                            dbc.CardBody([
                                html.I(className="bi bi-info-circle me-2", style={"fontSize": "1.2rem", "color": "#6c757d"}),
                                html.Span(item, style={"fontSize": "1.05rem", "color": "#444"})
                            ]),
                            style={
                                "background": "#f8f9fa",
                                "borderRadius": "14px",
                                "boxShadow": "0 1px 6px rgba(0,0,0,0.04)",
                                "minHeight": "60px",
                                "border": "1px solid #e9ecef",
                            },
                            className="h-100 animate__animated animate__fadeIn"
                        ),
                        style={"padding": "8px"},
                        className="insight-card-col"
                    ) for item in secundarios
                ]
                grid = html.Div(
                    cards_principais + cards_secundarios if (cards_principais or cards_secundarios) else [html.Div("Nenhum insight disponível.", className="text-center text-muted p-4")],
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(270px, 1fr))",
                        "gap": "8px",
                        "marginTop": "18px",
                        "marginBottom": "18px",
                        "alignItems": "stretch",
                    },
                    className="insights-masonry"
                )
                return html.Div([
                    html.H4("📊 Insights com IA", className="mb-4 text-center"),
                    grid,
                    dcc.Markdown("""
<style>
.insights-masonry { align-items: stretch; }
.insight-card-col:hover .card {
    transform: scale(1.03) translateY(-2px);
    box-shadow: 0 6px 24px rgba(13,110,253,0.09);
}
.insight-card-col .card {
    animation: fadeInUp 0.7s;
    transition: box-shadow 0.2s, transform 0.2s;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", dangerously_allow_html=True)
                ])
            except Exception as e:
                print(f"[ERRO] Falha ao renderizar insights: {e}")
                return html.Div([
                    html.H4("Erro ao carregar insights", className="text-danger text-center my-4"),
                    html.Pre(str(e), className="text-center text-muted")
                ])

        elif aba == "carteira-aba-movimentacoes":
            meses = [
                'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
            ]
            return html.Div([
                html.H4("Movimentações da Carteira", className="mb-4 text-center"),
                dbc.Row([
                    dbc.Col([
                        dcc.Dropdown(
                            id='movimentacoes-filtro-mes',
                            options=[{'label': mes, 'value': str(i+1).zfill(2)} for i, mes in enumerate(meses)],
                            placeholder="Selecione o mês",
                            style={"margin-bottom": "10px"}
                        ),
                    ], md=4),
                    dbc.Col([
                        dcc.Input(
                            id='movimentacoes-filtro-ano',
                            type='number',
                            placeholder='Ano',
                            value=date.today().year,
                            className="form-control"
                        )
                    ], md=4),
                ], className="mb-3"),
                dash_table.DataTable(
                    id='tabela-movimentacoes',
                    columns=[
                        {'name': 'Data', 'id': 'data'},
                        {'name': 'Ticker', 'id': 'ticker', 'presentation': 'markdown'},
                        {'name': 'Nome Completo', 'id': 'nome_completo'},
                        {'name': 'Quantidade', 'id': 'quantidade'},
                        {'name': 'Preço', 'id': 'preco'},
                        {'name': 'Tipo', 'id': 'tipo'},
                    ],
                    data=[],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    markdown_options={"html": True}
                ),
            ])

        elif aba == "carteira-aba-proventos":
            # --- Lógica de cálculo dos proventos ---
            df_carteira = pd.DataFrame(consultar_carteira())
            if df_carteira.empty:
                return html.Div([
                    html.H4("💰 Proventos Recebidos e Projetados", className="mb-4 text-center"),
                    html.Div("Nenhum ativo na carteira.", className="text-center text-muted")
                ])
            # Dropdown de período
            periodos = [
                {"label": "6 meses", "value": "6m"},
                {"label": "1 ano", "value": "1y"},
                {"label": "5 anos", "value": "5y"},
                {"label": "10 anos", "value": "10y"},
                {"label": "Tudo", "value": "all"},
            ]
            # Valor padrão: 1 ano
            periodo_selecionado = '1y'
            import dash
            ctx = dash.callback_context if hasattr(dash, 'callback_context') else None
            if ctx and ctx.triggered and ctx.triggered[0]['prop_id'].startswith('carteira-proventos-periodo'):
                periodo_selecionado = ctx.triggered[0]['value']
            # Dropdown
            dropdown_periodo = dcc.Dropdown(
                id='carteira-proventos-periodo',
                options=periodos,
                value=periodo_selecionado,
                clearable=False,
                style={"width": "220px", "marginBottom": "18px"}
            )
            proventos_todos = []
            for _, row in df_carteira.iterrows():
                ticker = row['ticker']
                nome = row['nome_completo']
                qtd = row['quantidade']
                try:
                    yf_ticker = yf.Ticker(ticker)
                    dividends = yf_ticker.dividends
                    if dividends.empty:
                        continue
                    df_div = dividends.reset_index()
                    df_div.columns = ['data', 'valor_por_acao']
                    df_div['ticker'] = ticker
                    df_div['nome_completo'] = nome
                    df_div['recebido'] = df_div['valor_por_acao'] * qtd
                    df_div['ano_mes'] = df_div['data'].dt.to_period('M').astype(str)
                    proventos_todos.append(df_div)
                except Exception as e:
                    print(f"[Proventos] Erro ao buscar {ticker}: {e}")
            if not proventos_todos:
                return html.Div([
                    html.H4("💰 Proventos Recebidos e Projetados", className="mb-4 text-center"),
                    dropdown_periodo,
                    html.Div("Nenhum provento encontrado para os ativos da carteira.", className="text-center text-muted")
                ])
            df_proventos = pd.concat(proventos_todos, ignore_index=True)
            df_proventos['data'] = df_proventos['data'].dt.tz_localize(None)  # Remover timezone
            # --- FILTRO DE PERÍODO ---
            hoje = pd.Timestamp.today()
            if periodo_selecionado == '6m':
                inicio = hoje - pd.DateOffset(months=6)
            elif periodo_selecionado == '1y':
                inicio = hoje - pd.DateOffset(years=1)
            elif periodo_selecionado == '5y':
                inicio = hoje - pd.DateOffset(years=5)
            elif periodo_selecionado == '10y':
                inicio = hoje - pd.DateOffset(years=10)
            else:
                inicio = df_proventos['data'].min()
            df_proventos = df_proventos[df_proventos['data'] >= inicio]
            # Agrupar por mês e ativo
            resumo_mes_ativo = df_proventos.groupby(['ano_mes', 'ticker', 'nome_completo'])['recebido'].sum().reset_index()
            resumo_mes = df_proventos.groupby('ano_mes')['recebido'].sum().reset_index()
            # Projeção: média do período filtrado por ativo
            projecao = df_proventos.groupby('ticker')['recebido'].mean().reset_index()
            projecao = projecao.merge(df_carteira[['ticker', 'nome_completo']], on='ticker', how='left')
            projecao['projecao_periodo'] = projecao['recebido']
            # --- Visualização ---
            # Processa dados com logos para a tabela de proventos
            data_proventos_with_logos = add_logo_column_to_data(resumo_mes_ativo.to_dict('records'))
            
            tabela = dash_table.DataTable(
                columns=[
                    {"name": "Mês", "id": "ano_mes"},
                    {"name": "Ticker", "id": "ticker", "presentation": "markdown"},
                    {"name": "Nome", "id": "nome_completo"},
                    {"name": "Recebido (R$)", "id": "recebido", "type": "numeric", "format": Format(precision=2, scheme='f', symbol=Symbol.yes, symbol_prefix='R$ ')}
                ],
                data=data_proventos_with_logos,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                page_size=20,
                markdown_options={"html": True}
            )
            grafico = px.bar(resumo_mes, x='ano_mes', y='recebido', title='Proventos Recebidos por Mês', labels={'ano_mes': 'Mês', 'recebido': 'Recebido (R$)'}, template='plotly_dark' if is_dark else 'simple_white')
            
            # Processa dados com logos para a tabela de projeção
            data_projecao_with_logos = add_logo_column_to_data(projecao.to_dict('records'))
            
            tabela_proj = dash_table.DataTable(
                columns=[
                    {"name": "Ticker", "id": "ticker", "presentation": "markdown"},
                    {"name": "Nome", "id": "nome_completo"},
                    {"name": "Projeção Mensal (R$)", "id": "projecao_periodo", "type": "numeric", "format": Format(precision=2, scheme='f', symbol=Symbol.yes, symbol_prefix='R$ ')}
                ],
                data=data_projecao_with_logos,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                page_size=20,
                markdown_options={"html": True}
            )
            return html.Div([
                html.H4("💰 Proventos Recebidos e Projetados", className="mb-4 text-center"),
                html.Div([
                    html.Label("Período dos Proventos:", className="fw-bold me-2"),
                    dropdown_periodo
                ], className="mb-3 d-flex align-items-center justify-content-center"),
                html.H5("Histórico de Proventos por Mês e Ativo", className="mb-3 mt-2"),
                tabela,
                dcc.Graph(figure=grafico, className="my-4"),
                html.H5("Projeção de Proventos Mensais (Média do período)", className="mb-3 mt-4"),
                tabela_proj
            ])





    @app.callback(
        Output("carteira-valor-total", "children"),
        Input("carteira-tabs", "active_tab"),
        Input("carteira-ocultar-valor", "data")
    )
    def carteira_atualizar_total_geral(_, store):
        df = pd.DataFrame(consultar_carteira())
        total = df['valor_total'].sum() if not df.empty else 0
        oculto = store.get("oculto", True) if store else True
        valor = "•••••••" if oculto else f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        icone = "👁" if oculto else "🔒"
        return html.Span([
            f"\U0001f4b0 Total da Carteira: ",
            html.Span(valor, id="carteira-valor-span", className="fw-bold"),
            html.Button(icone, id="carteira-botao-ocultar", n_clicks=0, style={"border": "none", "background": "none", "marginLeft": "10px", "fontSize": "1.3rem", "cursor": "pointer", "verticalAlign": "middle"})
        ])

    @app.callback(
        Output("carteira-ocultar-valor", "data"),
        Input("carteira-botao-ocultar", "n_clicks"),
        State("carteira-ocultar-valor", "data"),
        prevent_initial_call=True
    )
    def alternar_ocultar_valor(n, store):
        oculto = store.get("oculto", True) if store else True
        return {"oculto": not oculto}

    @app.callback(
        [
            Output("carteira-mensagem-status", "children"),
            Output("carteira-lista-ativos", "children")
        ],
        [
            Input("carteira-botao-adicionar", "n_clicks"),
            Input('tabela-carteira-ação', 'data_previous'),
            Input('tabela-carteira-fii', 'data_previous'),
            Input('tabela-carteira-criptomoeda', 'data_previous'),
            Input('tabela-carteira-bdr', 'data_previous'),
            Input('tabela-carteira-fixa', 'data_previous')],
        [State("carteira-input-ticker", "value"),
         State("carteira-input-quantidade", "value"),
         State('tabela-carteira-ação', 'data'),
         State('tabela-carteira-fii', 'data'),
         State('tabela-carteira-criptomoeda', 'data'),
         State('tabela-carteira-bdr', 'data'),
         State('tabela-carteira-fixa', 'data')]
    )
    def carteira_adicionar_ou_remover_ativo(n_clicks, data_prev_acao, data_prev_fii, data_prev_cripto, data_prev_bdr, data_prev_fixa,
                                            ticker, quantidade,
                                            data_acao, data_fii, data_cripto, data_bdr, data_fixa):
        mensagem = ""

        if n_clicks and ticker and quantidade:
            info = obter_informacoes_ativo(ticker)
            if info:
                adicionar_ou_atualizar_ativo(
                    info['ticker'], info['nome_completo'], float(quantidade),
                    info['preco_atual'], info['tipo'], info['dy'], info['pl'],
                    info['pvp'], info['roe']
                )
                mensagem = "✅ Ativo adicionado com sucesso."
            else:
                mensagem = "⚠️ Erro ao buscar informações."

        tipo_map = {
            'ação': data_prev_acao,
            'fii': data_prev_fii,
            'criptomoeda': data_prev_cripto,
            'bdr': data_prev_bdr,
            'fixa': data_prev_fixa
        }
        data_map = {
            'ação': data_acao,
            'fii': data_fii,
            'criptomoeda': data_cripto,
            'bdr': data_bdr,
            'fixa': data_fixa
        }
        for tipo, prev in tipo_map.items():
            atual = data_map[tipo]
            if prev is not None and atual is not None:
                prev_ids = {row['id'] for row in prev if 'id' in row}
                atual_ids = {row['id'] for row in atual if 'id' in row}
                removidos = prev_ids - atual_ids
                for id_removido in removidos:
                    remover_ativo(id_removido)
                if removidos:
                    mensagem = "🗑️ Ativo(s) removido(s)."
 
        df_carteira = pd.DataFrame(consultar_carteira())
        tipos_ativos = ['Ação', 'FII', 'Criptomoeda', 'BDR', 'Fixa']
        accordions = []
        for tipo in tipos_ativos:
            df_tipo = df_carteira[df_carteira['tipo'] == tipo] if not df_carteira.empty else pd.DataFrame()
            total_tipo = df_tipo['valor_total'].sum() if not df_tipo.empty else 0
            
            # Processa dados com logos
            data_with_logos = []
            if not df_tipo.empty:
                data_with_logos = add_logo_column_to_data(df_tipo.to_dict('records'))
            
            # Define colunas com logo
            base_columns = [
                {'name': 'Ticker', 'id': 'ticker', 'presentation': 'markdown'},
                {'name': 'Nome Completo', 'id': 'nome_completo'},
                {'name': 'Quantidade', 'id': 'quantidade', 'editable': True},
                {'name': 'Preço Atual', 'id': 'preco_atual'},
                {'name': 'Valor Total', 'id': 'valor_total'},
                {'name': 'DY', 'id': 'dy'},
                {'name': 'P/L', 'id': 'pl'},
                {'name': 'P/VP', 'id': 'pvp'},
                {'name': 'ROE', 'id': 'roe'},
                {'name': 'Tipo', 'id': 'tipo', 'editable': True}
            ]
            columns_with_logo = get_table_columns_with_logo(base_columns)
            
            tabela = dash_table.DataTable(
                id=f'tabela-carteira-{tipo.lower()}',
                columns=columns_with_logo,
                data=data_with_logos,
                editable=True,
                row_deletable=True,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                markdown_options={"html": True}
            )
            accordions.append(
                dbc.AccordionItem(
                    tabela,
                    title=f"{tipo} - Total: R$ {total_tipo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                )
            )
        return mensagem, dbc.Accordion(accordions, always_open=True)
    
    @app.callback(
    Output("carteira-lista-ativos2", "children"),
    Input("carteira-atualizador2", "n_intervals")
)
    def carteira_atualizar_tabelas_automaticamente(n_intervals):
        df_carteira = pd.DataFrame(consultar_carteira())
        tipos_ativos = ['Ação', 'FII', 'Criptomoeda', 'BDR', 'Fixa']
        accordions = []

        for tipo in tipos_ativos:
            df_tipo = df_carteira[df_carteira['tipo'] == tipo]
            total_tipo = df_tipo['valor_total'].sum() if not df_tipo.empty else 0

            # Processa dados com logos
            data_with_logos = []
            if not df_tipo.empty:
                data_with_logos = add_logo_column_to_data(df_tipo.to_dict('records'))

            # Define colunas com logo
            base_columns = [
                {'name': 'Ticker', 'id': 'ticker', 'presentation': 'markdown'},
                {'name': 'Nome Completo', 'id': 'nome_completo'},
                {'name': 'Quantidade', 'id': 'quantidade', 'editable': True},
                {'name': 'Preço Atual', 'id': 'preco_atual'},
                {'name': 'Valor Total', 'id': 'valor_total'},
                {'name': 'DY', 'id': 'dy'},
                {'name': 'P/L', 'id': 'pl'},
                {'name': 'P/VP', 'id': 'pvp'},
                {'name': 'ROE', 'id': 'roe'},
                {'name': 'Tipo', 'id': 'tipo', 'editable': True}
            ]
            columns_with_logo = get_table_columns_with_logo(base_columns)

            tabela = dash_table.DataTable(
                id=f'tabela-carteira-{tipo.lower()}',
                columns=columns_with_logo,
                data=data_with_logos,
                editable=True,
                row_deletable=True,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                markdown_options={"html": True}
            )

            accordions.append(
                dbc.AccordionItem(
                    tabela,
                    title=f"{tipo} - Total: R$ {total_tipo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                )
            )

        return dbc.Accordion(accordions, always_open=True)


    @app.callback(
    [
        Output("grafico-evolucao", "figure"),
        Output("grafico-por-tipo", "figure"),
        Output("grafico-por-ativo", "figure"),
        Output("grafico-top-posicoes", "figure"),
        Output("grafico-positivo-negativo", "figure")
    ],
    [Input("carteira-filtro-periodo", "value"), Input("switch-darkmode", "value")]
)
    def carteira_atualizar_graficos(periodo, is_dark):
        df_hist = consultar_historico(periodo)
        df_carteira = pd.DataFrame(consultar_carteira())

        template = "plotly_dark" if is_dark else "simple_white"
        fig1 = px.line(title="Evolução da Carteira vs Índices de Mercado", template=template)

        if not df_hist.empty:
            df_hist = df_hist.copy()
            df_hist["data"] = pd.to_datetime(df_hist["data"])
            df_hist = df_hist.sort_values("data")
            df_hist["carteira_normalizada"] = df_hist["valor_total"] / df_hist["valor_total"].iloc[0] * 100
            fig1.add_scatter(x=df_hist["data"], y=df_hist["carteira_normalizada"],
                            mode="lines", name="Carteira")

            data_inicio = df_hist["data"].min().strftime("%Y-%m-%d")
            data_fim = df_hist["data"].max().strftime("%Y-%m-%d")
            tickers = {
                "^BVSP": "Ibovespa",
                "IVVB11.SA": "IVVB11",
                "XFIX11.SA": "IFIX ",
                "IMAB11.SA": "IPCA",
            }
            for ticker, nome in tickers.items():
                try:
                    dados = yf.Ticker(ticker).history(start=data_inicio, end=data_fim)
                    if not dados.empty:
                        dados = dados["Close"]
                        dados_normalizado = dados / dados.iloc[0] * 100
                        fig1.add_scatter(x=dados_normalizado.index, y=dados_normalizado, mode="lines", name=nome)
                except Exception as e:
                    print(f"Erro ao obter histórico de {ticker}: {e}")

        if not df_carteira.empty:
            fig2 = px.pie(df_carteira, names="tipo", values="valor_total", title="Distribuição por Tipo de Ativo",
                          color_discrete_sequence=px.colors.sequential.Blues, template=template)
            fig3 = px.pie(df_carteira, names="ticker", values="valor_total", title="Distribuição por Ativo",
                          color_discrete_sequence=px.colors.sequential.Plasma, template=template)
            top5 = df_carteira.nlargest(5, 'valor_total')
            fig4 = px.bar(top5, x="valor_total", y="ticker", orientation="h", title="Top 5 Maiores Posições",
                         color="valor_total", color_continuous_scale=px.colors.sequential.Blues, template=template)
            fig5 = px.bar(df_carteira, x="ticker", y="valor_total", color=df_carteira["valor_total"] > 0,
                        title="Posições Positivas vs Negativas",
                        color_discrete_map={True: "#28a745", False: "#dc3545"}, template=template)
        else:
            fig2 = px.pie(title="Distribuição por Tipo de Ativo", template=template)
            fig3 = px.pie(title="Distribuição por Ativo", template=template)
            fig4 = px.bar(title="Top 5 Maiores Posições", template=template)
            fig5 = px.bar(title="Posições Positivas vs Negativas", template=template)

        return fig1, fig2, fig3, fig4, fig5

    
    @app.callback(
    Output('tabela-movimentacoes', 'data'),
    [Input('movimentacoes-filtro-mes', 'value'),
     Input('movimentacoes-filtro-ano', 'value')]
)
    def atualizar_tabela_movimentacoes(mes, ano):
        if not mes or not ano:
            return []
        df = consultar_movimentacoes(mes, ano)
        if df.empty:
            return []
        df = df.sort_values('data', ascending=False)
        df['preco'] = df['preco'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df['data'] = pd.to_datetime(df['data']).dt.strftime('%d/%m/%Y')
        
        # Adiciona logos aos dados
        data_with_logos = add_logo_column_to_data(df.to_dict('records'))
        
        return data_with_logos


    

def registrar_movimentacao(data, ticker, nome_completo, quantidade, preco, tipo):
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO movimentacoes (data, ticker, nome_completo, quantidade, preco, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data, ticker, nome_completo, quantidade, preco, tipo))
    conn.commit()
    conn.close()


def consultar_movimentacoes(mes=None, ano=None):
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    query = 'SELECT * FROM movimentacoes'
    params = []
    if mes and ano:
        query += ' WHERE strftime("%m", data) = ? AND strftime("%Y", data) = ?'
        params = [str(mes).zfill(2), str(ano)]
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df



def atualizar_precos_carteira():
    conn = sqlite3.connect('carteira.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, ticker, quantidade FROM carteira")
    ativos = cursor.fetchall()
    for id_, ticker, quantidade in ativos:
        info = obter_informacoes_ativo(ticker)
        if info and info['preco_atual']:
            preco_atual = info['preco_atual']
            valor_total = preco_atual * quantidade
            cursor.execute(
                "UPDATE carteira SET preco_atual = ?, valor_total = ? WHERE id = ?",
                (preco_atual, valor_total, id_)
            )
    conn.commit()
    conn.close()
    salvar_historico()



    



    


    
