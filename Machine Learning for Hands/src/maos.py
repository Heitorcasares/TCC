import cv2
import mediapipe as mp
import csv
import os







LABEL = "joinha"
OUTPUT_DIR = f"data/{LABEL}"
CSV_FILE = "dataset.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)


header = ["image_path", "label"]

for i in range(21):
    header += ([f"x{i}"], [f"y{i}"], [f"z{i}"])

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

video = cv2.VideoCapture(0)

hand = mp.solutions.hands
Hand = hand.Hands(max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

print("SISTEMA DE COLETA INICIADO!")
print("Faça o gesto na câmera e aperte:")
print("- 'p' para registrar sinal de PAZ")
print("- 'j' para registrar sinal de JOINHA")
print("- 'Esc' para SAIR")

while True:
    check, img = video.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = Hand.process(imgRGB)
    handsPoints = results.multi_hand_landmarks
    h,w,_ = img.shape
    pontos = []
    if handsPoints:
        for points in handsPoints:
            mpDraw.draw_landmarks(img, points, hand.HAND_CONNECTIONS)
            for id, cord in enumerate(points.landmark):
                cx, cy, cz = int(cord.x*w), int(cord.y*h), int(cord.z*h)
                #cv2.putText(img, str(id), (cx, cy+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
                pontos.append((cx, cy, cz))



   

        dedos = [8, 12, 16, 20]
        contador = 0

        if points:
            if pontos[4][0] < pontos[2][0]:
                contador +=1
            for x in dedos:
                if pontos[x][1] < pontos[ x-2 ][1]:
                    contador +=1

        
        #if contador == 0:
            #video.release()
            #cv2.destroyAllWindows()
        
        
        #print(contador)
        #print(pontos)

        





    cv2.imshow("IMAGEM", img)
    cv2.waitKey(1)

