
import cv2
import numpy as np
import pandas as pd

from sklearn.cluster import DBSCAN
from sklearn.linear_model import LinearRegression
from skimage.morphology import skeletonize


def normalizar(valor, referencia):
    if referencia <= 0 or not np.isfinite(valor):
        return 0.0
    return float(np.clip(valor / referencia, 0, 1))


def dados_escrita(path):
    img = cv2.imread(path)

    if img is None:
        raise ValueError(f"Imagem inválida ou caminho incorreto: {path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    altura, largura = gray.shape

    if altura < 10 or largura < 10:
        raise ValueError("Imagem muito pequena para análise.")

    # 1. Binarização
    gray_suave = cv2.GaussianBlur(gray, (5, 5), 0)

    _, binaria = cv2.threshold(
        gray_suave, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # 2. Remover linhas longas do papel, quando detectáveis.
    # Isso ajuda em folhas pautadas, mas não garante remover todas.
    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (max(20, largura // 20), 1)
    )
    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (1, max(20, altura // 20))
    )

    linhas_h = cv2.morphologyEx(
        binaria, cv2.MORPH_OPEN, horizontal_kernel
    )
    linhas_v = cv2.morphologyEx(
        binaria, cv2.MORPH_OPEN, vertical_kernel
    )

    linhas_papel = cv2.bitwise_or(linhas_h, linhas_v)
    binaria_limpa = cv2.subtract(binaria, linhas_papel)

    # Se a remoção apagar quase toda a escrita, usar imagem original.
    if np.count_nonzero(binaria_limpa) < 0.15 * np.count_nonzero(binaria):
        binaria_limpa = binaria.copy()

    # 3. Componentes conectados
    total, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binaria_limpa, connectivity=8
    )

    componentes = []

    for i in range(1, total):
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        area = int(stats[i, cv2.CC_STAT_AREA])

        if area < 8:
            continue

        if area > altura * largura * 0.20:
            continue

        componentes.append({
            "x": x, "y": y, "w": w, "h": h, "area": area,
            "cx": x + w / 2,
            "cy": y + h / 2
        })

    # 4. Criar máscara global da escrita.
    # A análise global continua funcionando mesmo com um único
    # componente conectado.
    mascara = binaria_limpa > 0
    ys, xs = np.where(mascara)

    if len(xs) == 0:
        return {
            "Legibilidade Estimada": 0.0,
            "Tamanho da Letra": 0.0,
            "Se está na mesma linha": 0.0,
            "Dispersão entre componentes": 0.0,
            "Grossura do Traço": 0.0,
            "Componentes Detectados": 0,
            "Método de Análise": "Sem escrita detectável"
        }

    # Medida global de altura da escrita
    altura_escrita = float(ys.max() - ys.min() + 1)
    largura_escrita = float(xs.max() - xs.min() + 1)

    # Usar componentes disponíveis; se houver poucos, estimar
    # a escala a partir da altura global da escrita.
    if componentes:
        alturas = np.array([c["h"] for c in componentes], dtype=float)
        altura_mediana = float(np.median(alturas))
    else:
        alturas = np.array([], dtype=float)
        altura_mediana = altura_escrita

    if altura_mediana <= 0:
        altura_mediana = 1.0

    tamanho_letra = normalizar(
        altura_mediana / altura,
        referencia=0.10
    )

    # 5. Regularidade da altura.
    # Com poucos componentes, usar um valor neutro e indicar
    # a limitação, em vez de interromper toda a análise.
    if len(alturas) >= 2:
        variacao_altura = (
            np.std(alturas) / (np.mean(alturas) + 1e-8)
        )
        regularidade_altura = float(np.exp(-variacao_altura))
    else:
        regularidade_altura = 0.5

    # 6. Agrupar componentes por posição vertical
    linhas = []

    if len(componentes) >= 3:
        posicoes_y = np.array(
            [[c["cy"]] for c in componentes], dtype=float
        )

        grupos = DBSCAN(
            eps=max(altura_mediana * 0.8, 1.0),
            min_samples=2
        ).fit_predict(posicoes_y)

        for grupo in sorted(set(grupos)):
            if grupo == -1:
                continue

            linha = [
                componentes[i]
                for i in range(len(componentes))
                if grupos[i] == grupo
            ]

            if len(linha) >= 2:
                linha.sort(key=lambda c: c["x"])
                linhas.append(linha)

    # 7. Alinhamento: usar linhas identificadas quando possível.
    alinhamentos = []
    todos_espacamentos = []

    for linha in linhas:
        X = np.array([[c["cx"]] for c in linha], dtype=float)
        Y = np.array([c["cy"] for c in linha], dtype=float)

        if len(linha) >= 2 and np.ptp(X) > 0:
            regressao = LinearRegression().fit(X, Y)
            residuos = Y - regressao.predict(X)

            erro_relativo = (
                np.sqrt(np.mean(residuos ** 2)) / altura_mediana
            )

            score = np.exp(-np.log(2) * erro_relativo / 0.15)
            alinhamentos.append(float(score))

        for atual, proxima in zip(linha[:-1], linha[1:]):
            distancia = proxima["x"] - (atual["x"] + atual["w"])
            todos_espacamentos.append(max(0.0, float(distancia)))

    if alinhamentos:
        alinhamento = float(np.mean(alinhamentos))
        metodo = "Componentes e linhas"
    else:
        # Alternativa: medir quanto a tinta varia verticalmente
        # ao longo da área ocupada pela escrita.
        # É uma estimativa geométrica, não uma avaliação clínica.
        projecao_y = np.sum(mascara, axis=1).astype(float)
        linhas_ativas = np.where(projecao_y > 0)[0]

        if len(linhas_ativas) >= 2:
            centros_y = ys.astype(float)
            dispersao_vertical = np.std(centros_y) / max(altura_mediana, 1)
            alinhamento = float(np.exp(-dispersao_vertical * 0.15))
        else:
            alinhamento = 0.5

        metodo = "Análise global de fallback"

    # 8. Dispersão horizontal entre componentes: 0 a 100%.
    # Se não houver pares de componentes, usar a largura total
    # da escrita em relação à altura como estimativa alternativa.
    if todos_espacamentos:
        distancia_media = float(np.mean(todos_espacamentos))
        distancia_referencia = 2.0 * altura_mediana

        dispersao_espacamento = float(np.clip(
            distancia_media / max(distancia_referencia, 1.0) * 100,
            0, 100
        ))
    else:
        razao_largura_altura = largura_escrita / max(altura_escrita, 1.0)

        # Referência ajustável; 8 alturas de largura = 100%.
        dispersao_espacamento = float(np.clip(
            razao_largura_altura / 8.0 * 100,
            0, 100
        ))

    # 9. Grossura do traço usando distância dentro da máscara.
    mascara_u8 = (mascara.astype(np.uint8) * 255)
    esqueleto = skeletonize(mascara)

    if np.any(esqueleto):
        distancias = cv2.distanceTransform(
            mascara_u8, cv2.DIST_L2, cv2.DIST_MASK_PRECISE
        )
        grossura_px = float(np.median(2 * distancias[esqueleto]))
        grossura_relativa = grossura_px / max(altura_mediana, 1.0)
        grossura = normalizar(grossura_relativa, referencia=0.20)
    else:
        grossura = 0.0

    # 10. Legibilidade estimada.
    # Os pesos e a medida global são provisórios e precisam de validação.
    legibilidade_estimada = (
        0.50 * alinhamento
        + 0.30 * regularidade_altura
        + 0.20 * (1.0 - dispersao_espacamento / 100.0)
    )

    return {
        "Legibilidade Estimada": round(legibilidade_estimada * 100, 2),
        "Tamanho da Letra": round(tamanho_letra * 100, 2),
        "Se está na mesma linha": round(alinhamento * 100, 2),
        "Dispersão entre componentes": round(dispersao_espacamento, 2),
        "Grossura do Traço": round(grossura * 100, 2)
    }


print(pd.DataFrame([dados_escrita("models/e02.jpeg")]))

tabela_dados = pd.DataFrame([dados_escrita("models/e02.jpeg")])
