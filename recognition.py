
import datetime
import glob
import json
from time import sleep
import cv2
import numpy as np

path_board=r'./testopstellingen/21.jpg'
BOARD_SIZE = 15
corners_to_be_found = BOARD_SIZE - 1 

def draw_point_and_show(image, point, window_name="Corners",wait_key=1):
    color = (0, 0, 255)
    radius = 10
    thickness = -1
    point = (int(point[0]), int(point[1]))
    cv2.circle(image, point, radius, color, thickness)
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, image)
    cv2.waitKey(wait_key)

def calculate_euclidean_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def determine_average_distances(corners):
    corners = corners.reshape((corners_to_be_found, corners_to_be_found, 2))
    
    horizontal_distances = []
    vertical_distances = []

    for i in range(corners_to_be_found):
        for j in range(corners_to_be_found):
            p1 = corners[i, j]

            # add horizontal distances
            if j + 1 < corners_to_be_found:
                p2 = corners[i, j + 1]
                horizontal_distances.append(calculate_euclidean_distance(p1, p2))

            # add vertical distances
            if i + 1 < corners_to_be_found:
                p3 = corners[i + 1, j]
                vertical_distances.append(calculate_euclidean_distance(p1, p3))

    # calculate average distances
    avg_horizontal_distance = np.mean(horizontal_distances)
    avg_vertical_distance = np.mean(vertical_distances)

    return avg_horizontal_distance, avg_vertical_distance

def extrapolate_other_corners(corners, avg_distances):
    global avg_horizontal, avg_vertical
    avg_horizontal, avg_vertical = avg_distances

    complete_corners = np.zeros((BOARD_SIZE + 1, BOARD_SIZE + 1, 2), dtype=np.float32)
    complete_corners[1:-1, 1:-1] = corners.reshape((corners_to_be_found, corners_to_be_found, 2))

    for i in range(1, BOARD_SIZE):
        complete_corners[i, -1] = [complete_corners[i, -2, 0] + avg_horizontal, complete_corners[i, -2, 1]]

    for j in range(1, BOARD_SIZE):
        complete_corners[-1, j] = [complete_corners[-2, j, 0], complete_corners[-2, j, 1] + avg_vertical]

    for i in range(1, BOARD_SIZE):
        complete_corners[i, 0] = [complete_corners[i, 1, 0] - avg_horizontal, complete_corners[i, 1, 1]]

    for j in range(1, BOARD_SIZE):
        complete_corners[0, j] = [complete_corners[1, j, 0], complete_corners[1, j, 1] - avg_vertical]

    complete_corners[0, 0] = [complete_corners[1, 1, 0] - avg_horizontal, complete_corners[1, 1, 1] - avg_vertical]
    complete_corners[0, -1] = [complete_corners[1, -2, 0] + avg_horizontal, complete_corners[1, -2, 1] - avg_vertical]
    complete_corners[-1, 0] = [complete_corners[-2, 1, 0] - avg_horizontal, complete_corners[-2, 1, 1] + avg_vertical]
    complete_corners[-1, -1] = [complete_corners[-2, -2, 0] + avg_horizontal, complete_corners[-2, -2, 1] + avg_vertical]

    return complete_corners

def calculate_cell_centers(corners):
    centers = []
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            p1 = corners[i, j]
            p2 = corners[i, j + 1]
            p3 = corners[i + 1, j]
            p4 = corners[i + 1, j + 1]
            center_x = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
            center_y = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
            centers.append((center_x, center_y))
    return np.array(centers)


def detect_pieces(cell_centers, path_board):
    img = cv2.imread(path_board)
    
    # Convert image to HSV (Hue, Saturation, Value)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])
    
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = mask_red1 + mask_red2
    
    blue_ellipses = detect_and_draw_ellipses(img, mask_blue, color=(255, 0, 0), shape="blue ellipses")
    red_ellipses = detect_and_draw_ellipses(img, mask_red, color=(0, 0, 255), shape="red ellipses")

    list_blue_shapes=match_shapes_to_centers(blue_ellipses, cell_centers, img,"blue")
    list_red_shapes=match_shapes_to_centers(red_ellipses, cell_centers, img,"red")

    all_shapes = blue_ellipses + red_ellipses

    list_shapes = list(set(list_blue_shapes + list_red_shapes))

    data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "pieces": list_shapes
        }
        
    with open('detected_pieces.json', 'w') as json_file:
        json.dump(data, json_file, indent=4, default=int) 

    cv2.namedWindow("Detected Pieces", cv2.WINDOW_NORMAL)
    cv2.imshow("Detected Pieces", img)
    if not "_processed2" in path_board and not "."+path_board.rsplit(".",2)[1]+"_processed2.jpg" in glob.glob('./test_images/images_with_pieces/*.jpg',recursive=True):
        cv2.imwrite(path_board[:-4] + "_processed2.jpg"  , img)

    cv2.waitKey(4000)
    cv2.destroyAllWindows()

def detect_and_draw_ellipses(img, mask, color, shape="ellipses", min_area=50):
    global avg_horizontal, avg_vertical
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    min_area = (avg_horizontal * avg_vertical)/60
    max_area = (avg_horizontal * avg_vertical)+10
    detected_ellipses = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if max_area>=area >= min_area and len(cnt) >= 5:  
            ellipse = cv2.fitEllipse(cnt)
            cv2.ellipse(img, ellipse, color, 2)
            center = (int(ellipse[0][0]), int(ellipse[0][1]))  
            detected_ellipses.append(center)  
    print(f"Detected {len(detected_ellipses)} {shape}.")
    
    return detected_ellipses 

def get_coordinates(index):
    x = index[0]//BOARD_SIZE
    y = index[0]%BOARD_SIZE
    return (x,y)

def match_shapes_to_centers(shapes, cell_centers, img,color):
    """
    Voor elk gedetecteerd object (cirkel of ellips), bepaal welk celcentrum het dichtstbijzijnde is
    en teken de lijn tussen hen op de afbeelding.
    """
    list_shapes = []
    for shape in shapes:
        closest_center = None
        min_distance = float("inf")
        
        for center in cell_centers:
            # Bereken de Euclidische afstand
            distance = np.linalg.norm(np.array(shape) - np.array(center))
            if distance < min_distance:
                min_distance = distance
                closest_center = center
        
        max_distance=(avg_horizontal+avg_vertical)/2

        if min_distance>max_distance:
            continue

        if closest_center.any():
            result=np.where(cell_centers == closest_center)
            index = (result[0][0], result[1][0])
            coordinates= get_coordinates(index)

            list_shapes.append((color,coordinates))


            shape_point = tuple(map(int, shape)) 
            closest_center_point = tuple(map(int, closest_center)) 
            

            cv2.line(img, shape_point, closest_center_point, (0, 255, 0), 2)
            cv2.circle(img, shape_point, 5, (0, 255, 255), -1) 
            cv2.circle(img, closest_center_point, 5, (255, 255, 0), -1)  

    return list_shapes

def crop_to_square(frame):
    height, width = frame.shape[:2]
    smallest_side = min(height, width)
    start_x = (width - smallest_side) // 2 
    start_y = (height - smallest_side) // 2
    square_frame = frame[start_y:start_y + smallest_side, start_x:start_x + smallest_side]
    return square_frame

def main():
    number_of_corners = (corners_to_be_found, corners_to_be_found)
    aantal=0
    number_succeeded=0
    for i in glob.glob('./test_images/images_with_pieces/*.jpg',recursive=True):
        path_board = i
        if "_processed" in path_board:#or "."+path_board.rsplit(".",2)[1]+"_processed.jpg" in glob.glob('./test_images/images_with_pieces/*.jpg',recursive=True)
                continue
        aantal+=1

        img=cv2.imread(path_board)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        gray = cv2.medianBlur(gray, 13)

        #gray=cv2.GaussianBlur(gray, (53, 53), 0)
       
        ret, corners = cv2.findChessboardCornersSB(gray, number_of_corners,
                                                flags= cv2.CALIB_CB_EXHAUSTIVE )
    
        if ret == True:
            number_succeeded+=1
            print("Chessboard detected",i)
        
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), 
                                        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
        
            avg_distances = determine_average_distances(corners)
        
            all_corners = extrapolate_other_corners(corners, avg_distances)
        
            img_with_corners = cv2.imread(path_board).copy()
            img_with_corners = cv2.drawChessboardCorners(img_with_corners, (BOARD_SIZE + 1, BOARD_SIZE + 1), all_corners.reshape(-1, 1, 2), ret)
            cv2.namedWindow("Chessboard", cv2.WINDOW_NORMAL)
            cv2.imshow('Chessboard', img_with_corners)
            cv2.waitKey(1)

            cv2.imwrite(path_board[:-4] + "_processed.jpg"  , img_with_corners)

            cell_centers = calculate_cell_centers(all_corners)

            # img_with_centers = img.copy()
            # for index,center in enumerate(cell_centers):
            #     if index == len(cell_centers) - 1:
            #         draw_point_and_show(img_with_centers, tuple(center), window_name="Cell Centers",wait_key=1)
            #     else:
            #         draw_point_and_show(img_with_centers, tuple(center), window_name="Cell Centers")
            
            detect_pieces(cell_centers,path_board)


        else:
            print("No chessboard detected",i)

        cv2.destroyAllWindows()
        print("score:",number_succeeded,"off the",aantal,"boards were recognized")
if __name__ == "__main__":
    main()
