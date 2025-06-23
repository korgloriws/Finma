import sqlite3
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import dash_table
from datetime import date
from dash import callback_context
import plotly.express as px
import dash_bootstrap_components as dbc

def init_db():

    conn = sqlite3.connect('marmitas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marmitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            valor REAL,
            comprou INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


init_db()

def adicionar_marmita(data, valor, comprou):

    conn = sqlite3.connect('marmitas.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO marmitas (data, valor, comprou) VALUES (?, ?, ?)', (data, valor, comprou))
    conn.commit()
    conn.close()

def consultar_marmitas(mes=None, ano=None):

    conn = sqlite3.connect('marmitas.db')
    cursor = conn.cursor()
    
    if mes and ano:
        query = 'SELECT * FROM marmitas WHERE strftime("%m", data) = ? AND strftime("%Y", data) = ?'
        cursor.execute(query, (mes.zfill(2), str(ano)))
        registros = cursor.fetchall()
    else:
        registros = [] 
    
    conn.close()
    return registros

def remover_marmita(id_marmita):

    conn = sqlite3.connect('marmitas.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM marmitas WHERE id = ?', (id_marmita,))
    conn.commit()
    conn.close()

PERIODOS = [
    {"label": "6 meses", "value": "6m"},
    {"label": "1 ano", "value": "1y"},
    {"label": "Tudo", "value": "all"},
]

def gastos_mensais(periodo="6m"):
    conn = sqlite3.connect('marmitas.db')
    df = pd.read_sql_query('SELECT data, valor FROM marmitas WHERE comprou=1', conn, parse_dates=['data'])
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["AnoMes", "valor"])
    df['AnoMes'] = df['data'].dt.to_period('M').astype(str)
    df_group = df.groupby('AnoMes')['valor'].sum().reset_index()
    # Filtro de período
    if periodo != "all":
        n = 6 if periodo == "6m" else 12
        df_group = df_group.tail(n)
    return df_group

def layout():
    return html.Div([
        html.H2("Controle de Marmitas", className="mb-4 text-center fw-bold text-primary"),
        dbc.Row([
            dbc.Col([
                dcc.DatePickerSingle(id='input-data-marmita', date=date.today()),
                dcc.Input(id='input-valor-marmita', type='number', placeholder='Valor da Marmita', min=0, style={"width": "150px", "marginLeft": "10px"}),
                dcc.RadioItems(
                    id='input-comprou-marmita', 
                    options=[{'label': 'Sim', 'value': 1}, {'label': 'Não', 'value': 0}], 
                    value=1, 
                    inline=True,
                    style={"marginLeft": "10px"}
                ),
                html.Button('Adicionar Marmita', id='button-adicionar-marmita', n_clicks=0, className="btn btn-success ms-2"),
            ], width=12, className="mb-3 d-flex align-items-center justify-content-center"),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='filtro-mes', 
                    options=[{'label': mes, 'value': str(i+1).zfill(2)} for i, mes in enumerate([
                        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 
                        'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
                    ])], 
                    placeholder="Selecione o Mês",
                    style={"width": "180px"}
                ),
                dcc.Input(id='filtro-ano', type='number', placeholder='Ano', value=date.today().year, style={"width": "100px", "marginLeft": "10px"}),
            ], width=6, className="mb-2 d-flex align-items-center"),
            dbc.Col([
                html.Label("Período do gráfico:", className="fw-bold me-2"),
                dcc.Dropdown(
                    id="grafico-periodo-marmita",
                    options=PERIODOS,
                    value="6m",
                    clearable=False,
                    style={"width": "150px", "display": "inline-block"}
                ),
            ], width=6, className="mb-2 d-flex align-items-center justify-content-end"),
        ]),
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(
                    id='tabela-marmitas', 
                    columns=[{'name': 'Data', 'id': 'data'}, {'name': 'Valor', 'id': 'valor'}, {'name': 'Comprou', 'id': 'comprou'}], 
                    editable=True, 
                    row_deletable=True, 
                    style_table={'overflowX': 'auto', 'backgroundColor': '#fff'},
                    style_cell={'textAlign': 'center', 'fontFamily': 'Segoe UI', 'fontSize': 15},
                    style_header={'backgroundColor': '#007bff', 'color': 'white', 'fontWeight': 'bold'},
                ),
                html.H4(id='valor-total-marmitas', className="mt-3 text-success fw-bold text-end"),
            ], width=7),
            dbc.Col([
                html.Div(id="cards-resumo-marmita"),
                html.Div(id="grafico-marmita"),
            ], width=5),
        ], className="mt-4"),
    ], className="container-fluid animate__animated animate__fadeIn")

def registrar_callbacks(app):
    @app.callback(
        [Output('tabela-marmitas', 'data'),
         Output('valor-total-marmitas', 'children'),
         Output('cards-resumo-marmita', 'children'),
         Output('grafico-marmita', 'children')],
        [Input('button-adicionar-marmita', 'n_clicks'),
         Input('tabela-marmitas', 'data_previous'),
         Input('filtro-mes', 'value'),
         Input('filtro-ano', 'value'),
         Input('grafico-periodo-marmita', 'value'),
         Input('switch-darkmode', 'value')],
        [State('input-data-marmita', 'date'),
         State('input-valor-marmita', 'value'),
         State('input-comprou-marmita', 'value'),
         State('tabela-marmitas', 'data')]
    )
    def gerenciar_marmitas(n_clicks, data_anterior, mes, ano, periodo_grafico, is_dark, data, valor, comprou, data_atual):
        registros = []
        if n_clicks > 0 and data and comprou is not None:
            adicionar_marmita(data, valor if comprou == 1 else 0, comprou)
        if data_anterior:
            ids_anteriores = [row['id'] for row in data_anterior if 'id' in row]
            ids_atuais = [row['id'] for row in data_atual if 'id' in row]
            ids_deletados = list(set(ids_anteriores) - set(ids_atuais))
            for id_deletado in ids_deletados:
                remover_marmita(id_deletado)
        if mes and ano:
            registros = consultar_marmitas(mes, ano)
        else:
            registros = consultar_marmitas()
        registros_formatados = formatar_dados_marmitas(registros)
        df_marmitas = pd.DataFrame(registros_formatados)
        total_gasto = df_marmitas['valor'].sum() if not df_marmitas.empty else 0
        # Cards de resumo
        df_graf = gastos_mensais(periodo_grafico)
        if not df_graf.empty:
            maior = df_graf['valor'].max()
            menor = df_graf['valor'].min()
            media = df_graf['valor'].mean()
            mes_maior = df_graf.loc[df_graf['valor'].idxmax(), 'AnoMes']
            mes_menor = df_graf.loc[df_graf['valor'].idxmin(), 'AnoMes']
        else:
            maior = menor = media = mes_maior = mes_menor = 0
        cards = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Total no período", className="text-muted"),
                    html.H4(f"R$ {df_graf['valor'].sum():,.2f}" if not df_graf.empty else "R$ 0,00", className="fw-bold text-primary")
                ])
            ], className="mb-2 shadow-sm")),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Média mensal", className="text-muted"),
                    html.H4(f"R$ {media:,.2f}" if not df_graf.empty else "R$ 0,00", className="fw-bold text-info")
                ])
            ], className="mb-2 shadow-sm")),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Maior mês", className="text-muted"),
                    html.H4(f"{mes_maior} - R$ {maior:,.2f}" if not df_graf.empty else "-", className="fw-bold text-danger")
                ])
            ], className="mb-2 shadow-sm")),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Menor mês", className="text-muted"),
                    html.H4(f"{mes_menor} - R$ {menor:,.2f}" if not df_graf.empty else "-", className="fw-bold text-success")
                ])
            ], className="mb-2 shadow-sm")),
        ], className="g-2 mb-3")
        # Gráfico
        template = "plotly_dark" if is_dark else "simple_white"
        if not df_graf.empty:
            fig = px.bar(df_graf, x='AnoMes', y='valor', text_auto='.2s', title="Gasto com Marmitas por Mês", color='valor', color_continuous_scale='Blues', template=template)
            fig.update_layout(
                xaxis_title="Mês", yaxis_title="Gasto (R$)", hovermode='x unified',
                coloraxis_showscale=False
            )
            grafico = dcc.Graph(figure=fig, config={'displayModeBar': False})
        else:
            grafico = html.Div("Sem dados para o período selecionado.", className="text-muted")
        return registros_formatados, f"Total gasto no mês: R$ {total_gasto:,.2f}", cards, grafico

def formatar_dados_marmitas(registros):

    dados_formatados = []
    for registro in registros:
        dados_formatados.append({
            'id': registro[0], 
            'data': registro[1],
            'valor': registro[2],
            'comprou': 'Sim' if registro[3] == 1 else 'Não'
        })
    return dados_formatados
