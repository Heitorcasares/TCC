import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

opcsv = pd.read_csv("C:/Users/heito/OneDrive/Área de Trabalho/TCC/Machine Learning for Hands/dataset.csv")

X = opcsv.drop(columns=["label", "image_path"])
Y = opcsv["label"]

X_train, X_test, Y_train, Y_test = train_test_split(
    X,
    Y,
    test_size = 0.3,
    random_state = 42,
    stratify = Y
)

model = RandomForestClassifier(
    n_estimators = 300,
    random_state = 42
)

model.fit(X_train, Y_train)
predict = model.predict(X_test)

print(classification_report(Y_test, predict))

with open("modelo_treinado.pkl", "wb") as f:
    pickle.dump(model, f)
    print("modelo salvo como modelo_treinado.pkl")