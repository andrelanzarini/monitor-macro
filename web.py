from flask import Flask, render_template_string
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Usa um backend não interativo
import matplotlib.pyplot as plt
import io
import base64
import os
from sqlalchemy import create_engine

app = Flask(__name__)
engine = create_engine("sqlite:///dados.db")

def generate_risk_chart(risk_data):
    if risk_data.empty:
        return None

    plt.figure(figsize=(10, 5))
    plt.plot(risk_data['Time'], risk_data['Alta'], label='Alta', color='green')
    plt.plot(risk_data['Time'], risk_data['Queda'], label='Queda', color='red')
    plt.plot(risk_data['Time'], risk_data['Neutro'], label='Neutro', color='gray', linestyle='dashed')

    plt.title(f"Monitor do Dólar - {datetime.today().strftime('%d-%m-%Y')}")
    plt.xlabel('Hora')
    plt.ylabel('Quantidade')
    plt.legend()
    plt.xticks(rotation=90)
    plt.ylim(0, 40)
    plt.tight_layout()

    today = datetime.today().strftime('%Y-%m-%d')
    img = io.BytesIO()
    plt.savefig(f"static/{today}_graf.png", format='png')
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode()

@app.route('/')
def index():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM risk_data WHERE Date = date('now') ORDER BY Time ASC", conn)

    if df.empty:
        df = pd.DataFrame(columns=['Date', 'Time', 'Alta', 'Queda', 'Neutro'])
    
    today = datetime.today().strftime('%Y-%m-%d')
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d').dt.strftime('%d-%m-%Y')
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.strftime('%H:%M')
    
    if not df['Time'].empty:
        max_time = datetime.strptime(df['Time'].max(), '%H:%M')
        extra_times = [(max_time + timedelta(minutes=5 * i)).strftime('%H:%M') for i in range(1, 21)]
        extra_df = pd.DataFrame({'Time': extra_times, 'Alta': [None]*20, 'Queda': [None]*20, 'Neutro': [None]*20})
        df = pd.concat([df, extra_df], ignore_index=True, sort=False)
    
    graph_url = generate_risk_chart(df)

    image_files = [f for f in os.listdir('static') if f.endswith('_graf.png')]
    image_files.sort(reverse=True)
    image_files = image_files[:31]  # Limitar a 31 imagens no máximo

    image_table = "<table border='1' style='width: 100%; text-align: center;'><tr>"
    for i, img in enumerate(image_files):
        if i > 0 and i % 6 == 0:
            image_table += "</tr><tr>"
        image_table += f"<td><a href='static/{img}' target='_blank'>{img}</a></td>"
    image_table += "</tr></table>"
    
    html = f"""
    <html>
        <head>
            <meta http-equiv="refresh" content="300">
            <style>
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid black; padding: 8px; text-align: center; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <img src="data:image/png;base64,{graph_url}"/>
            <h3>Últimos Gráficos:</h3>
            {image_table}
            <h3>Dados Coletados Yahoo Finance</h3>
            <table>
                <tr>
                    {''.join(f"<th>{col}</th>" for col in df.columns)}
                </tr>
                {''.join(f"<tr>{''.join(f'<td>{row[col]}</td>' if pd.notna(row[col]) else '<td></td>' for col in df.columns)}</tr>" for _, row in df.iterrows())}
            </table>
        </body>
    </html>
    """
    return render_template_string(html)
  
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

