import cv2
import numpy as np
import pandas as pd

from sklearn.cluster import DBSCAN
from sklearn.linear_model import LinearRegression
from skimage.morphology import skeletonize


def normalizar(valor, referencia):
    """Limita valor/referencia ao intervalo de 0 a 1."""
    if referencia <= 0 or not np.isfinite(valor):
        return 0.0
    return float(np.clip(valor / referencia, 0, 1))


def dados_escrita(path, texto_referencia=None, numero_letras=None):
    """Analisa uma imagem de escrita.

    Para uma palavra conectada em um único componente, informe o texto que a
    criança copiou (texto_referencia="palavra") ou numero_letras=... . Nesse
    caso, calcula-se uma estimativa separada de largura média por letra. Ela
    NÃO é uma medição direta dos espaços entre letras.
    """
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Imagem inválida ou caminho incorreto: {path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    altura, largura = gray.shape
    if altura < 10 or largura < 10:
        raise ValueError("Imagem muito pequena para análise.")

    # 1. Binarização. Não remover linhas verticais automaticamente, pois
    # isso pode apagar hastes reais das letras.
    gray_suave = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binaria = cv2.threshold(
        gray_suave, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # 2. Componentes conectados
    total, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binaria, connectivity=8
    )

    componentes = []
    area_minima = max(8, int(altura * largura * 0.00005))

    for i in range(1, total):
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        area = int(stats[i, cv2.CC_STAT_AREA])

        # Preservar componentes grandes: uma palavra cursiva inteira pode
        # ser um único componente. O filtro superior descarta apenas áreas
        # quase tão grandes quanto a imagem inteira.
        if area < area_minima or area > altura * largura * 0.80:
            continue

        componentes.append({
            "x": x, "y": y, "w": w, "h": h, "area": area,
            "cx": x + w / 2,
            "cy": y + h / 2,
            "base": y + h
        })

    if not componentes:
        return {
            "Legibilidade Estimada": 0.0,
            "Tamanho da Letra": 0.0,
            "Se está na mesma linha": 0.0,
            "Dispersão entre componentes (%)": None,
            "Dispersão estimada por largura/letra (%)": None,
            "Número de letras de referência": None,
            "Grossura do Traço": 0.0,
            "Componentes Detectados": 0,
            "Método de alinhamento": "Sem componentes detectados",
            "Método da dispersão": "Sem escrita detectável"
        }

    # 3. Caixa total ocupada pela escrita
    x_min = min(c["x"] for c in componentes)
    y_min = min(c["y"] for c in componentes)
    x_max = max(c["x"] + c["w"] - 1 for c in componentes)
    y_max = max(c["y"] + c["h"] - 1 for c in componentes)

    largura_escrita = max(1, x_max - x_min + 1)
    altura_escrita = max(1, y_max - y_min + 1)
    alturas = np.array([c["h"] for c in componentes], dtype=float)

    # Uma caixa única contém a palavra inteira, não uma letra. Para esse
    # caso, usa-se uma estimativa de corpo de letra (60% da altura do bloco).
    # Esse fator é heurístico e deve ser calibrado com imagens anotadas.
    if len(componentes) == 1:
        altura_mediana = max(1.0, 0.60 * altura_escrita)
    else:
        altura_mediana = max(float(np.median(alturas)), 1.0)

    tamanho_letra = float(np.clip(
        altura_mediana / altura_escrita * 100, 0, 100
    ))

    # 4. Regularidade das alturas
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
        # Uma palavra conectada não oferece alturas individuais para comparar.
        regularidade_altura = 0.5

    # 5. Agrupar componentes por linha usando a base inferior
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

    # 6. Alinhamento e espaços horizontais observados
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
            # Só espaços positivos informam separação entre as caixas.
            if gap > 0:
                todos_espacamentos.append(float(gap))

    if alinhamentos:
        alinhamento = float(np.average(
            [item[0] for item in alinhamentos],
            weights=[item[1] for item in alinhamentos]
        ))
        metodo_alinhamento = "Linha de base dos componentes"
    else:
        alinhamento = 0.5
        metodo_alinhamento = "Estimativa neutra: poucos componentes para avaliar a linha"

    # 7. Dispersão real por espaços entre componentes (quando observável).
    if todos_espacamentos:
        distancia_media = float(np.mean(todos_espacamentos))
        dispersao_componentes = float(np.clip(
            distancia_media / max(2.0 * altura_mediana, 1.0) * 100.0,
            0.0, 100.0
        ))
        metodo_dispersao = "Espaços horizontais observados entre componentes"
    else:
        dispersao_componentes = None
        metodo_dispersao = "Sem espaços vazios mensuráveis entre componentes"

    # 8. IF solicitado: um único componente representa uma palavra conectada.
    # A contagem de letras vem do texto copiado ou de numero_letras.
    # Essa métrica é mantida em coluna separada para não confundi-la com gaps.
    dispersao_por_largura_letra = None
    letras_consideradas = None

    if len(componentes) == 1:
        if numero_letras is not None:
            try:
                letras_consideradas = int(numero_letras)
            except (TypeError, ValueError):
                letras_consideradas = None
        elif texto_referencia:
            letras_consideradas = sum(
                caractere.isalpha() for caractere in texto_referencia
            )

        if letras_consideradas is not None and letras_consideradas > 0:
            largura_media_por_letra = largura_escrita / letras_consideradas

            # Altura aproximada do corpo de letra. É uma referência heurística
            # porque a caixa do componente único inclui hastes, descendentes
            # e floreios. A calibração ideal usa as avaliações do TCC.
            altura_corpo_aproximada = max(1.0, 0.60 * altura_escrita)
            referencia_largura = 2.0 * altura_corpo_aproximada

            dispersao_por_largura_letra = float(np.clip(
                largura_media_por_letra / referencia_largura * 100.0,
                0.0, 100.0
            ))

            dispersao_componentes = dispersao_por_largura_letra

    # 9. Grossura do traço
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

    # 10. Legibilidade. A estimativa por largura/letra não entra aqui,
    # porque não é equivalente a espaçamento real entre letras.
    if dispersao_componentes is not None:
        legibilidade_estimada = (
            0.50 * alinhamento
            + 0.30 * regularidade_altura
            + 0.20 * (1.0 - dispersao_componentes / 100.0)
        )
        metodo_legibilidade = "Inclui espaçamento observado"
    else:
        legibilidade_estimada = (
            0.50 * alinhamento + 0.30 * regularidade_altura
        ) / 0.80
        metodo_legibilidade = "Pesos redistribuídos: espaçamento real não mensurável"

    return {
        "Legibilidade Estimada": round(legibilidade_estimada * 100, 2),
        "Tamanho da Letra": round(tamanho_letra, 2),
        "Se está na mesma linha": round(alinhamento * 100, 2),
        "Dispersão entre componentes (%)": (
            None if dispersao_componentes is None
            else round(dispersao_componentes, 2)
        ),
        "Grossura do Traço": round(grossura * 100, 2)
    }


if __name__ == "__main__":
    caminho = "models/e05.jpeg"

    # IMPORTANTE: substitua pelo texto exato que a criança copiou.
    texto_referencia = "Renato"

    resultado = dados_escrita(
        caminho,
        texto_referencia=texto_referencia
    )

    tabela_dados = pd.DataFrame([resultado])
    print(tabela_dados.to_string(index=False))
