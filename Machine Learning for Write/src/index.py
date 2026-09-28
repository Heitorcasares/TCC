import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.linear_model import LinearRegression
from skimage.feature import hog
import pandas as pd
from skimage.morphology import skeletonize 


def normalizar(valor, referencia):
    return float(np.clip(valor / referencia, 0, 1))

def dados_escrita(path):

    # Transformar imagem em cinza e depois converter para fundo preto e letra branca
    img = cv2.imread(path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _ , binaria = cv2.threshold(
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

    tamanho_letra = normalizar(
        altura_relativa,
        referencia=0.10
    )

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

    grupos = modelo.fit_predict(y)

    linhas = []
    espacamento = []

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
        desvios = []

        for linha in linhas:

            print("Bão")
            
            if len(linha) < 3:
                continue

            X = np.array([
                [c["x"]]
                for c in linha
            ]).reshape(-1, 1)

            Y = np.array([
                c["y"]
                for c in linha
            ])

            regressao = LinearRegression()
            regressao.fit(X, Y)

            esperado = regressao.predict(X)

            residuos = Y - esperado

            desvio = np.std(residuos)

            desvios.append(desvio)

            desvio_linha = np.mean(desvios)


            erro = (
                np.std(residuos) / (altura_mediana + 1e-8)
            )

            inclinacoes.append(
                abs(regressao.coef_[0])
            )

            erros.append(erro)

            erro_relativo = (
                np.sqrt(np.mean(residuos ** 2)) / altura_mediana
            )

            alinhamento = np.exp(
                -np.log(2) * erro_relativo / 0.15
            )

            l = sorted(linha, key=lambda c: c["x"])

            

            for i in range(len(linha) - 1):
                
                atual = linha[i]
                proxima = linha[i + 1]

                espaco = proxima["x"] - (
                    atual["x"] + atual["w"]
                )

                espacamento.append(espaco)

                espacos = np.maximum(
                    0,
                    espacamento
                )

                espaco_relativo = np.median(espacos) / altura_mediana

                espacamento_def = normalizar(
                    espaco_relativo,
                    referencia=0.50
                )

        if not erros:
            erros = [0, 0, 0, 0]

        media_erros = np.mean(erros)
        difereca_erros = np.std(erros)
        media_inclinacoes = np.mean(inclinacoes)
        diferenca_inclinacoes = np.std(inclinacoes)



        imagem = cv2.resize(gray, (256, 256))

        caracteristicas = hog(
            imagem,
            orientations = 9,
            pixels_per_cell = (16, 16),
            cells_per_block = (1, 1),
            feature_vector = False
        )

        caracteristicas = caracteristicas.reshape(-1, 9)

        medias = caracteristicas.mean(axis=0)
        desvios = caracteristicas.std(axis=0)

        medias_desvios = np.concatenate([medias, desvios])

        densidade = (np.count_nonzero(binaria) / binaria.size)

        densidades = [
            c["area"] / (c["w"] * c["h"])
            for c in componentes
        ]

        grossura_traco = np.median(densidades)

        quantidade_componentes = (len(componentes) / (largura * altura))

        areas = np.array([
            c["area"]
            for c in componentes
        ])

        if len(areas) == 0:
            areas = [0, 0, 0]

        variacao_area = (
            np.std(areas) / (np.mean(areas) + 1e-8)
        )

        distancias = cv2.distanceTransform(
            binaria,
            cv2.DIST_L2,
            cv2.DIST_MASK_PRECISE
        )

        esqueleto = skeletonize(binaria > 0)

        grossura_px = np.median(
            2 * distancias[esqueleto]
        )

        grossura_relativa = grossura_px / altura_mediana

        grossura = normalizar(
            grossura_relativa,
            referencia=0.20
        )

        regularidade_altura = np.exp(-variacao_altura)

        variacao_espacamento = (
            np.std(espaco_relativo) / (np.mean(espaco_relativo) + 1e-8)
        )
        
        regularidade_espacamento = np.exp(
            -variacao_espacamento
        )

        legibilidade_estimada = (
            0.50 * alinhamento + 0.30 * regularidade_altura + 0.20 * regularidade_espacamento
        )
        

        return ({
            "Legibilidade Estimada": legibilidade_estimada * 100,
            "Tamanho da Letra": tamanho_letra * 100,
            "Se está na mesma linha": alinhamento * 100,
            "esçamento entre letras": espacamento_def * 100,
            "Grossura do Traço": grossura * 100
        })



        

        

    

print(pd.DataFrame([dados_escrita("models/e01.png")]))

tabela_dados = pd.DataFrame([dados_escrita("models/e01.png")])

tabela_dados.to_csv("Dados.csv", index=False)
tabela_dados.to_excel("Dados.xlsx", index=False)



