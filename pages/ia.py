# pages/ia.py

import pandas as pd
from dash import html
import dash_bootstrap_components as dbc
from pages.carteira import consultar_carteira, consultar_historico

from datetime import date

def gerar_insights():
    df = pd.DataFrame(consultar_carteira())
    insights = []

    if df.empty:
        return ["Nenhum dado na carteira atual."]

 
    tipo_distrib = df['tipo'].value_counts(normalize=True)
    for tipo, proporcao in tipo_distrib.items():
        if proporcao > 0.6:
            insights.append(f"🟥 Mais de {int(proporcao*100)}% da carteira está concentrada em {tipo}s. Avalie diversificação.")
        elif proporcao > 0.4:
            insights.append(f"🟨 {int(proporcao*100)}% da carteira está em {tipo}s. Atenção ao equilíbrio.")
        else:
            insights.append(f"🟩 Diversificação saudável em {tipo}s.")


    top_ativo = df.nlargest(1, 'valor_total')
    if not top_ativo.empty:
        ativo = top_ativo.iloc[0]
        insights.append(f"🟨 O ativo com maior posição é {ativo['ticker']} com R$ {ativo['valor_total']:.2f}.")


    for indicador in ['dy', 'pl', 'pvp', 'roe']:
        media = df[indicador].mean()
        if not pd.isna(media):
            insights.append(f"📊 Média de {indicador.upper()}: {media:.2f}")

 
    df_hist = consultar_historico('mensal')
    if not df_hist.empty:
        df_hist = df_hist.sort_values("data")
        inicial = df_hist.iloc[0]['valor_total']
        final = df_hist.iloc[-1]['valor_total']
        variacao = final - inicial
        pct = (variacao / inicial) * 100 if inicial else 0
        cor = "🟩" if pct >= 0 else "🟥"
        insights.append(f"{cor} A carteira variou {pct:.2f}% no último mês.")

    return insights


def layout():
    insights = gerar_insights()

    cards = [
        dbc.Card(dbc.CardBody(html.P(item)), className="mb-3")
        for item in insights
    ]

    return dbc.Container([
        html.H5("📊 Insignts da Carteira", className="text-center my-4"),
        html.Div(cards)
    ], fluid=True)


def registrar_callbacks(app):
    pass  
