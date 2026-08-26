import extrair_carac as ec
import train as tr
import numpy as np

def analisar_escrita(caminho):

    caracteristicas = ec.extrair_caracteristicas(
        caminho
    )

    caracteristicas = caracteristicas.reshape(1, -1)

    previsao = tr.modelo.predict(caracteristicas)[0]

    previsao = np.clip(previsao, 0, 1)

    legibilidade = previsao[0] * 100
    alinhamento = previsao[1] * 100
    forma = previsao[2] * 100
    tamanho = previsao[3] * 100

    nota_final = np.mean([
        legibilidade,
        alinhamento,
        forma,
        tamanho
    ])

    return {
        "legibilidade": legibilidade,
        "alinhamento": alinhamento,
        "forma": forma,
        "tamanho": tamanho,
        "nota_final": nota_final
    }

resultado = analisar_escrita("C:/Users/Camargo/Desktop/TCC/Machine Learning for Write/models/e01.png")

print(resultado)