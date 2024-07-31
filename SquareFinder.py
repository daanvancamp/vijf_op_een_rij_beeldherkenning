import cv2
import numpy as np

class SquareFinder:
    # Constante parameters voor vierkantdetectie
    canny_upper_thresh = 30
    thresh_it = 30

    @staticmethod
    def find_squares(image):
        """
        Detecteert vierkanten in een afbeelding.
        Parameters:
            image (numpy.ndarray): De invoerafbeelding waarin vierkanten moeten worden gedetecteerd.
        Returns:
            list: Een lijst van vierkanten (elk vierkant wordt gerepresenteerd als een lijst van vier punten).
        """
        squares = []
        # Maak een kopie van de afbeelding om mee te werken
        img = image.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Voor elke kleurcomponent in de afbeelding
        for c in range(3):
            # Splits de kleurkanalen
            ch = img[:, :, c]
            
            # Probeer meerdere drempelwaarden
            for l in range(SquareFinder.thresh_it):
                # Gebruik Canny bij de eerste iteratie
                if l == 0:
                    edges = cv2.Canny(ch, 0, SquareFinder.canny_upper_thresh)
                    edges = cv2.dilate(edges, None)
                else:
                    _, edges = cv2.threshold(ch, (l + 1) * 255 / SquareFinder.thresh_it, 255, cv2.THRESH_BINARY)
                
                # Vind contouren
                contours, _ = cv2.findContours(edges.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    # Benader het contour met een nauwkeurigheid afhankelijk van de omtrek
                    epsilon = 0.02 * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, epsilon, True)
                    
                    # Controleer of de benaderde contour een vierkant is
                    if len(approx) == 4 and cv2.isContourConvex(approx):
                        # Controleer of het vierkant een voldoende grote oppervlakte heeft
                        if cv2.contourArea(approx) > 1000:
                            max_cosine = 0
                            for i in range(2, 5):
                                cosine = abs(SquareFinder.angle_cos(approx[i%4][0], approx[i-2][0], approx[i-1][0]))
                                max_cosine = max(max_cosine, cosine)
                            
                            # Controleer of de maximale cosinuswaarde minder dan 0.3 is (alle hoeken dicht bij 90 graden)
                            if max_cosine < 0.3:
                                squares.append(approx)
        
        return squares

    @staticmethod
    def angle_cos(p0, p1, p2):
        """
        Berekent de cosinus van de hoek tussen twee vectoren met gemeenschappelijk startpunt.
        Parameters:
            p0, p1, p2: Punten die de vectoren definiëren.
        Returns:
            float: De cosinus van de hoek tussen de vectoren.
        """
        d1, d2 = p1 - p0, p2 - p0
        return abs(np.dot(d1, d2) / (np.linalg.norm(d1) * np.linalg.norm(d2)))

# Voorbeeld van gebruik
if __name__ == "__main__":
    # Lees de afbeelding
    image = cv2.imread('./testopstellingen/bord2.jpg')
    
    if image is None:
        print("Fout bij het laden van de afbeelding. Controleer of het bestandspad correct is.")
    else:
        # Zoek vierkanten
        squares = SquareFinder.find_squares(image)
        
        print("Vierkanten gedetecteerd:", len(squares))
        # Teken de gevonden vierkanten op de afbeelding
        for square in squares:
            cv2.drawContours(image, [square], 0, (0, 255, 0), 2)
        
        # Toon de afbeelding
        image=cv2.resize(image,(600,800))
        cv2.imshow('Gedetecteerde Vierkanten', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()



