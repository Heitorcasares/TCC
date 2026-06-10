import cv2
import mediapipe as mp
import csv
import os







LABEL = "Joinha"
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

frame_count = 0

print("Pressione S para salvar")
print("Pressione Q para sair")

hand = mp.solutions.hands
Hand = hand.Hands(max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

while True:
    check, img = video.read()
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = Hand.process(imgRGB)
    handsPoints = results.multi_hand_landmarks
    w, h, _ = img.shape
    pontos = []

    


    if handsPoints:
        for points in handsPoints:
            mpDraw.draw_landmarks(img, points, hand.HAND_CONNECTIONS)
            for id, cord in enumerate(points.landmark):
                cx = int(cord.x*w) 
                cy = int(cord.y*h)
                cz = float(cord.z)
                #cv2.putText(img, str(id), (cx, cy+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
                pontos.extend([cx, cy, cz])

        
   


        
        #if contador == 0:
            #video.release()
            #cv2.destroyAllWindows()
        
        
        #print(contador)
        #print(pontos)

        cv2.putText(img, f"Rotulo: {LABEL}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(img, "S = salvar | Q = sair", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        





    cv2.imshow("IMAGEM", img)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        if points is not None:
            image_name = f"frame_{frame_count:04d}.jpg"
            image_path = os.path.join(OUTPUT_DIR, image_name)

            cv2.imwrite(image_path, img)

            row = [image_path, LABEL] + pontos

            with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            print(f"Salvo: {image_path}")
            frame_count += 1
        else:
            print("Nenhuma mão detectada. Não salvou.")
    elif key == ord("q"):
        break

video.release()
cv2.destroyAllWindows()

