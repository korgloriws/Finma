from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output
import re

def extract_ticker_clean(ticker_value):
    """Extrai o ticker limpo de dados que podem conter HTML"""
    if isinstance(ticker_value, str) and '<div' in ticker_value:
        # Se contém HTML, extrair o ticker do span
        match = re.search(r'<span[^>]*>([^<]+)</span>', ticker_value)
        if match:
            return match.group(1)
    return ticker_value

def clean_ticker_column(df):
    """Limpa a coluna ticker removendo HTML se necessário"""
    if 'ticker' in df.columns:
        df['ticker_clean'] = df['ticker'].apply(extract_ticker_clean)
    return df

def layout(df_ativos=None):
    config = {'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines', 'sendDataToCloud']}


    tipos = sorted(df_ativos['tipo'].dropna().unique()) if 'tipo' in df_ativos else []
    setores = sorted(df_ativos['setor'].dropna().unique()) if 'setor' in df_ativos else []

    filtros = dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='filtro-tipo',
                options=[],
                placeholder='Filtrar por tipo',
                clearable=True,
                style={'marginBottom': '8px'}
            )
        ], md=4),
        dbc.Col([
            dcc.Dropdown(
                id='filtro-setor',
                options=[],
                placeholder='Filtrar por setor',
                clearable=True,
                style={'marginBottom': '8px'}
            )
        ], md=8),
    ], className='mb-2')


    return html.Div([
        html.H2("Oportunidades e Indicadores", className="mb-3 mt-2 text-center"),
        filtros,
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Heatmap de Correlação dos Indicadores", className="card-header-heatmap"),
                    dbc.CardBody([
                        dcc.Graph(id='heatmap-correlacao')
                    ], className="card-body-heatmap")
                ]),
                width=12
            )
        ]),
        html.Div(id='graficos-oportunidades-filtrados'),
    ])

def register_callbacks(app):
    @app.callback(
        Output('heatmap-correlacao', 'figure'),
        [Input('ativos-filtrados-store', 'data'), Input('switch-darkmode', 'value')]
    )
    def atualizar_heatmap(dados, is_dark):
        if not dados:
            return go.Figure()
        df_ativos = pd.DataFrame(dados)
        indicadores = ['preco_atual', 'pl', 'pvp', 'roe', 'dividend_yield']
        df_corr = df_ativos[indicadores].corr() if not df_ativos.empty else pd.DataFrame()
        template = 'plotly_dark' if is_dark else 'simple_white'
        if not df_corr.empty:
            fig_heatmap = px.imshow(
                df_corr,
                text_auto=True,
                color_continuous_scale='RdBu',
                zmin=-1, zmax=1,
                aspect='auto',
                title='Correlação entre Indicadores',
                template=template
            )
        else:
            fig_heatmap = go.Figure()
        return fig_heatmap

    @app.callback(
        Output('graficos-oportunidades-filtrados', 'children'),
        [Input('filtro-tipo', 'value'), Input('filtro-setor', 'value'), Input('ativos-filtrados-store', 'data'), Input('switch-darkmode', 'value')]
    )
    def atualizar_graficos_filtrados(tipo, setor, dados, is_dark):
        if not dados:
            return html.Div("Sem dados para exibir.", className="text-muted p-4")
        df = pd.DataFrame(dados)
        
        # Limpa a coluna ticker se necessário
        df = clean_ticker_column(df)
        
        if tipo:
            df = df[df['tipo'] == tipo]
        if setor:
            df = df[df['setor'] == setor]
        config = {'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines', 'sendDataToCloud']}
        template = 'plotly_dark' if is_dark else 'simple_white'

    
        fig_scatter = px.scatter(
            df.dropna(subset=['pl', 'dividend_yield', 'ticker_clean']),
            x='pl', y='dividend_yield',
            color='setor' if 'setor' in df else 'tipo',
            hover_data=['ticker_clean', 'nome_completo', 'roe'],
            title='P/L vs Dividend Yield',
            labels={'pl': 'P/L', 'dividend_yield': 'Dividend Yield (%)'},
            size_max=18,
            template=template,
            color_discrete_sequence=px.colors.qualitative.Safe
        ) if not df.empty and 'pl' in df and 'dividend_yield' in df else px.scatter(title='P/L vs Dividend Yield', template=template)

        if not df.empty and 'pl' in df and 'dividend_yield' in df:
            if not df.dropna(subset=['pl', 'dividend_yield']).empty:
                ideal = df.loc[df['dividend_yield'] == df['dividend_yield'].max()]
                if not ideal.empty:
                    fig_scatter.add_trace(go.Scatter(
                        x=ideal['pl'], y=ideal['dividend_yield'],
                        mode='markers+text',
                        marker=dict(size=22, color='gold', symbol='star'),
                        text=ideal['ticker_clean'],
                        textposition='top center',
                        name='Destaque',
                        showlegend=True
                    ))
        fig_scatter.update_layout(
            xaxis_title="P/L", yaxis_title="Dividend Yield (%)", hovermode='closest',
            legend=dict(bgcolor='rgba(255,255,255,0.7)' if not is_dark else 'rgba(40,40,40,0.7)', bordercolor='#007bff', borderwidth=1)
        )
        fig_scatter.update_traces(marker=dict(size=14, line=dict(width=1, color='#222')), selector=dict(mode='markers'))


        top_dy = df.nlargest(3, 'dividend_yield') if 'dividend_yield' in df else pd.DataFrame()
        top_roe = df.nlargest(3, 'roe') if 'roe' in df else pd.DataFrame()
        top_pl = df.nsmallest(3, 'pl') if 'pl' in df else pd.DataFrame()
        def highlight_bar(fig, top_df, y_col, color):
            if not top_df.empty:
                fig.add_trace(go.Bar(
                    x=[top_df.iloc[0]['ticker_clean']],
                    y=[top_df.iloc[0][y_col]],
                    marker_color=color,
                    name='Destaque',
                    showlegend=True,
                    marker_line_width=3,
                    marker_line_color='#222',
                ))
        fig_bar_dy = px.bar(
            top_dy.iloc[::-1],
            x='ticker_clean', y='dividend_yield',
            color='setor' if 'setor' in top_dy else 'tipo',
            title='TOP 3 Dividend Yield',
            labels={'dividend_yield': 'Dividend Yield (%)'},
            color_discrete_sequence=px.colors.sequential.Blues,
            template=template
        ) if not top_dy.empty else px.bar(title='TOP 3 Dividend Yield', template=template)
        highlight_bar(fig_bar_dy, top_dy, 'dividend_yield', 'gold')
        fig_bar_dy.update_layout(
            xaxis_title="Ticker", yaxis_title="Dividend Yield (%)", hovermode='x unified',
            showlegend=True, legend=dict(bgcolor='rgba(255,255,255,0.7)' if not is_dark else 'rgba(40,40,40,0.7)', bordercolor='#007bff', borderwidth=1)
        )
        fig_bar_roe = px.bar(
            top_roe.iloc[::-1],
            x='ticker_clean', y='roe',
            color='setor' if 'setor' in top_roe else 'tipo',
            title='TOP 3 ROE',
            labels={'roe': 'ROE (%)'},
            color_discrete_sequence=px.colors.sequential.Purples,
            template=template
        ) if not top_roe.empty else px.bar(title='TOP 3 ROE', template=template)
        highlight_bar(fig_bar_roe, top_roe, 'roe', 'gold')
        fig_bar_roe.update_layout(
            xaxis_title="Ticker", yaxis_title="ROE (%)", hovermode='x unified',
            showlegend=True, legend=dict(bgcolor='rgba(255,255,255,0.7)' if not is_dark else 'rgba(40,40,40,0.7)', bordercolor='#007bff', borderwidth=1)
        )
        fig_bar_pl = px.bar(
            top_pl.iloc[::-1],
            x='ticker_clean', y='pl',
            color='setor' if 'setor' in top_pl else 'tipo',
            title='TOP 3 Menor P/L',
            labels={'pl': 'P/L'},
            color_discrete_sequence=px.colors.sequential.Greens,
            template=template
        ) if not top_pl.empty else px.bar(title='TOP 3 Menor P/L', template=template)
        highlight_bar(fig_bar_pl, top_pl, 'pl', 'gold')
        fig_bar_pl.update_layout(
            xaxis_title="Ticker", yaxis_title="P/L", hovermode='x unified',
            showlegend=True, legend=dict(bgcolor='rgba(255,255,255,0.7)' if not is_dark else 'rgba(40,40,40,0.7)', bordercolor='#007bff', borderwidth=1)
        )


        df_score = df.copy()
        if not df_score.empty and all(col in df_score for col in ['dividend_yield', 'roe', 'pl']):

            dy_min, dy_max = df_score['dividend_yield'].min(), df_score['dividend_yield'].max()
            roe_min, roe_max = df_score['roe'].min(), df_score['roe'].max()
            pl_min, pl_max = df_score['pl'].min(), df_score['pl'].max()
            df_score['dy_norm'] = (df_score['dividend_yield'] - dy_min) / (dy_max - dy_min) if dy_max != dy_min else 1
            df_score['roe_norm'] = (df_score['roe'] - roe_min) / (roe_max - roe_min) if roe_max != roe_min else 1
            df_score['pl_norm'] = (pl_max - df_score['pl']) / (pl_max - pl_min) if pl_max != pl_min else 1  # menor P/L é melhor
            df_score['score'] = df_score['dy_norm'] + df_score['roe_norm'] + df_score['pl_norm']
            top_score = df_score.nlargest(3, 'score')
            fig_score = px.bar(
                top_score.iloc[::-1],
                x='ticker_clean', y='score',
                color='setor' if 'setor' in top_score else 'tipo',
                title='TOP 3 Score de Oportunidade',
                labels={'score': 'Score'},
                template=template
            )
        else:
            fig_score = px.bar(title='TOP 3 Score de Oportunidade', template=template)


        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_scatter, config=config), md=6),
            dbc.Col(dcc.Graph(figure=fig_bar_dy, config=config), md=6),
            dbc.Col(dcc.Graph(figure=fig_bar_roe, config=config), md=6),
            dbc.Col(dcc.Graph(figure=fig_bar_pl, config=config), md=6),
            dbc.Col(dcc.Graph(figure=fig_score, config=config), md=12),
        ])

    @app.callback(
        [
            Output('pie-chart-setor-geral', 'figure'),
            Output('pie-chart-pais-geral', 'figure'),
            Output('pie-chart-industria-geral', 'figure'),
            Output('pie-chart-setor-acoes', 'figure'),
            Output('pie-chart-pais-acoes', 'figure'),
            Output('pie-chart-industria-acoes', 'figure'),
            Output('pie-chart-setor-bdrs', 'figure'),
            Output('pie-chart-pais-bdrs', 'figure'),
            Output('pie-chart-industria-bdrs', 'figure'),
            Output('pie-chart-setor-fiis', 'figure'),
            Output('pie-chart-pais-fiis', 'figure'),
            Output('pie-chart-industria-fiis', 'figure')
        ],
        [Input("ativos-filtrados-store", "data"), Input("switch-darkmode", "value")]
    )
    def atualizar_graficos(dados, is_dark):
        if not dados:
            return [{}] * 12
        df_ativos = pd.DataFrame(dados)
        template = 'plotly_dark' if is_dark else 'simple_white'
        return (
            px.pie(df_ativos, names='setor', title="Distribuição por Setor (Geral)", template=template),
            px.pie(df_ativos, names='pais', title="Distribuição por País (Geral)", template=template),
            px.pie(df_ativos, names='industria', title="Distribuição por Indústria (Geral)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'Ação'], names='setor', title="Setor (Ações)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'Ação'], names='pais', title="País (Ações)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'Ação'], names='industria', title="Indústria (Ações)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'BDR'], names='setor', title="Setor (BDRs)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'BDR'], names='pais', title="País (BDRs)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'BDR'], names='industria', title="Indústria (BDRs)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'FII'], names='setor', title="Setor (FIIs)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'FII'], names='pais', title="País (FIIs)", template=template),
            px.pie(df_ativos[df_ativos['tipo'] == 'FII'], names='industria', title="Indústria (FIIs)", template=template)
        )

    @app.callback(
        Output('filtro-tipo', 'options'),
        Input('ativos-filtrados-store', 'data')
    )
    def atualizar_opcoes_tipo(dados):
        if not dados:
            return []
        df = pd.DataFrame(dados)
        tipos = sorted(df['tipo'].dropna().unique()) if 'tipo' in df else []
        return [{'label': t, 'value': t} for t in tipos]

    @app.callback(
        Output('filtro-setor', 'options'),
        Input('ativos-filtrados-store', 'data')
    )
    def atualizar_opcoes_setor(dados):
        if not dados:
            return []
        df = pd.DataFrame(dados)
        setores = sorted(df['setor'].dropna().unique()) if 'setor' in df else []
        return [{'label': s, 'value': s} for s in setores]
