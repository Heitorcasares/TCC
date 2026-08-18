import cv2 
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.linear_model import LinearRegression
from skimage.feature import hog


def upload_imagem(imagem):
    img = cv2.imread(imagem)

    if imagem is None:
        raise ValueError("Faça o upload da imagem!")

    togray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    altura, largura = togray.shape

    nova_largura = 1200
    escala = nova_largura / largura
    nova_altura = int(altura * escala)

    togray = cv2.resize(togray, (nova_largura, nova_altura))

    _, binaria = cv2.threshold(
        togray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    return togray, binaria

def encontrar_objetos(binaria):

    total, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            binaria,
            connectivity=8
        )
    )

    components = []

    altura_bi, largura_bi = binaria.shape

    for i in range(1, total):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        if area < 8:
            continue

        if area > altura_bi * largura_bi * 0.05:
            continue

        components.append({
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "area": area
        })

    return components

def caracteristicas_tamanho(componentes, image_shape):

    altura_img, largura_img = image_shape.shape

    alturas = np.array([
        c["h"]
        for c in componentes
    ])

    larguras = np.array([
        c["w"]
        for c in componentes
    ])

    altura_medianas = np.median(alturas)
    altura_relativa = altura_medianas/altura_img

    variacao_altura = (
        np.std(alturas) / (np.mean(alturas) + 1e-8)
    )

    largura_relativa = (
        np.median(larguras) / largura_img
    )

    variacao_largura = (
        np.std(larguras) / (np.mean(larguras) + 1e-8)
    )

    return [
        altura_relativa,
        variacao_altura,
        largura_relativa,
        variacao_largura
    ]

def detectar_linhas(componentes):
    if len(componentes) < 5:
        return []

    alturas = np.array([
        c["h"] for c in componentes
    ])

    altura_mediana = np.median(alturas)

    coordenadas_y = np.array([
        [c["cy"]]
        for c in componentes
    ])

    modelo = DBSCAN(
        eps=altura_mediana * 0.8,
        min_samples=3
    )

    grupos = modelo.fit_predict(coordenadas_y)

    linhas = []

    for grupo in set(grupos):
        if grupo == -1:
            continue

        elementos = [
            componentes[i]
            for i in range(len(componentes))
            if grupos[i] == grupo
        ]

        if len(elementos) >= 3:
            linhas.append(elementos)

    return linhas

def caracteristicas_alinhamento(linhas):

    inclinacoes = []
    erros = []

    for linha in linhas:

        if len(linha) < 3:
            continue

        X = np.array([
            [c["cx"]] for c in linha
        ]).reshape(-1, 1)

        y = np.array([
            c["cy"] for c in linha
        ])

        regressao = LinearRegression()
        regressao.fit(X, y)

        esperado = regressao.predict(X)

        residuos = y - esperado

        altura_mediana = np.median([
            c["h"] for c in linha
        ])

        erro = (
            np.std(residuos) / (altura_mediana + 1e-8)
        )

        inclinacoes.append(
            abs(regressao.coef_[0])
        )

        erros.append(erro)

    if not erros:
        return [0, 0, 0, 0]

    return [
        np.mean(erros),
        np.std(erros),
        np.mean(inclinacoes),
        np.std(inclinacoes)
    ]

def caracteristicas_hog(gray):

    imagem = cv2.resize(gray, (256, 256))

    caracteristicas, = hog(
        imagem,
        orientations=9,
        pixels_per_cell=(16, 16),
        cells_per_block=(1, 1),
        feature_vector=False
    )

    caracteristicas = caracteristicas.reshape(-1, 9)

    medias = caracteristicas.mean(axis=0)
    desvios = caracteristicas.std(axis=0)

    return np.concatenate([medias, desvios])

def caracteristicas_gerais(binaria, componentes):

    altura, largura = binaria.shape

    densidade = (np.count_nonzero(binaria) / binaria.size)

    quantidade_componentes = (len(componentes) / (altura * largura))

    areas = np.array([
        c["area"] for c in componentes
    ])

    if len(areas) == 0:
        return [0, 0, 0]

    variacao_area = (
        np.std(areas) / (np.mean(areas) + 1e-8)
    )

    return [
        densidade,
        quantidade_componentes,
        variacao_area
    ]