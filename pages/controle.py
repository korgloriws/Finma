import sqlite3
import dash
import pandas as pd
from datetime import date
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table
import plotly.express as px



def init_db():
    conn = sqlite3.connect('financeiro.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor REAL NOT NULL,
            data TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cartoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            valor REAL,
            pago TEXT,
            quem_usou TEXT,
            data TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outros_gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            valor REAL,
            data TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def salvar_receita(valor):

    conn = sqlite3.connect('financeiro.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO receitas (valor, data) VALUES (?, ?)
    """, (valor, date.today().isoformat()))
    conn.commit()
    conn.close()

def adicionar_cartao(nome, valor, pago, quem_usou):

    conn = sqlite3.connect('financeiro.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cartoes (nome, valor, pago, quem_usou, data)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, valor, pago, quem_usou, date.today().isoformat()))
    conn.commit()
    conn.close()

def adicionar_outro_gasto(nome, valor):

    conn = sqlite3.connect('financeiro.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO outros_gastos (nome, valor, data)
        VALUES (?, ?, ?)
    """, (nome, valor, date.today().isoformat()))
    conn.commit()
    conn.close()

def remover_cartao(id_registro):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cartoes WHERE id = ?", (id_registro,))
    conn.commit()
    conn.close()

def remover_outro_gasto(id_registro):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM outros_gastos WHERE id = ?", (id_registro,))
    conn.commit()
    conn.close()

def atualizar_cartao(id_registro, nome, valor, pago, quem_usou):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cartoes
        SET nome = ?, valor = ?, pago = ?, quem_usou = ?
        WHERE id = ?
    """, (nome, valor, pago, quem_usou, id_registro))
    conn.commit()
    conn.close()

def atualizar_outro_gasto(id_registro, nome, valor):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE outros_gastos
        SET nome = ?, valor = ?
        WHERE id = ?
    """, (nome, valor, id_registro))
    conn.commit()
    conn.close()

def carregar_cartoes_mes_ano(mes, ano):
    if not mes:
        mes = str(date.today().month).zfill(2)
    if not ano:
        ano = str(date.today().year)
    conn = sqlite3.connect("financeiro.db")
    query = """
        SELECT id, nome, valor, pago, quem_usou, data
        FROM cartoes
        WHERE strftime('%m', data) = ?
          AND strftime('%Y', data) = ?
    """
    df = pd.read_sql_query(query, conn, params=[str(mes).zfill(2), str(ano)])
    conn.close()
    return df.to_dict("records")

def carregar_outros_mes_ano(mes, ano):
    if not mes:
        mes = str(date.today().month).zfill(2)
    if not ano:
        ano = str(date.today().year)
    conn = sqlite3.connect("financeiro.db")
    query = """
        SELECT id, nome, valor, data
        FROM outros_gastos
        WHERE strftime('%m', data) = ?
          AND strftime('%Y', data) = ?
    """
    df = pd.read_sql_query(query, conn, params=[str(mes).zfill(2), str(ano)])
    conn.close()
    return df.to_dict("records")

def carregar_receitas_mes_ano(mes, ano):
    if not mes:
        mes = str(date.today().month).zfill(2)
    if not ano:
        ano = str(date.today().year)
    conn = sqlite3.connect("financeiro.db")
    query = """
        SELECT id, valor, data
        FROM receitas
        WHERE strftime('%m', data) = ?
          AND strftime('%Y', data) = ?
    """
    df = pd.read_sql_query(query, conn, params=[str(mes).zfill(2), str(ano)])
    conn.close()
    return df

def calcular_saldo_mes_ano(mes, ano):

    df_receitas = carregar_receitas_mes_ano(mes, ano)
    total_receita = df_receitas['valor'].sum() if not df_receitas.empty else 0

    df_cartoes = pd.DataFrame(carregar_cartoes_mes_ano(mes, ano))
    gastos_cartao = 0
    if not df_cartoes.empty:
        gastos_cartao = df_cartoes[
            (df_cartoes['pago'] == 'Sim') & (df_cartoes['quem_usou'] == 'Mateus')
        ]['valor'].sum()

    df_outros = pd.DataFrame(carregar_outros_mes_ano(mes, ano))
    gastos_outros = df_outros['valor'].sum() if not df_outros.empty else 0

    return total_receita - gastos_cartao - gastos_outros



def registrar_callbacks(app):


    @app.callback(
        [Output('tabela-cartoes', 'data'),
         Output('mensagem-status-cartoes', 'children')],
        [Input('btn-adicionar-cartao', 'n_clicks'),
         Input('tabela-cartoes', 'data_previous'),
         Input('filtro-mes', 'value'),
         Input('filtro-ano', 'value')],
        [State('nome-cartao', 'value'),
         State('valor-cartao', 'value'),
         State('pago-cartao', 'value'),
         State('quem-usou', 'value'),
         State('tabela-cartoes', 'data')],
        prevent_initial_call=True
    )
    def callback_cartoes(n_clicks, data_previous, mes, ano, nome, valor, pago, quem, data_atual):
        status_msg = ""


        if n_clicks and nome and valor and pago and quem:
            adicionar_cartao(nome, valor, pago, quem)
            status_msg = "✅ Cartão adicionado."


        if data_previous:
            df_prev = pd.DataFrame(data_previous)
            df_new = pd.DataFrame(data_atual)


            if len(df_prev) > len(df_new):
                removidos = df_prev[~df_prev['id'].isin(df_new['id'])]
                for _, row in removidos.iterrows():
                    remover_cartao(row['id'])
                status_msg = "🗑️ Cartão removido."


            for i in df_new.index:
                atual = df_new.loc[i]
                antigo = df_prev[df_prev['id'] == atual['id']]
                if not antigo.empty:
                    antigo = antigo.iloc[0]
                    if (antigo['nome'] != atual['nome']
                        or float(antigo['valor']) != float(atual['valor'])
                        or antigo['pago'] != atual['pago']
                        or antigo['quem_usou'] != atual['quem_usou']):
                        atualizar_cartao(
                            atual['id'],
                            atual['nome'],
                            float(atual['valor']),
                            atual['pago'],
                            atual['quem_usou']
                        )
                        status_msg = "✏️ Cartão atualizado."


        if mes and ano:
            df_cartoes = carregar_cartoes_mes_ano(mes, ano)
        else:
            df_cartoes = []
        return df_cartoes, status_msg


    @app.callback(
        [Output('tabela-outros', 'data'),
         Output('mensagem-status-outros', 'children')],
        [Input('btn-adicionar-outro', 'n_clicks'),
         Input('tabela-outros', 'data_previous'),
         Input('filtro-mes', 'value'),
         Input('filtro-ano', 'value')],
        [State('nome-outro', 'value'),
         State('valor-outro', 'value'),
         State('tabela-outros', 'data')],
        prevent_initial_call=True
    )
    def callback_outros(n_clicks, data_previous, mes, ano, nome, valor, data_atual):
        status_msg = ""


        if n_clicks and nome and valor:
            adicionar_outro_gasto(nome, valor)
            status_msg = "✅ Gasto adicionado."


        if data_previous:
            df_prev = pd.DataFrame(data_previous)
            df_new = pd.DataFrame(data_atual)
            if len(df_prev) > len(df_new):

                removidos = df_prev[~df_prev['id'].isin(df_new['id'])]
                for _, row in removidos.iterrows():
                    remover_outro_gasto(row['id'])
                status_msg = "🗑️ Gasto removido."


            for i in df_new.index:
                atual = df_new.loc[i]
                antigo = df_prev[df_prev['id'] == atual['id']]
                if not antigo.empty:
                    antigo = antigo.iloc[0]
                    if (antigo['nome'] != atual['nome']
                        or float(antigo['valor']) != float(atual['valor'])):
                        atualizar_outro_gasto(
                            atual['id'],
                            atual['nome'],
                            float(atual['valor'])
                        )
                        status_msg = "✏️ Gasto atualizado."


        if mes and ano:
            df_outros = carregar_outros_mes_ano(mes, ano)
        else:
            df_outros = []
        return df_outros, status_msg

    @app.callback(
        Output("display-saldo", "children"),
        [Input("btn-salvar-receita", "n_clicks"),
         Input("tabela-cartoes", "data"),
         Input("tabela-outros", "data"),
         Input("filtro-mes", "value"),
         Input("filtro-ano", "value")],
        [State("input-receita", "value")],
        prevent_initial_call=True
    )
    def atualizar_saldo(n_clicks_receita, data_cartoes, data_outros, mes, ano, receita_value):

        ctx = dash.callback_context
        if ctx.triggered and "btn-salvar-receita" in ctx.triggered[0]["prop_id"]:
            if receita_value:
                salvar_receita(valor=receita_value)

        if mes and ano:
            saldo = calcular_saldo_mes_ano(mes, ano)
        else:
            saldo = 0  

        cor = "green" if saldo >= 0 else "red"
        texto = f"Saldo Atual: R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return html.Span(texto, style={"color": cor})


    @app.callback(
    Output("total-por-pessoa", "children"),
    [Input("tabela-cartoes", "data"),
     Input("tabela-outros", "data")]
)
    def agrupar_por_pessoa(cartoes_data, outros_data):
        df_cartoes = pd.DataFrame(cartoes_data)
        df_outros = pd.DataFrame(outros_data)
        if not df_cartoes.empty and 'quem_usou' in df_cartoes.columns:
            grupo_cartoes = df_cartoes.groupby("quem_usou")["valor"].sum().reset_index()
        else:
            grupo_cartoes = pd.DataFrame(columns=["quem_usou", "valor"])
        total_outros = df_outros["valor"].sum() if not df_outros.empty else 0
        if "Mateus" in grupo_cartoes["quem_usou"].values:
            grupo_cartoes.loc[grupo_cartoes["quem_usou"] == "Mateus", "valor"] += total_outros
        else:
            grupo_cartoes = pd.concat([
                grupo_cartoes,
                pd.DataFrame([{"quem_usou": "Mateus", "valor": total_outros}])
            ], ignore_index=True)
        linhas = []
        for _, row in grupo_cartoes.iterrows():
            linhas.append(f"{row['quem_usou']}: R$ {row['valor']:.2f}".replace('.', ','))
        return html.Div([html.Div(linha) for linha in linhas])



    @app.callback(
        Output("grafico-evolucao-financeira", "figure"),
        [Input("filtro-mes", "value"),
         Input("filtro-ano", "value"),
         Input("tabela-cartoes", "data"),
         Input("tabela-outros", "data"),
         Input("switch-darkmode", "value")]
    )
    def atualizar_grafico(mes, ano, cartoes_data, outros_data, is_dark):
        template = 'plotly_dark' if is_dark else 'simple_white'
        if is_dark:
            bg_color = "#18191A"
            paper_color = "#18191A"
            font_color = "#E4E6EB"
            legend_bg = "rgba(40,40,40,0.7)"
        else:
            bg_color = "#f8f9fa"
            paper_color = "#f8f9fa"
            font_color = "#222"
            legend_bg = "rgba(255,255,255,0.7)"
        if not mes or not ano:
            fig = px.line(title="Evolução Financeira", template=template)
            fig.update_layout(
                plot_bgcolor=bg_color, paper_bgcolor=paper_color,
                font=dict(color=font_color, family='Segoe UI'),
                title_font=dict(size=22, color='#007bff'),
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis=dict(showgrid=True, gridcolor='#e9ecef'),
                yaxis=dict(showgrid=True, gridcolor='#e9ecef'),
                hovermode='x unified',
                legend=dict(bgcolor=legend_bg, bordercolor='#007bff', borderwidth=1)
            )
            return fig


        df_receita = carregar_receitas_mes_ano(mes, ano)
        df_receita["data"] = pd.to_datetime(df_receita["data"])
        df_receita_grouped = df_receita.groupby("data")["valor"].sum().reset_index(name="receitas")


        df_cartao = pd.DataFrame(cartoes_data)
        df_outros = pd.DataFrame(outros_data)
        df_cartao["data"] = pd.to_datetime(df_cartao["data"]) if not df_cartao.empty else pd.Series(dtype='datetime64[ns]')
        df_outros["data"] = pd.to_datetime(df_outros["data"]) if not df_outros.empty else pd.Series(dtype='datetime64[ns]')
        df_cartao_ = df_cartao[["data", "valor"]] if not df_cartao.empty else pd.DataFrame(columns=["data", "valor"])
        df_outros_ = df_outros[["data", "valor"]] if not df_outros.empty else pd.DataFrame(columns=["data", "valor"])
        df_despesas = pd.concat([df_cartao_, df_outros_]) if not df_cartao_.empty or not df_outros_.empty else pd.DataFrame(columns=["data", "valor"])
        if df_despesas.empty:
            df_despesas_grouped = pd.DataFrame({"data": [], "despesas": []})
        else:
            df_despesas_grouped = df_despesas.groupby("data")["valor"].sum().reset_index(name="despesas")


        dias = pd.date_range(start=f"{ano}-{mes.zfill(2)}-01", end=pd.Timestamp(f"{ano}-{mes.zfill(2)}-01") + pd.offsets.MonthEnd(0))
        df_base = pd.DataFrame({"data": dias})
        df_merged = pd.merge(df_base, df_receita_grouped, on="data", how="left").merge(df_despesas_grouped, on="data", how="left")
        df_merged["receitas"] = df_merged["receitas"].fillna(0)
        df_merged["despesas"] = df_merged["despesas"].fillna(0)
        df_merged["saldo_dia"] = df_merged["receitas"] - df_merged["despesas"]
        df_merged["saldo_acumulado"] = df_merged["saldo_dia"].cumsum()

        fig = px.line(df_merged, x="data", y="saldo_acumulado", title="Evolução Financeira", markers=True, template=template)
        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=paper_color,
            font=dict(color=font_color, family='Segoe UI'),
            title_font=dict(size=22, color='#007bff'),
            margin=dict(l=20, r=20, t=60, b=20),
            xaxis_title="Data", yaxis_title="Saldo Acumulado",
            xaxis=dict(showgrid=True, gridcolor='#e9ecef'),
            yaxis=dict(showgrid=True, gridcolor='#e9ecef'),
            hovermode='x unified',
            legend=dict(bgcolor=legend_bg, bordercolor='#007bff', borderwidth=1)
        )
        return fig


    @app.callback(
        Output("grafico-por-pessoa", "figure"),
        [Input("tabela-cartoes", "data"), Input("switch-darkmode", "value")]
    )
    def grafico_por_pessoa(cartoes_data, is_dark):
        template = 'plotly_dark' if is_dark else 'simple_white'
        if is_dark:
            bg_color = "#18191A"
            paper_color = "#18191A"
            font_color = "#E4E6EB"
            legend_bg = "rgba(40,40,40,0.7)"
        else:
            bg_color = "#f8f9fa"
            paper_color = "#f8f9fa"
            font_color = "#222"
            legend_bg = "rgba(255,255,255,0.7)"
        df = pd.DataFrame(cartoes_data)
        if df.empty:
            fig = px.pie(title="Gastos por Pessoa", template=template)
        else:
            fig = px.pie(df, names="quem_usou", values="valor", title="Gastos por Pessoa",
                         color_discrete_sequence=px.colors.sequential.Blues, template=template)
        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=paper_color,
            font=dict(color=font_color, family='Segoe UI'),
            title_font=dict(size=22, color='#007bff'),
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(bgcolor=legend_bg, bordercolor='#007bff', borderwidth=1)
        )
        return fig


    @app.callback(
        Output("grafico-receitas-despesas", "figure"),
        [Input("filtro-mes", "value"),
         Input("filtro-ano", "value"),
         Input("tabela-cartoes", "data"),
         Input("tabela-outros", "data"),
         Input("switch-darkmode", "value")]
    )
    def grafico_receitas_despesas(mes, ano, cartoes_data, outros_data, is_dark):
        template = 'plotly_dark' if is_dark else 'simple_white'
        if is_dark:
            bg_color = "#18191A"
            paper_color = "#18191A"
            font_color = "#E4E6EB"
            legend_bg = "rgba(40,40,40,0.7)"
        else:
            bg_color = "#f8f9fa"
            paper_color = "#f8f9fa"
            font_color = "#222"
            legend_bg = "rgba(255,255,255,0.7)"
        df_receita = carregar_receitas_mes_ano(mes, ano)
        df_cartao = pd.DataFrame(cartoes_data)
        df_outros = pd.DataFrame(outros_data)
        despesas = 0
        if not df_cartao.empty:
            despesas += df_cartao["valor"].sum()
        if not df_outros.empty:
            despesas += df_outros["valor"].sum()
        total_receita = df_receita["valor"].sum() if not df_receita.empty else 0
        df_bar = pd.DataFrame({
            "Categoria": ["Receitas", "Despesas"],
            "Valor": [total_receita, despesas]
        })
        fig = px.bar(df_bar, x="Categoria", y="Valor", title="Receitas x Despesas",
                     color="Categoria", color_discrete_map={"Receitas": "#28a745", "Despesas": "#dc3545"}, template=template)
        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=paper_color,
            font=dict(color=font_color, family='Segoe UI'),
            title_font=dict(size=22, color='#007bff'),
            margin=dict(l=20, r=20, t=60, b=20),
            xaxis=dict(showgrid=True, gridcolor='#e9ecef'),
            yaxis=dict(showgrid=True, gridcolor='#e9ecef'),
            hovermode='x unified',
            legend=dict(bgcolor=legend_bg, bordercolor='#007bff', borderwidth=1)
        )
        return fig


def layout():
    return dbc.Container([
        html.H3("Controle Financeiro", className="text-center my-4"),


        dbc.Row([

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filtrar Mês/Ano"),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id='filtro-mes',
                            options=[
                                {'label': mes, 'value': str(i+1).zfill(2)} for i, mes in enumerate([
                                    'Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                                    'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'
                                ])
                            ],
                            placeholder="Selecione o mês",
                            style={"margin-bottom": "10px"}
                        ),
                        dcc.Input(
                            id='filtro-ano',
                            type='number',
                            placeholder='Ano',
                            value=date.today().year,
                            className="form-control"
                        )
                    ])
                ], className="mb-3"),
            ], width=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Saldo e Receita"),
                    dbc.CardBody([
                        html.Div(id="display-saldo", className="fs-5 fw-bold text-center mb-4"),
                        dcc.Input(
                            id="input-receita",
                            type="number",
                            placeholder="Valor recebido",
                            className="form-control mb-2"
                        ),
                        html.Button("Salvar Receita", id="btn-salvar-receita", className="btn btn-success w-100"),
                    ])
                ], className="mb-3"),
            ], width=5),


            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total por Pessoa"),
                    dbc.CardBody([
                        html.Div(
                            id="total-por-pessoa", 
                            className="text-center fs-5"
                        )
                    ])
                ], className="mb-3"),
            ], width=4),
        ], justify="start"),

        html.Hr(className="my-4"),


        html.H4("Gastos com Cartão de Crédito", className="mt-4 mb-3 text-primary"),
        dbc.Row([
            dbc.Col(dcc.Input(id='nome-cartao', type='text', placeholder='Nome do Cartão', className='form-control'), md=3),
            dbc.Col(dcc.Input(id='valor-cartao', type='number', placeholder='Valor', className='form-control'), md=2),
            dbc.Col(
                dcc.Dropdown(
                    id='pago-cartao',
                    options=[{'label': i, 'value': i} for i in ['Sim', 'Não']],
                    placeholder='Foi pago?',
                    className='form-control'
                ), md=2
            ),
            dbc.Col(dcc.Input(id='quem-usou', type='text', placeholder='Quem usou?', className='form-control'), md=3),
            dbc.Col(html.Button('Adicionar', id='btn-adicionar-cartao', className='btn btn-primary w-100'), md=2),
        ], className='mb-3 g-2'),

        dash_table.DataTable(
            id='tabela-cartoes',
            columns=[
                {'name': 'ID', 'id': 'id', 'editable': False},
                {'name': 'Nome', 'id': 'nome', 'editable': True},
                {'name': 'Valor', 'id': 'valor', 'editable': True},
                {'name': 'Pago', 'id': 'pago', 'editable': True},
                {'name': 'Quem Usou', 'id': 'quem_usou', 'editable': True},
                {'name': 'Data', 'id': 'data', 'editable': False},
            ],
            data=[],
            editable=True,
            row_deletable=True,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
        ),

        html.Div(id="mensagem-status-cartoes", className="text-center my-2 text-success"),

        html.Hr(className="my-4"),

        html.H4("Outros Gastos", className="mb-3 text-primary"),
        dbc.Row([
            dbc.Col(dcc.Input(id='nome-outro', type='text', placeholder='Nome', className='form-control'), md=6),
            dbc.Col(dcc.Input(id='valor-outro', type='number', placeholder='Valor', className='form-control'), md=4),
            dbc.Col(html.Button('Adicionar', id='btn-adicionar-outro', className='btn btn-primary w-100'), md=2),
        ], className='mb-3 g-2'),

        dash_table.DataTable(
            id='tabela-outros',
            columns=[
                {'name': 'ID', 'id': 'id', 'editable': False},
                {'name': 'Nome', 'id': 'nome', 'editable': True},
                {'name': 'Valor', 'id': 'valor', 'editable': True},
                {'name': 'Data', 'id': 'data', 'editable': False},
            ],
            data=[],
            editable=True,
            row_deletable=True,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
        ),

        html.Div(id="mensagem-status-outros", className="text-center my-2 text-success"),

        html.Hr(className="my-4"),


        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Evolução Financeira"),
                    dbc.CardBody([
                        dcc.Graph(id="grafico-evolucao-financeira", style={"height": "300px"})
                    ])
                ])
            ], md=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribuição de Gastos por Pessoa"),
                    dbc.CardBody([
                        dcc.Graph(id="grafico-por-pessoa", style={"height": "300px"})
                    ])
                ])
            ], md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Receitas x Despesas"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="grafico-receitas-despesas", 
                            style={"height": "300px"},
                            config={"displayModeBar": False}
                        )
                    ])
                ])
            ], md=12),
        ]),

        html.Div(style={"height": "50px"})
    ], fluid=True)

