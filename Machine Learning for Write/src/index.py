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


def _detectar_ligaduras_e_espacos(binaria, componentes, altura_mediana):
    if not componentes:
        return []

    x_min = min(c["x"] for c in componentes)
    y_min = min(c["y"] for c in componentes)
    x_max = max(c["x"] + c["w"] - 1 for c in componentes)
    y_max = max(c["y"] + c["h"] - 1 for c in componentes)

    recorte = binaria[y_min:y_max+1, x_min:x_max+1]
    h_rec, w_rec = recorte.shape
    if w_rec < 10 or h_rec < 10:
        return []

    esq = skeletonize(recorte > 0)
    dist = cv2.distanceTransform(
        (recorte > 0).astype(np.uint8) * 255,
        cv2.DIST_L2,
        cv2.DIST_MASK_PRECISE
    )
    grossura_px = float(np.median(2 * dist[esq])) if np.any(esq) else 3.0
    limiar_altura_traco = max(grossura_px * 2.2, 8.0)

    classificacao = np.zeros(w_rec, dtype=int)
    for x in range(w_rec):
        col = recorte[:, x]
        pts = np.where(col > 0)[0]
        if len(pts) == 0:
            classificacao[x] = 0
        else:
            diffs = np.diff(pts)
            num_segmentos = 1 + np.sum(diffs > 2)
            tam_vertical = len(pts)
            if num_segmentos == 1 and tam_vertical <= limiar_altura_traco:
                classificacao[x] = 1
            else:
                classificacao[x] = 2

    cols_corpo = np.where(classificacao == 2)[0]
    if len(cols_corpo) < 2:
        return []

    inicio = cols_corpo[0]
    fim = cols_corpo[-1]

    espacamentos = []
    em_espaco = False
    x_ini = 0

    for i in range(inicio, fim + 1):
        c = classificacao[i]
        if c in (0, 1):
            if not em_espaco:
                em_espaco = True
                x_ini = i
        else:
            if em_espaco:
                comp = i - x_ini
                if comp >= 4:
                    espacamentos.append(float(comp))
                em_espaco = False

    if em_espaco:
        comp = (fim + 1) - x_ini
        if comp >= 4:
            espacamentos.append(float(comp))

    return espacamentos


def _filtrar_artefatos_borda(componentes, largura_img, altura_img):
    limiar_borda = max(5, int(largura_img * 0.005))
    limiar_largura = largura_img * 0.15
    filtrados = []

    for c in componentes:
        x, y, w, h = c["x"], c["y"], c["w"], c["h"]

        if x < limiar_borda and w < limiar_largura:
            continue
        if (x + w) > (largura_img - limiar_borda) and w < limiar_largura:
            continue
        if y < limiar_borda and (y + h) > (altura_img - limiar_borda):
            if w < limiar_largura:
                continue
        filtrados.append(c)

    return filtrados


def _filtrar_ruido_adaptativo(componentes):
    if len(componentes) <= 1:
        return componentes

    areas = np.array([c["area"] for c in componentes], dtype=float)
    area_ref = float(np.max(areas))
    limiar_area = max(10, area_ref * 0.01)

    alturas = np.array([c["h"] for c in componentes], dtype=float)
    altura_ref = float(np.max(alturas))
    limiar_altura = max(3, altura_ref * 0.10)

    return [
        c for c in componentes
        if c["area"] >= limiar_area and c["h"] >= limiar_altura
    ]


def dados_escrita(path, texto_referencia=None, numero_letras=None):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Imagem inválida ou caminho incorreto: {path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    altura, largura = gray.shape
    if altura < 10 or largura < 10:
        raise ValueError("Imagem muito pequena para análise.")

    gray_suave = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binaria = cv2.threshold(
        gray_suave, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    kernel_closing = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel_closing)

    total, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binaria, connectivity=8
    )

    area_minima_bruta = max(8, int(altura * largura * 0.00005))
    area_maxima = altura * largura * 0.80

    componentes_brutos = []
    for i in range(1, total):
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        area = int(stats[i, cv2.CC_STAT_AREA])

        if area < area_minima_bruta or area > area_maxima:
            continue

        componentes_brutos.append({
            "x": x, "y": y, "w": w, "h": h, "area": area,
            "cx": x + w / 2,
            "cy": y + h / 2,
            "base": y + h
        })

    componentes = _filtrar_artefatos_borda(componentes_brutos, largura, altura)
    componentes = _filtrar_ruido_adaptativo(componentes)

    if not componentes:
        return {
            "Legibilidade Estimada": 0.0,
            "Tamanho da Letra": 0.0,
            "Se está na mesma linha": 0.0,
            "Dispersão entre componentes (%)": 0.0,
            "Grossura do Traço": 0.0
        }

    x_min = min(c["x"] for c in componentes)
    y_min = min(c["y"] for c in componentes)
    x_max = max(c["x"] + c["w"] - 1 for c in componentes)
    y_max = max(c["y"] + c["h"] - 1 for c in componentes)

    largura_escrita = max(1, x_max - x_min + 1)
    altura_escrita = max(1, y_max - y_min + 1)
    alturas = np.array([c["h"] for c in componentes], dtype=float)

    if len(componentes) == 1:
        altura_mediana = max(1.0, 0.60 * altura_escrita)
    else:
        altura_mediana = max(float(np.median(alturas)), 1.0)

    tamanho_letra = float(np.clip(
        altura_mediana / altura_escrita * 100, 0, 100
    ))

    if len(alturas) >= 3:
        mediana_h = float(np.median(alturas))
        alturas_corpo = alturas[
            (alturas >= 0.50 * mediana_h) &
            (alturas <= 1.60 * mediana_h)
        ]
        if len(alturas_corpo) >= 2:
            variacao_altura = (
                np.std(alturas_corpo) / (np.mean(alturas_corpo) + 1e-8)
            )
            regularidade_altura = float(np.exp(-variacao_altura))
        else:
            regularidade_altura = 0.5
    elif len(alturas) == 2:
        variacao_altura = (
            abs(alturas[0] - alturas[1]) / (np.mean(alturas) + 1e-8)
        )
        regularidade_altura = float(np.exp(-variacao_altura))
    else:
        regularidade_altura = 0.5

    linhas = []
    if len(componentes) >= 2:
        bases = np.array([[c["base"]] for c in componentes], dtype=float)
        eps_linha = max(0.45 * altura_mediana, 8.0)
        grupos = DBSCAN(eps=eps_linha, min_samples=2).fit_predict(bases)

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

    alinhamentos = []
    todos_espacamentos = []

    for linha in linhas:
        X = np.array([[c["cx"]] for c in linha], dtype=float)
        Y = np.array([c["base"] for c in linha], dtype=float)

        if len(linha) >= 3 and np.ptp(X) > 0:
            modelo = LinearRegression().fit(X, Y)
            residuos = Y - modelo.predict(X)
            mad = float(np.median(np.abs(residuos - np.median(residuos))))
            erro_relativo = mad / altura_mediana
            score_linha = float(np.exp(-np.log(2) * erro_relativo / 0.12))
            alinhamentos.append((score_linha, len(linha)))
        elif len(linha) == 2:
            erro_relativo = float(np.std(Y) / altura_mediana)
            score_linha = float(np.exp(-np.log(2) * erro_relativo / 0.12))
            alinhamentos.append((score_linha, len(linha)))

        for atual, proxima in zip(linha[:-1], linha[1:]):
            gap = proxima["x"] - (atual["x"] + atual["w"])
            if gap > 0:
                todos_espacamentos.append(float(gap))

    if len(componentes) == 1 and not alinhamentos:
        c = componentes[0]
        roi = binaria[c["y"]:c["y"]+c["h"], c["x"]:c["x"]+c["w"]]
        roi_bool = roi > 0
        try:
            esq = skeletonize(roi_bool)
        except Exception:
            esq = roi_bool

        if np.any(esq):
            colunas_y = []
            colunas_x = []
            for col_idx in range(esq.shape[1]):
                ys = np.where(esq[:, col_idx])[0]
                if len(ys) > 0:
                    colunas_y.append(float(np.max(ys)))
                    colunas_x.append(float(col_idx))

            if len(colunas_x) >= 10:
                janela = max(5, len(colunas_y) // 20)
                y_suave = np.convolve(colunas_y, np.ones(janela)/janela, mode='valid')
                x_suave = np.arange(len(y_suave)).reshape(-1, 1)

                reg = LinearRegression().fit(x_suave, y_suave)
                res = y_suave - reg.predict(x_suave)
                mad_intra = float(np.median(np.abs(res - np.median(res))))
                h_ref = max(c["h"] * 0.6, 1.0)
                erro_intra = mad_intra / h_ref
                score_intra = float(np.exp(-np.log(2) * erro_intra / 0.12))
                alinhamento = float(np.clip(score_intra, 0, 1))
            else:
                alinhamento = 0.5
        else:
            alinhamento = 0.5
    elif alinhamentos:
        alinhamento = float(np.average(
            [item[0] for item in alinhamentos],
            weights=[item[1] for item in alinhamentos]
        ))
    else:
        alinhamento = 0.5

    espacos_ligaduras = _detectar_ligaduras_e_espacos(binaria, componentes, altura_mediana)

    if todos_espacamentos and len(todos_espacamentos) >= 2:
        distancia_media = float(np.mean(todos_espacamentos))
        dispersao_componentes = float(np.clip(
            distancia_media / max(2.0 * altura_mediana, 1.0) * 100.0,
            0.0, 100.0
        ))
    elif espacos_ligaduras:
        distancia_media = float(np.mean(espacos_ligaduras))
        dispersao_componentes = float(np.clip(
            distancia_media / max(2.0 * altura_mediana, 1.0) * 100.0,
            0.0, 100.0
        ))
    elif todos_espacamentos:
        distancia_media = float(np.mean(todos_espacamentos))
        dispersao_componentes = float(np.clip(
            distancia_media / max(2.0 * altura_mediana, 1.0) * 100.0,
            0.0, 100.0
        ))
    else:
        letras_consideradas = None
        if numero_letras is not None:
            try:
                letras_consideradas = int(numero_letras)
            except (TypeError, ValueError):
                letras_consideradas = None
        elif texto_referencia:
            letras_consideradas = sum(
                caractere.isalpha() for caractere in texto_referencia
            )

        if letras_consideradas and letras_consideradas > 1:
            largura_media = largura_escrita / letras_consideradas
            altura_corpo = max(1.0, 0.60 * altura_escrita)
            dispersao_componentes = float(np.clip(
                largura_media / (2.0 * altura_corpo) * 100.0,
                0.0, 100.0
            ))
        else:
            dispersao_componentes = 0.0

    mascara = binaria > 0
    esqueleto = skeletonize(mascara)
    mascara_u8 = mascara.astype(np.uint8) * 255

    if np.any(esqueleto):
        distancias = cv2.distanceTransform(
            mascara_u8, cv2.DIST_L2, cv2.DIST_MASK_PRECISE
        )
        grossura_px = float(np.median(2 * distancias[esqueleto]))
        grossura_relativa = grossura_px / max(altura_mediana, 1.0)
        grossura = normalizar(grossura_relativa, referencia=0.20)
    else:
        grossura = 0.0

    legibilidade_estimada = (
        0.50 * alinhamento
        + 0.30 * regularidade_altura
        + 0.20 * (1.0 - dispersao_componentes / 100.0)
    )

    return {
        "Legibilidade Estimada": round(legibilidade_estimada * 100, 2),
        "Tamanho da Letra": round(tamanho_letra, 2),
        "Se está na mesma linha": round(alinhamento * 100, 2),
        "Dispersão entre componentes (%)": round(dispersao_componentes, 2),
        "Grossura do Traço": round(grossura * 100, 2)
    }


if __name__ == "__main__":
    caminho = "models/e01.jpeg"
    texto_referencia = "Renato"

    resultado = dados_escrita(
        caminho,
        texto_referencia=texto_referencia
    )

    tabela_dados = pd.DataFrame([resultado])
    print(tabela_dados.to_string(index=False))
