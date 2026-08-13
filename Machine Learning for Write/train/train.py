import pandas as pd
import index as idex
from sklearn.model_selection import GroupShuffleSplit

df = pd.read_csv('dataset.csv')

X = []

for caminho in df["imagem"]:
    features = idex.extrair_caracteristicas(caminho)
    X.append(features)

X = np.array(X)

Y = df[
    [
        "legibilidade",
        "alinhamento",
        "forma",
        "tamanho"
    ]
].values

grupos = df["crianca_id"].values

split = 
