import cv2
import numpy as np


def dados_escrita(path):

    # Transformar imagem em cinza e depois converter para fundo preto e letra branca
    img = cv2.imread(path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    binaria, _ = cv2.threshold(
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

    largura_bi, altura_bi = binaria.sha


