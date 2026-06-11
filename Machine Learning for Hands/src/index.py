import cv2
import mediapipe as mp
import numpy as np
import pickle

video = cv2.VideoCapture(0)




hand = mp.solutions.hands
Hand = hand.Hands(max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

with open("modelo_treinado.pkl", "rb") as f:
    model = pickle.load(f)

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

        input_data = np.array(pontos).reshape(1, -1)
        label_predicted = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]
        confidance = max(probabilities) * 100

        text = f"{label_predicted}: {confidance:.2f}%"

        cv2.putText(
            img,
            text,
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        for label, prob in zip(model.classes_, probabilities):
            print(f"{label}: {prob * 100:.2f}%")
        
        





    cv2.imshow("IMAGEM", img)
    key = cv2.waitKey(1) & 0xFF

    
    if key == ord("q"):
        break

video.release()
cv2.destroyAllWindows()

