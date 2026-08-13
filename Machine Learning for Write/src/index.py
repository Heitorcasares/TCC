import functions as f
import cv2
import numpy as np

def extrair_caracteristicas(caminho):

    gray, binaria = f.upload_imagem(caminho)

    componentes = f.encontrar_objetos(binaria)

    if len(componentes) < 5:
        raise ValueError("Pouca escrita detectada na imagem!")

    linhas = f.detectar_linhas(componentes)

    tamanho = f.caracteristicas_tamanho(componentes, binaria.shape)

    alinhamento = f.caracteristicas_alinhamento(linhas)

    forma = f.caracteristicas_hog(binaria, componentes)

    gerais = f.caracteristicas_gerais(binaria, componentes)

    return np.concatenate([
        tamanho,
        alinhamento,
        forma,
        gerais
    ])
