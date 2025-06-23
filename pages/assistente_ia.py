# pages/assistente_ia.py

import os
import pandas as pd
from datetime import date, datetime
from dash import html, Input, Output, dcc, callback
import dash_bootstrap_components as dbc
from llama_cpp import Llama
import models
from pages.carteira import consultar_carteira, consultar_historico
from pages.controle import calcular_saldo_mes_ano, carregar_receitas_mes_ano, carregar_outros_mes_ano, carregar_cartoes_mes_ano
from pages.ia import gerar_insights
from dash import callback_context
import plotly.express as px
from dash.dependencies import State
import yfinance as yf

CAMINHO_MODELO = "modelos/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

modelo_global = None

def carregar_modelo():
    global modelo_global
    if modelo_global is None:
        modelo_global = Llama(model_path=CAMINHO_MODELO, n_ctx=2048, verbose=False)
    return modelo_global

def analisar_contexto_financeiro():
    hoje = date.today()
    mes = str(hoje.month).zfill(2)
    ano = str(hoje.year)
    

    df_carteira = pd.DataFrame(consultar_carteira())
    df_hist = consultar_historico('mensal')
    saldo = calcular_saldo_mes_ano(mes, ano)
    receitas = carregar_receitas_mes_ano(mes, ano)
    total_receitas = receitas['valor'].sum() if not receitas.empty else 0
    outros_gastos = carregar_outros_mes_ano(mes, ano)
    total_outros = sum([g['valor'] for g in outros_gastos]) if outros_gastos else 0
    cartoes = carregar_cartoes_mes_ano(mes, ano)
    total_cartoes = sum([c['valor'] for c in cartoes if c.get('pago') == 'Sim']) if cartoes else 0
    total_gastos = total_outros + total_cartoes
    total_investido = df_carteira['valor_total'].sum() if not df_carteira.empty else 0
    

    rentab = 0
    if not df_hist.empty:
        df_hist = df_hist.sort_values('data')
        inicial = df_hist.iloc[0]['valor_total']
        final = df_hist.iloc[-1]['valor_total']
        if inicial:
            rentab = ((final - inicial) / inicial) * 100
    

    alertas = []
    sugestoes = []
    
    if saldo < 0:
        alertas.append(f"🟥 Seu saldo financeiro está negativo: R$ {saldo:,.2f}.")
        sugestoes.append("Evite novos gastos e priorize receitas para equilibrar as contas.")
    elif saldo < total_gastos * 0.2 and total_gastos > 0:
        alertas.append(f"🟧 Seu saldo está baixo em relação aos gastos do mês: R$ {saldo:,.2f}.")
        sugestoes.append("Atenção ao risco de saldo negativo. Considere reduzir despesas.")
    if total_gastos > total_receitas and total_receitas > 0:
        alertas.append(f"🟧 Gastos do mês ({total_gastos:,.2f}) superam as receitas ({total_receitas:,.2f}).")
        sugestoes.append("Busque aumentar receitas ou cortar despesas para evitar déficit.")
    if rentab < 0:
        alertas.append(f"🟥 Rentabilidade negativa no mês: {rentab:.2f}%.")
        sugestoes.append("Analise os ativos com pior desempenho e avalie ajustes na carteira.")
    if df_carteira.empty:
        alertas.append("⚠️ Você ainda não possui ativos na carteira.")
        sugestoes.append("Considere investir para potencializar seu patrimônio.")
    else:

        tipo_distrib = df_carteira['tipo'].value_counts(normalize=True)
        for tipo, prop in tipo_distrib.items():
            if prop > 0.6:
                alertas.append(f"🟥 Mais de {int(prop*100)}% da carteira está concentrada em {tipo}s.")
                sugestoes.append(f"Avalie diversificar mais seus investimentos além de {tipo}s.")
            elif prop > 0.4:
                alertas.append(f"🟨 {int(prop*100)}% da carteira está em {tipo}s.")
                sugestoes.append(f"Atenção ao equilíbrio entre tipos de ativos.")

        top_ativo = df_carteira.nlargest(1, 'valor_total')
        if not top_ativo.empty:
            ativo = top_ativo.iloc[0]
            if ativo['valor_total'] > total_investido * 0.5:
                alertas.append(f"🟧 O ativo {ativo['ticker']} representa mais de 50% da carteira.")
                sugestoes.append(f"Considere distribuir melhor entre outros ativos.")

        for indicador in ['dy', 'pl', 'pvp', 'roe']:
            media = df_carteira[indicador].mean()
            if not pd.isna(media):
                if indicador == 'dy' and media < 2:
                    alertas.append(f"🟨 Dividend Yield médio baixo: {media:.2f}%.")
                    sugestoes.append("Busque ativos com melhor distribuição de dividendos.")
                if indicador == 'pl' and media > 20:
                    alertas.append(f"🟧 P/L médio elevado: {media:.2f}.")
                    sugestoes.append("Avalie se há ativos caros na carteira.")
                if indicador == 'roe' and media < 10:
                    alertas.append(f"🟨 ROE médio baixo: {media:.2f}%.")
                    sugestoes.append("Busque empresas mais rentáveis.")

    df_mov = None
    try:
        from pages.carteira import consultar_movimentacoes
        df_mov = consultar_movimentacoes(mes, ano)
    except Exception:
        pass
    if df_mov is not None and not df_mov.empty:
        ultimas = df_mov.sort_values('data', ascending=False).head(3)
        ultimas_str = '\n'.join([
            f"{row['data'][:10]}: {row['tipo'].capitalize()} {row['quantidade']} de {row['ticker']} a R$ {row['preco']:.2f}" for _, row in ultimas.iterrows()
        ])
    else:
        ultimas_str = "Nenhuma movimentação recente."

    resumo = f"""
    Saldo: R$ {saldo:,.2f}\nReceitas do mês: R$ {total_receitas:,.2f}\nGastos do mês: R$ {total_gastos:,.2f}\nTotal investido: R$ {total_investido:,.2f}\nRentabilidade mês: {rentab:.2f}%\n\nMovimentações recentes:\n{ultimas_str}
    """
    return resumo, alertas, sugestoes

def construir_prompt(pergunta):
    resumo, alertas, sugestoes = analisar_contexto_financeiro()
    alertas_str = '\n'.join(alertas) if alertas else 'Nenhum alerta crítico.'
    sugestoes_str = '\n'.join(sugestoes) if sugestoes else 'Nenhuma sugestão específica.'
    prompt = f"""
Você é um agente financeiro inteligente e proativo. Analise o contexto abaixo, gere alertas, sugestões e responda dúvidas sobre o sistema ou finanças.\n\nContexto do usuário:\n{resumo}\n\nAlertas detectados:\n{alertas_str}\n\nSugestões do agente:\n{sugestoes_str}\n\nPergunta do usuário: {pergunta}\n\nResponda de forma clara, útil e, se possível, proativa, mesmo que o usuário não pergunte nada diretamente.
    """
    return prompt

def get_dashboard_data():
    hoje = date.today()
    mes = str(hoje.month).zfill(2)
    ano = str(hoje.year)

    df_carteira = pd.DataFrame(consultar_carteira())
    total_investido = df_carteira['valor_total'].sum() if not df_carteira.empty else 0

    df_hist = consultar_historico('mensal')
    rentab = 0
    if not df_hist.empty:
        df_hist = df_hist.sort_values('data')
        inicial = df_hist.iloc[0]['valor_total']
        final = df_hist.iloc[-1]['valor_total']
        if inicial:
            rentab = ((final - inicial) / inicial) * 100

    saldo = calcular_saldo_mes_ano(mes, ano)
    receitas = carregar_receitas_mes_ano(mes, ano)
    total_receitas = receitas['valor'].sum() if not receitas.empty else 0
    outros_gastos = carregar_outros_mes_ano(mes, ano)
    total_outros = sum([g['valor'] for g in outros_gastos]) if outros_gastos else 0
    cartoes = carregar_cartoes_mes_ano(mes, ano)
    total_cartoes = sum([c['valor'] for c in cartoes if c.get('pago') == 'Sim']) if cartoes else 0
    total_gastos = total_outros + total_cartoes
    # Insights
    insights = gerar_insights()
    insight_principal = insights[0] if insights else "Sem insights no momento."
    return {
        'total_investido': total_investido,
        'saldo': saldo,
        'total_receitas': total_receitas,
        'total_gastos': total_gastos,
        'rentabilidade': rentab,
        'insight': insight_principal,
        'debug_cartoes': cartoes,
        'debug_outros': outros_gastos
    }

def layout():
    data = get_dashboard_data()

    oculto_store = dcc.Store(id="assistente-ocultar-valor", data={"oculto": True})

    oculto_btn = html.Button(
        id="assistente-botao-ocultar",
        n_clicks=0,
        children=html.Span(id="assistente-icone-ocultar", children="👁"),
        style={
            "border": "none", "background": "none", "fontSize": "1.3rem", "cursor": "pointer", "verticalAlign": "middle", "marginLeft": "10px", "color": "#888"
        }
    )

    topo = html.Div([
        html.H3("Dashboard do Assistente", className="d-inline-block me-2 mb-3"),
        oculto_btn,
        oculto_store
    ], className="d-flex align-items-center justify-content-between mb-2")

    def mostrar_valor(valor, oculto):
        return "•••••••" if oculto else valor

    cards_row1 = [
        dbc.Col(dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-wallet2", style={"fontSize": "2.5rem", "color": "#0d6efd"}),
                    html.Div("Total Investido", className="fw-bold text-muted small mt-2 mb-1"),
                    html.Div(id="assistente-total-investido", className="fs-4 fw-bold text-primary")
                ])
            ], className="dashboard-card2 animate__animated animate__fadeInUp"),
            href="/carteira", style={"textDecoration": "none"}
        ), md=4, xs=12),
        dbc.Col(dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-cash-coin", style={"fontSize": "2.5rem", "color": "#28a745"}),
                    html.Div("Saldo Financeiro", className="fw-bold text-muted small mt-2 mb-1"),
                    html.Div(id="assistente-saldo", className="fs-4 fw-bold text-success")
                ])
            ], className="dashboard-card2 animate__animated animate__fadeInUp"),
            href="/controle", style={"textDecoration": "none"}
        ), md=4, xs=12),
        dbc.Col(dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-arrow-down-circle", style={"fontSize": "2.5rem", "color": "#dc3545"}),
                    html.Div("Gastos do Mês", className="fw-bold text-muted small mt-2 mb-1"),
                    html.Div(id="assistente-total-gastos", className="fs-4 fw-bold text-danger")
                ])
            ], className="dashboard-card2 animate__animated animate__fadeInUp"),
            href="/controle", style={"textDecoration": "none"}
        ), md=4, xs=12),
    ]
    cards_row2 = [
        dbc.Col(dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-arrow-up-circle", style={"fontSize": "2.5rem", "color": "#ffc107"}),
                    html.Div("Receitas do Mês", className="fw-bold text-muted small mt-2 mb-1"),
                    html.Div(id="assistente-total-receitas", className="fs-4 fw-bold text-warning")
                ])
            ], className="dashboard-card2 animate__animated animate__fadeInUp"),
            href="/controle", style={"textDecoration": "none"}
        ), md=4, xs=12),
        dbc.Col(dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-graph-up-arrow", style={"fontSize": "2.5rem", "color": "#6610f2"}),
                    html.Div("Rentabilidade Mês", className="fw-bold text-muted small mt-2 mb-1"),
                    html.Div(id="assistente-rentabilidade", className="fs-4 fw-bold", style={"color": "#6610f2"})
                ])
            ], className="dashboard-card2 animate__animated animate__fadeInUp"),
            href="/carteira", style={"textDecoration": "none"}
        ), md=4, xs=12),
        dbc.Col(dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-lightbulb", style={"fontSize": "2.5rem", "color": "#fd7e14"}),
                    html.Div("Insight do Mês", className="fw-bold text-muted small mt-2 mb-1"),
                    html.Div(data['insight'], className="fs-6 fw-bold text-dark", style={"minHeight": "32px"})
                ])
            ], className="dashboard-card2 animate__animated animate__fadeInUp"),
            href="/carteira", style={"textDecoration": "none"}
        ), md=4, xs=12),
    ]
    periodos = [
        {"label": "Semanal", "value": "semanal"},
        {"label": "Mensal", "value": "mensal"},
        {"label": "Semestral", "value": "semestral"},
        {"label": "Anual", "value": "anual"},
    ]
    return dbc.Container([
        topo,
        dbc.Row(cards_row1, className="g-4 mb-3"),
        dbc.Row(cards_row2, className="g-4 mb-4"),

        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label("Período:", className="fw-bold mb-1 me-2"),
                    dcc.Dropdown(
                        id="assistente-filtro-periodo",
                        options=periodos,
                        value="mensal",
                        clearable=False,
                        style={"width": "220px", "display": "inline-block"}
                    ),
                ], className="d-flex justify-content-center align-items-center mb-2"),
                dcc.Graph(id="assistente-grafico-evolucao", config={'displayModeBar': False}),
            ], md=12, xs=12, className="mb-4"),
        ], className="g-4 mb-2"),

        dbc.Row([
            dbc.Col(dcc.Graph(id="assistente-grafico-pizza", config={'displayModeBar': False}), md=6, xs=12, className="mb-4"),
            dbc.Col(dcc.Graph(id="assistente-grafico-gastos", config={'displayModeBar': False}), md=6, xs=12, className="mb-4"),
        ], className="g-4 mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🧠 Assistente com IA", className="bg-white text-primary fw-bold text-center"),
                    dbc.CardBody([
                        html.P("Pergunte sobre sua carteira ou finanças em geral:", className="mb-2 text-muted small"),
                        dbc.Input(id="input-pergunta-ia", type="text", placeholder="Ex: O que é o Ibovespa?", debounce=True, className="mb-2"),
                        html.Div(id="output-resposta-ia", className="mt-2 p-3 border rounded assistente-output animate__animated animate__fadeIn")
                    ])
                ], className="shadow-sm animate__animated animate__fadeInRight")
            ], md=8, xs=12, style={"minWidth": "320px", "margin": "0 auto"}),
        ], className="g-4 align-items-stretch justify-content-center mt-4 mb-4"),
        dcc.Markdown("""
<style>
.dashboard-card2 {
    border-radius: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    background: #fff;
    min-height: 140px;
    transition: box-shadow 0.2s, transform 0.2s;
    cursor: pointer;
    border: 1px solid #e9ecef;
    padding: 1.2rem 1.5rem 1.2rem 1.5rem;
}
.dashboard-card2:hover {
    box-shadow: 0 8px 32px rgba(13,110,253,0.13);
    transform: scale(1.03) translateY(-2px);
}
@media (max-width: 900px) {
    .dashboard-card2 { min-height: 110px; padding: 0.7rem 0.7rem; }
}
</style>
""", dangerously_allow_html=True)
    ], fluid=True)

def registrar_callbacks(app):
    @app.callback(
        Output("output-resposta-ia", "children"),
        Input("input-pergunta-ia", "value")
    )
    def responder_ia(pergunta):
        try:
            prompt = construir_prompt(pergunta or "")
            resposta = carregar_modelo()(prompt, max_tokens=256)  
            texto = resposta["choices"][0]["text"].strip()
            return html.Div([
                html.H6("Resposta:"),
                html.P(texto)
            ])
        except Exception as e:
            return html.Div([
                html.H6("❌ Erro ao processar a pergunta:"),
                html.Pre(str(e))
            ])

    @app.callback(
        Output("assistente-grafico-evolucao", "figure"),
        [Input("assistente-filtro-periodo", "value"), Input("switch-darkmode", "value")]
    )
    def atualizar_grafico_evolucao(periodo, is_dark):
        from datetime import date
        from pages.carteira import consultar_historico
        import plotly.express as px
        import yfinance as yf
        template = 'plotly_dark' if is_dark else 'simple_white'
        if is_dark:
            bg_color = "#18191A"
            paper_color = "#18191A"
            font_color = "#E4E6EB"
        else:
            bg_color = "#f8f9fa"
            paper_color = "#f8f9fa"
            font_color = "#222"
        df_hist = consultar_historico(periodo)
        fig = px.line(title="Evolução da Carteira vs Índices de Mercado", template=template)
        if not df_hist.empty:
            df_hist = df_hist.copy()
            df_hist["data"] = pd.to_datetime(df_hist["data"])
            df_hist = df_hist.sort_values("data")
            df_hist["carteira_normalizada"] = df_hist["valor_total"] / df_hist["valor_total"].iloc[0] * 100
            fig.add_scatter(x=df_hist["data"], y=df_hist["carteira_normalizada"],
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
                        fig.add_scatter(x=dados_normalizado.index, y=dados_normalizado, mode="lines", name=nome)
                except Exception as e:
                    print(f"Erro ao obter histórico de {ticker}: {e}")
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20), height=300,
            plot_bgcolor=bg_color, paper_bgcolor=paper_color, font=dict(size=15, color=font_color, family='Segoe UI'),
            xaxis=dict(showgrid=True, gridcolor='#e9ecef'), yaxis=dict(showgrid=True, gridcolor='#e9ecef'),
            title_font=dict(size=18, color='#007bff'),
            xaxis_title="Data", yaxis_title="% Evolução",
            hovermode='x unified',
        )
        return fig

    @app.callback(
        [Output("assistente-grafico-pizza", "figure"), Output("assistente-grafico-gastos", "figure")],
        [Input("switch-darkmode", "value")]
    )
    def atualizar_graficos_pizza_gastos(is_dark):
        from pages.carteira import consultar_carteira
        from pages.controle import carregar_cartoes_mes_ano, carregar_outros_mes_ano
        from datetime import date
        import plotly.express as px
        template = 'plotly_dark' if is_dark else 'simple_white'
        if is_dark:
            bg_color = "#18191A"
            paper_color = "#18191A"
            font_color = "#E4E6EB"
        else:
            bg_color = "#f8f9fa"
            paper_color = "#f8f9fa"
            font_color = "#222"
        df_carteira = pd.DataFrame(consultar_carteira())
        fig_pizza = px.pie()
        if not df_carteira.empty:
            fig_pizza = px.pie(df_carteira, names='tipo', values='valor_total', title='Distribuição por Tipo',
                               color_discrete_sequence=px.colors.sequential.Blues, template=template)
        fig_pizza.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300,
                               plot_bgcolor=bg_color, paper_bgcolor=paper_color, font=dict(size=15, color=font_color, family='Segoe UI'),
                               title_font=dict(size=18, color='#007bff'))
        mes = str(date.today().month).zfill(2)
        ano = str(date.today().year)
        cartoes = carregar_cartoes_mes_ano(mes, ano)
        outros = carregar_outros_mes_ano(mes, ano)
        df_gastos = pd.DataFrame(cartoes + outros)
        if not df_gastos.empty:
            df_gastos['nome'] = df_gastos.get('nome', df_gastos.get('quem_usou', 'Gasto'))
            df_gastos['valor'] = df_gastos['valor'].astype(float)
            top_gastos = df_gastos.groupby('nome')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(5)
            fig_gastos = px.bar(top_gastos, x='valor', y='nome', orientation='h', title='Top 5 Gastos do Mês',
                                color='valor', color_continuous_scale=px.colors.sequential.Reds, template=template)
            fig_gastos.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=320,
                                    plot_bgcolor=bg_color, paper_bgcolor=paper_color, font=dict(size=15, color=font_color, family='Segoe UI'),
                                    title_font=dict(size=18, color='#dc3545'), xaxis_title='', yaxis_title='')
        else:
            fig_gastos = px.bar(title='Top 5 Gastos do Mês', template=template)
            fig_gastos.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=320,
                                    plot_bgcolor=bg_color, paper_bgcolor=paper_color, font=dict(size=15, color=font_color, family='Segoe UI'),
                                    title_font=dict(size=18, color='#dc3545'), xaxis_title='', yaxis_title='')
        return fig_pizza, fig_gastos

    @app.callback(
        Output("assistente-ocultar-valor", "data"),
        Input("assistente-botao-ocultar", "n_clicks"),
        State("assistente-ocultar-valor", "data"),
        prevent_initial_call=True
    )
    def alternar_ocultar_assistente(n, store):
        oculto = store.get("oculto", True) if store else True
        return {"oculto": not oculto}

    @app.callback(
        [Output("assistente-total-investido", "children"),
         Output("assistente-saldo", "children"),
         Output("assistente-total-gastos", "children"),
         Output("assistente-total-receitas", "children"),
         Output("assistente-rentabilidade", "children"),
         Output("assistente-icone-ocultar", "children")],
        [Input("assistente-ocultar-valor", "data")]
    )
    def atualizar_valores_assistente(store):
        data = get_dashboard_data()
        oculto = store.get("oculto", True) if store else True
        def fmt(valor, prefixo="R$"):
            return f"{prefixo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        total_investido = "•••••••" if oculto else fmt(data['total_investido'])
        saldo = "•••••••" if oculto else fmt(data['saldo'])
        total_gastos = "•••••••" if oculto else fmt(data['total_gastos'])
        total_receitas = "•••••••" if oculto else fmt(data['total_receitas'])
        rentabilidade = "•••••••" if oculto else f"{data['rentabilidade']:.2f}%"
        icone = "👁" if oculto else "🔒"
        return total_investido, saldo, total_gastos, total_receitas, rentabilidade, icone




