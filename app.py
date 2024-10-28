from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# Cargar los archivos de Excel
def load_data():
    aeronaves_df = pd.read_excel('aeronaves.xlsx')
    componentes_df = pd.read_excel('componentes.xlsx')
    englimiter_df = pd.read_excel('englimiter.xlsx')
    return aeronaves_df, componentes_df, englimiter_df

@app.route('/')
def index():
    aeronaves_df, _, _ = load_data()
    aeronaves = aeronaves_df['Matricula'].tolist()
    return render_template('index.html', aeronaves=aeronaves)

@app.route('/aeronave/<matricula>')
def aeronave(matricula):
    print(f"Accediendo a la aeronave: {matricula}")  # Debugging
    aeronaves_df, componentes_df, englimiter_df = load_data()
    
    # Obtener el MSN de la matrícula seleccionada
    msn = aeronaves_df.loc[aeronaves_df['Matricula'] == matricula, 'MSN']
    if msn.empty:
        print(f"No se encontró MSN para la matrícula: {matricula}")  # Debugging
        return render_template('aeronave.html', matricula=matricula, motores=[])

    msn_value = msn.values[0]  # Obtener el valor del MSN

    # Filtrar componentes instalados
    motores_instalados = componentes_df[componentes_df['Depository'].str.startswith(str(msn_value))]
    print(f"Motores instalados encontrados para {matricula}: {len(motores_instalados)}")  # Debugging

    motores_info = []

    for _, motor in motores_instalados.iterrows():
        sn = motor['S/N']
        eng_data = englimiter_df[englimiter_df['S/N'] == sn]
        print(f"Buscando datos en englimiter para S/N: {sn}")  # Debugging

        if not eng_data.empty:
            eng_data = eng_data.iloc[0]
            motores_info.append({
                'P/N': motor['P/N'],
                'S/N': sn,
                'EGTLimit': eng_data['EGTLimit'],
                'LLPLimit': eng_data['LLPLimit'],
                'Status': motor['Status'],
                'TSO': motor['TSO'],
                'CSO': motor['CSO']
            })
            print(f"Motor encontrado: {motor['P/N']} con S/N: {sn}")  # Debugging
        else:
            print(f"No se encontraron datos de englimiter para S/N: {sn}")  # Debugging

    print(f"Información de motores para {matricula}: {motores_info}")  # Debugging

    return render_template('aeronave.html', matricula=matricula, motores=motores_info)

@app.route('/motores_desinstalados')
def motores_desinstalados():
    print("Accediendo a motores desinstalados")  # Debugging
    aeronaves_df, componentes_df, englimiter_df = load_data()

    # Asegurarse de que las columnas sean de tipo string
    componentes_df['S/N'] = componentes_df['S/N'].astype(str)
    componentes_df['Depository'] = componentes_df['Depository'].astype(str)
    englimiter_df['S/N'] = englimiter_df['S/N'].astype(str)

    # Eliminar espacios en blanco
    componentes_df['S/N'] = componentes_df['S/N'].str.strip()
    componentes_df['Depository'] = componentes_df['Depository'].str.strip()
    englimiter_df['S/N'] = englimiter_df['S/N'].str.strip()

    # Definir una expresión regular para validar el formato NNNNNLN
    pattern = r'^\d{5}[A-Z][0-9]$'  # 5 dígitos, 1 letra, 1 dígito al final

    # Filtrar motores desinstalados que no cumplen con el formato
    motores_desinstalados = componentes_df[~componentes_df['Depository'].str.match(pattern, na=False)]

    motores_info = []

    for _, motor in motores_desinstalados.iterrows():
        sn = motor['S/N']
        eng_data = englimiter_df[englimiter_df['S/N'] == sn]

        if not eng_data.empty:
            eng_data = eng_data.iloc[0]
            # Calcular Rem Limiter
            csn = motor['CSN']
            egt_limit = eng_data['EGTLimit']
            llp_limit = eng_data['LLPLimit']
            rem_limiter = min(egt_limit - csn, llp_limit - csn)

            motores_info.append({
                'P/N': motor['P/N'],
                'S/N': sn,
                'EGTLimit': egt_limit,
                'LLPLimit': llp_limit,
                'Status': motor['Status'],
                'TSO': motor['TSO'],
                'CSO': motor['CSO'],
                'TSN': motor['TSN'],
                'CSN': csn,
                'RemLimiter': rem_limiter  # Agregar el resultado de Rem Limiter
            })
        else:
            print(f"No se encontraron datos de englimiter para S/N: {sn}")  # Debugging

    print(f"Número de motores desinstalados encontrados: {len(motores_desinstalados)}")
    return render_template('motores_desinstalados.html', motores=motores_info)


if __name__ == '__main__':
    app.run(debug=True)
