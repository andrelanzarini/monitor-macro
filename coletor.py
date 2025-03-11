import yfinance as yf
from flask import Flask, render_template_string
from datetime import datetime
import sqlite3
import time
import pandas as pd
from sqlalchemy import create_engine

# Lista de ativos de risco
symbols_risk = [
    'GC=F', 'HG=F', 'CL=F', 'PBR', 'VALE', 'EWZ', 'XLF', 'XLE', 'XLP', 'XME',
    '^BSESN', 'OSEAX.OL', 'ZS=F', 'SOXX', '^DJI', 'EEM', '^GDOW'
]

# Lista de ativos de segurança
symbols_security = [
    'DX=F', '^VIX', 'MXN=X', 'NOK=X', 'NZD=X', 'AUD=X', 'KRW=X', 'CNY=X', 'EURUSD=X'
]

# Lista de ativos com cotação de pré-abertura disponível
pre_market_symbols = {'PBR', 'VALE', 'EWZ', 'XLF', 'XLE', 'XLP', 'XME', 'SOXX', 'EEM'}

# Criar conexão com SQLite
engine = create_engine("sqlite:///dados.db")

def store_data(df):
    with engine.connect() as conn:
        df.to_sql("risk_data", conn, if_exists="append", index=False)

def get_stock_signal(symbol):
    stock = yf.Ticker(symbol)
    past_data = stock.history(period="2d")
    yesterday_close = past_data['Close'].iloc[-2] if len(past_data) >= 2 else None

    pre_market_price = stock.info.get('preMarketPrice') if symbol in pre_market_symbols else None
    reference_price = pre_market_price if pre_market_price else yesterday_close
    
    percentage_change = stock.info.get("regularMarketChangePercent") if reference_price else None
    
    if stock in symbols_risk:
        signal = 'Q' if percentage_change and percentage_change > 0.30 else 'A' if percentage_change and percentage_change < -0.30 else 'N'
    else:
        signal = 'A' if percentage_change and percentage_change > 0.30 else 'Q' if percentage_change and percentage_change < -0.30 else 'N'
    
    return signal

def get_risk_data():
    qtde_alta = 0
    qtde_queda = 0
    qtde_neutro = 0
    
    for symbol in symbols_risk + symbols_security:
        signal = get_stock_signal(symbol)
        if signal == 'A':
            qtde_alta += 1
        elif signal == 'Q':
            qtde_queda += 1
        else:
            qtde_neutro += 1
    
    return {
        'Date': datetime.today().strftime('%Y-%m-%d'),
        'Time': datetime.now().strftime('%H:%M:%S'),
        'Alta': qtde_alta,
        'Queda': qtde_queda,
        'Neutro': qtde_neutro
    }

while True:
    data = [get_risk_data()]
    print("Linha coletada:", data)  # Adicionando print para debug
    df = pd.DataFrame(data)
    store_data(df)
    time.sleep(300)  # Aguarda 5 minutos antes da próxima coleta

