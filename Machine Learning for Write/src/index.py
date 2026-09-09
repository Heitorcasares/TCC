import cv2
import numpy as np
from sklearn.cluster import DBSCAN


def dados_escrita(path):

    # Transformar imagem em cinza e depois converter para fundo preto e letra branca
    img = cv2.imread(path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, binaria = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    
    

    # Retirar características de toda a frase
    total, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binaria,
        connectivity=8
    )

    
    componentes = []
    
    altura, largura = binaria.shape
    

    

    for i in range(1, total):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        if area < 8:
            continue

        if area > altura * largura *0.05:
            continue

        componentes.append({
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "area": area
        })

    all_height = np.array([
        c["h"]
        for c in componentes
    ])

    all_width = np.array([
        c["w"]
        for c in componentes
    ])

    altura_mediana = np.median(all_height)
    altura_relativa = altura_mediana/altura

    variacao_altura = (
        np.std(all_height) / (np.mean(all_height) + 1e-8)
    )

    largura_relativa = np.median(all_width) / largura

    variacao_largura = (
        np.std(all_width) / (np.mean(all_width) + 1e-8)
    )

    if len(componentes) < 5:
        return []

    y = np.array([
        [c["y"]]
        for c in componentes
    ])

    x = np.array([
        [c["x"]]
        for c in componentes
    ])

    modelo = DBSCAN(
        eps = altura_mediana * 0.8,
        min_samples= 3
    )

    grupos = modelo.fit_predict(x, y)

    linhas = []

    for grupo in set(grupos):
        if grupo == -1:
            continue

        elementos = [
            componentes[i]
            for i in range (len(componentes))
            if grupos[i] == grupo
        ]

        if len(elementos) >= 3:
            linhas.append(elementos)

        inclinacoes = []
        erros = []

        for linha in linhas:

            if len(linha) < 3:
                continue

            X = np.array([
                [c["cx"]]
                for c in linha
            ]).reshape(-1, 1)

            Y = np.array([
                c["cy"]
                for c in linha
            ])

    

#print(dados_escrita("C:/Users/Camargo/Desktop/TCC/Machine Learning for Write/models/e01.png"))



