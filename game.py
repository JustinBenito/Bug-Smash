import cv2
import numpy as np
import pygame
import random

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bug Catcher Game")

# Load Bug Image
bug_img = pygame.image.load("bug.png")
bug_img = pygame.transform.scale(bug_img, (50, 50))

# Generate Bugs
bugs = [{"x": random.randint(50, WIDTH-50), "y": random.randint(50, HEIGHT-50), 
         "value": random.choice([-10, 10])} for _ in range(5)]

score = 0
running = True

# Start Webcam Capture
cap = cv2.VideoCapture(0)

def detect_fingertip(frame):
    """Detects hand and returns the index fingertip coordinates."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define skin color range
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)
    
    # Threshold to get skin region
    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Apply Morphological Transformations
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (5, 5), 100)

    # Find Contours
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        max_contour = max(contours, key=cv2.contourArea)  # Largest contour
        hull = cv2.convexHull(max_contour)

        # Find Extreme Top Point (Index Finger Tip)
        top_point = tuple(hull[hull[:, :, 1].argmin()][0])

        # Flip X-axis to match Pygame's mirrored display
        pygame_x = WIDTH - int(top_point[0] * WIDTH / frame.shape[1])
        pygame_y = int(top_point[1] * HEIGHT / frame.shape[0])

        return (pygame_x, pygame_y)
    return None

while running:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)  # Flip horizontally for correct orientation
    finger_tip = detect_fingertip(frame)

    # Convert OpenCV image (BGR) to Pygame surface (RGB)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)  # Rotate to match Pygame coordinate system
    frame = pygame.surfarray.make_surface(frame)
    frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))  # Resize to fit game window

    # Display Camera Feed in Pygame
    screen.blit(frame, (0, 0))

    # Draw Bugs
    for bug in bugs:
        screen.blit(bug_img, (bug["x"], bug["y"]))
        bug_text = pygame.font.SysFont("Arial", 24).render(str(bug["value"]), True, (255, 255, 255))
        screen.blit(bug_text, (bug["x"] + 15, bug["y"] + 15))

    # Check Collision Between Hand & Bug
    if finger_tip:
        pygame.draw.circle(screen, (0, 255, 0), finger_tip, 10)  # Draw detected fingertip
        for bug in bugs[:]:  
            if bug["x"] < finger_tip[0] < bug["x"] + 50 and bug["y"] < finger_tip[1] < bug["y"] + 50:
                score += bug["value"]
                bugs.remove(bug)  
                bugs.append({"x": random.randint(50, WIDTH-50), "y": random.randint(50, HEIGHT-50), "value": random.choice([-10, 10])})

    # Display Score
    score_text = pygame.font.SysFont("Arial", 36).render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    # Update Display
    pygame.display.flip()

    # Check for Quit Event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

cap.release()
pygame.quit()
cv2.destroyAllWindows()
