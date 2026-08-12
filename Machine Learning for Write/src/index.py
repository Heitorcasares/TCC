import cv2 
import numpy as np 


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