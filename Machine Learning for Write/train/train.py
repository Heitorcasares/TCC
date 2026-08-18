import pandas as pd
import extrair_carac as idex
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

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

split = GroupShuffleSplit(
    n_splits=1, 
    test_size=0.20, 
    random_state=42
)

train_idx, test_idx = next(
    split.split(
        X, 
        Y, 
        grupos = grupos
    )
)

X_train = X[train_idx]
X_test = X[test_idx]

Y_train = Y[train_idx]
Y_test = Y[test_idx]

modelo_base = HistGradientBoostingRegressor(
    learning_rate=0.05,
    max_iter=300,
    max_leaf_nodes=31,
    l2_regularization=1.0,
    random_state=42
)

modelo = MultiOutputRegressor(modelo_base)

modelo.fit(X_train, Y_train)
