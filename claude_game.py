import cv2
import numpy as np
import random
import time
import os
import sys
import subprocess

class BugSquashGame:
    def __init__(self):
        # Game settings
        self.screen_width = 640
        self.screen_height = 480
        self.bug_size = 40
        self.num_bugs = 5
        self.score = 0
        self.game_over = False
        self.start_time = time.time()
        self.game_duration = 60  # Game duration in seconds
        
        # Default to demo mode and attempt to initialize camera
        self.demo_mode = True
        self.initialize_camera()
        
        # Create bugs
        self.bugs = []
        self.create_bugs(self.num_bugs)
        
        # Load bug image
        self.bug_img = self.load_bug_image()
        
        # Background subtractor for hand detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=36, detectShadows=False)
        
        # Set up font
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Background collection settings
        self.collecting_bg = True
        self.bg_collection_frames = 15
        self.bg_collected = 0
        self.last_bg_collect_time = time.time()
        
        # Force progression to gameplay after timeout
        self.force_progress_timeout = 5  # seconds

    def initialize_camera(self):
        """Try to initialize the camera with fallback to demo mode"""
        print("Attempting to initialize camera...")
        
        # On macOS, try to reset the camera system
        if sys.platform == 'darwin':
            try:
                print("Resetting macOS camera system...")
                subprocess.run(['killall', 'VDCAssistant'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(1)
            except:
                pass
        
        # Try camera indices 0, 1, and 2
        for idx in range(3):
            print(f"Trying camera index {idx}...")
            
            try:
                cap = cv2.VideoCapture(idx)
                
                if cap.isOpened():
                    # Test if we can actually read a frame
                    ret, frame = cap.read()
                    
                    if ret and frame is not None and frame.size > 0:
                        print(f"Successfully connected to camera {idx}")
                        self.cap = cap
                        self.demo_mode = False
                        
                        # Try to set resolution
                        try:
                            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.screen_width)
                            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.screen_height)
                        except:
                            pass
                        
                        # Update dimensions from actual camera
                        ret, frame = self.cap.read()
                        if ret:
                            self.screen_height, self.screen_width = frame.shape[:2]
                        
                        return True
                    else:
                        print(f"Camera {idx} opened but couldn't read frames")
                        cap.release()
                else:
                    print(f"Failed to open camera {idx}")
            except Exception as e:
                print(f"Error accessing camera {idx}: {str(e)}")
        
        print("Could not initialize any camera, falling back to demo mode")
        self.demo_mode = True
        return False

    def get_frame(self):
        """Get a frame from the camera or generate a demo frame"""
        if not self.demo_mode and self.cap is not None:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    return cv2.flip(frame, 1)  # Flip horizontally
            except Exception as e:
                print(f"Error capturing frame: {str(e)}")
                self.demo_mode = True
        
        # Generate a demo frame if no camera
        demo_frame = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        
        # Add some text to the demo frame
        cv2.putText(demo_frame, "DEMO MODE - NO CAMERA DETECTED", 
                   (20, self.screen_height // 2 - 20), self.font, 0.7, (255, 255, 255), 2)
        cv2.putText(demo_frame, "Click on bugs to squash them", 
                   (60, self.screen_height // 2 + 20), self.font, 0.7, (255, 255, 255), 2)
        
        return demo_frame

    def load_bug_image(self):
        """Create a simple bug image"""
        bug = np.zeros((self.bug_size, self.bug_size, 4), dtype=np.uint8)
        
        # Create a black body with transparency
        cv2.circle(bug, (self.bug_size // 2, self.bug_size // 2), self.bug_size // 3, (0, 0, 0, 255), -1)
        
        # Add red eyes
        eye_radius = self.bug_size // 10
        eye_offset = self.bug_size // 6
        cv2.circle(bug, (self.bug_size // 2 - eye_offset, self.bug_size // 2 - eye_offset), 
                   eye_radius, (0, 0, 255, 255), -1)
        cv2.circle(bug, (self.bug_size // 2 + eye_offset, self.bug_size // 2 - eye_offset), 
                   eye_radius, (0, 0, 255, 255), -1)
        
        # Add legs
        leg_color = (0, 0, 0, 255)
        leg_thickness = 2
        
        # Bottom legs
        cv2.line(bug, (self.bug_size // 3, self.bug_size // 3 * 2), 
                 (self.bug_size // 6, self.bug_size - 5), leg_color, leg_thickness)
        cv2.line(bug, (self.bug_size // 3 * 2, self.bug_size // 3 * 2), 
                 (self.bug_size - 5, self.bug_size - 5), leg_color, leg_thickness)
        
        # Middle legs
        cv2.line(bug, (self.bug_size // 6, self.bug_size // 2), 
                 (0, self.bug_size // 2), leg_color, leg_thickness)
        cv2.line(bug, (self.bug_size - self.bug_size // 6, self.bug_size // 2), 
                 (self.bug_size, self.bug_size // 2), leg_color, leg_thickness)
        
        # Top legs
        cv2.line(bug, (self.bug_size // 3, self.bug_size // 3), 
                 (self.bug_size // 6, 5), leg_color, leg_thickness)
        cv2.line(bug, (self.bug_size // 3 * 2, self.bug_size // 3), 
                 (self.bug_size - 5, 5), leg_color, leg_thickness)
        
        return bug

    def create_bugs(self, num_bugs):
        """Create the specified number of bugs"""
        self.bugs = []
        for _ in range(num_bugs):
            x = random.randint(0, self.screen_width - self.bug_size)
            y = random.randint(0, self.screen_height - self.bug_size)
            dx = random.choice([-2, -1, 1, 2])
            dy = random.choice([-2, -1, 1, 2])
            self.bugs.append({
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy,
                'alive': True,
                'death_time': 0
            })

    def update_bugs(self):
        """Update bug positions and create new ones if needed"""
        current_time = time.time()
        
        # Check if we need to create new bugs
        alive_bugs = sum(1 for bug in self.bugs if bug['alive'])
        if alive_bugs < self.num_bugs:
            for _ in range(self.num_bugs - alive_bugs):
                x = random.randint(0, self.screen_width - self.bug_size)
                y = random.randint(0, self.screen_height - self.bug_size)
                dx = random.choice([-2, -1, 1, 2])
                dy = random.choice([-2, -1, 1, 2])
                self.bugs.append({
                    'x': x,
                    'y': y,
                    'dx': dx,
                    'dy': dy,
                    'alive': True,
                    'death_time': 0
                })
        
        # Update bug positions
        bugs_to_remove = []
        for i, bug in enumerate(self.bugs):
            if bug['alive']:
                # Update position
                bug['x'] += bug['dx']
                bug['y'] += bug['dy']
                
                # Bounce off edges
                if bug['x'] <= 0 or bug['x'] >= self.screen_width - self.bug_size:
                    bug['dx'] *= -1
                    # Adjust position to ensure it's inside bounds
                    bug['x'] = max(0, min(bug['x'], self.screen_width - self.bug_size))
                
                if bug['y'] <= 0 or bug['y'] >= self.screen_height - self.bug_size:
                    bug['dy'] *= -1
                    # Adjust position to ensure it's inside bounds
                    bug['y'] = max(0, min(bug['y'], self.screen_height - self.bug_size))
                    
                # Randomly change direction occasionally
                if random.random() < 0.02:
                    bug['dx'] = random.choice([-2, -1, 1, 2])
                    bug['dy'] = random.choice([-2, -1, 1, 2])
            else:
                # Remove dead bugs after a delay
                if current_time - bug['death_time'] > 0.5:
                    bugs_to_remove.append(i)
        
        # Remove dead bugs (in reverse order to avoid index issues)
        for i in sorted(bugs_to_remove, reverse=True):
            if i < len(self.bugs):  # Safety check
                self.bugs.pop(i)

    def overlay_bug(self, frame, bug):
        """Overlay a bug onto the frame"""
        if not bug['alive']:
            return
            
        # Extract bug location and size
        x, y = bug['x'], bug['y']
        h, w = self.bug_img.shape[:2]
        
        # Safety check to make sure the bug is within frame
        if x < 0 or y < 0 or x + w >= frame.shape[1] or y + h >= frame.shape[0]:
            return
            
        try:
            # Create an overlay mask for the bug
            overlay = frame[y:y+h, x:x+w].copy()
            alpha_mask = self.bug_img[:, :, 3] / 255.0
            alpha_mask = np.stack([alpha_mask, alpha_mask, alpha_mask], axis=2)
            
            # Apply the bug to the frame
            bug_rgb = self.bug_img[:, :, :3]
            frame[y:y+h, x:x+w] = overlay * (1 - alpha_mask) + bug_rgb * alpha_mask
        except Exception as e:
            print(f"Error overlaying bug: {str(e)}")

    def detect_hand(self, frame):
        """Detect the player's hand using background subtraction"""
        if self.demo_mode:
            return None  # Skip hand detection in demo mode
            
        # Check if we need to collect more background frames
        if self.collecting_bg:
            # Check for force progression timeout
            current_time = time.time()
            
            # Process background frame
            try:
                self.bg_subtractor.apply(frame)
                self.bg_collected += 1
                self.last_bg_collect_time = current_time
                
                # Progress either when we have enough frames or timeout
                if (self.bg_collected >= self.bg_collection_frames or 
                    current_time - self.start_time > self.force_progress_timeout):
                    print(f"Background collection complete with {self.bg_collected} frames")
                    self.collecting_bg = False
            except Exception as e:
                print(f"Error in background collection: {str(e)}")
                # Force progression if we encounter an error
                self.collecting_bg = False
                
            return None
        
        try:
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Apply morphological operations to remove noise
            kernel = np.ones((5, 5), np.uint8)
            fg_mask = cv2.erode(fg_mask, kernel, iterations=1)
            fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
            
            # Threshold to get foreground
            _, fg_mask = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get the largest contour (likely the hand)
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 2000:  # Minimum area to consider as a hand
                    return largest_contour
        except Exception as e:
            print(f"Error in hand detection: {str(e)}")
        
        return None

    def check_collisions(self, hand_contour=None, mouse_pos=None):
        """Check if the hand or mouse is touching any bugs"""
        current_time = time.time()
        
        if hand_contour is not None:
            try:
                # Create a mask from the hand contour
                hand_mask = np.zeros((self.screen_height, self.screen_width), dtype=np.uint8)
                cv2.drawContours(hand_mask, [hand_contour], 0, 255, -1)
                
                # Check collision with each bug
                for bug in self.bugs:
                    if not bug['alive']:
                        continue
                        
                    # Create a mask for the bug
                    bug_mask = np.zeros((self.screen_height, self.screen_width), dtype=np.uint8)
                    cv2.rectangle(bug_mask, (bug['x'], bug['y']), 
                                (bug['x'] + self.bug_size, bug['y'] + self.bug_size), 255, -1)
                    
                    # Check if they overlap
                    overlap = cv2.bitwise_and(hand_mask, bug_mask)
                    if cv2.countNonZero(overlap) > 0:
                        # Bug is squashed!
                        bug['alive'] = False
                        bug['death_time'] = current_time
                        self.score += 1
                        print(f"Bug squashed! Score: {self.score}")
            except Exception as e:
                print(f"Error checking hand collisions: {str(e)}")
        
    

    def display_info(self, frame):
        """Display game information on the frame"""
        # Display score
        cv2.putText(frame, f"Score: {self.score}", (10, 30), self.font, 0.7, (0, 255, 0), 2)
        
        # Display time
        elapsed_time = int(time.time() - self.start_time)
        remaining_time = max(0, self.game_duration - elapsed_time)
        cv2.putText(frame, f"Time: {remaining_time} s", (10, 60), self.font, 0.7, (0, 255, 0), 2)
        
        # Display instructions
        if self.demo_mode:
            cv2.putText(frame, "DEMO MODE: Click on bugs to squash them", 
                       (self.screen_width // 6, 30), self.font, 0.7, (0, 255, 255), 2)
        elif self.collecting_bg:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.force_progress_timeout - elapsed)
            bg_text = f"Collecting background... {self.bg_collected}/{self.bg_collection_frames} (Auto-start in {remaining:.1f}s)"
            cv2.putText(frame, bg_text, (10, self.screen_height // 2),
                       self.font, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "Please stand clear of the camera", 
                       (60, self.screen_height // 2 + 30),
                       self.font, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Use hand to squash bugs", (self.screen_width // 3, 30), 
                       self.font, 0.7, (0, 255, 255), 2)
        
        cv2.putText(frame, "Press 'q' to quit", (self.screen_width - 200, 30), 
                   self.font, 0.7, (0, 255, 0), 2)
        
        # Check if game time is up
        if remaining_time <= 0:
            cv2.putText(frame, "GAME OVER!", (self.screen_width // 3, self.screen_height // 2),
                       self.font, 1.2, (0, 0, 255), 3)
            cv2.putText(frame, f"Final Score: {self.score}", 
                       (self.screen_width // 3, self.screen_height // 2 + 40),
                       self.font, 1, (0, 255, 255), 2)
            cv2.putText(frame, "Press 'q' to quit or 'r' to restart", 
                       (self.screen_width // 6, self.screen_height // 2 + 80),
                       self.font, 0.7, (255, 255, 255), 2)
            self.game_over = True



    def run(self):
        """Main game loop"""
        print("Starting Bug Squash Game!")
        
        # Setup mouse callback for clicks
        cv2.namedWindow('Bug Squash Game')
        cv2.setMouseCallback('Bug Squash Game', self.mouse_callback)
        
        if not self.demo_mode:
            print("Stand clear of the camera while background is collected...")
            print(f"Game will automatically start in {self.force_progress_timeout} seconds")
            print("You can also click anywhere to skip background collection")
        else:
            print("Running in DEMO MODE - click on bugs to squash them")
        
        try:
            while True:
                # Get frame
                frame = self.get_frame()
                if frame is None:
                    print("Failed to get frame")
                    time.sleep(0.1)  # Add a small delay to prevent CPU overuse
                    continue
                
                # Create a copy of the frame to draw on
                display_frame = frame.copy()
                
                # Only draw bugs if we're in gameplay phase or demo mode
                if not self.collecting_bg or self.demo_mode:
                    # Update bug positions if game is active
                    if not self.game_over:
                        self.update_bugs()
                    
                    # Draw bugs on the frame
                    for bug in self.bugs:
                        self.overlay_bug(display_frame, bug)
                    
                    # Detect hand (only in camera mode)
                    hand_contour = None
                    if not self.demo_mode:
                        hand_contour = self.detect_hand(frame)
                        
                        # Draw hand contour for feedback
                        if hand_contour is not None:
                            cv2.drawContours(display_frame, [hand_contour], 0, (0, 255, 0), 2)
                    
                    # Check for hand collisions if not in game over state
                    if not self.game_over and hand_contour is not None:
                        self.check_collisions(hand_contour=hand_contour)
                else:
                    # Process background collection
                    self.detect_hand(frame)
                
                # Display game information
                self.display_info(display_frame)
                
                # Show the frame
                cv2.imshow('Bug Squash Game', display_frame)
                
                # Process key presses
                key = cv2.waitKey(1) & 0xFF
                
                # Handle key presses
                if key == ord('q'):
                    break
                elif key == ord('r') and self.game_over:
                    # Restart the game
                    self.score = 0
                    self.game_over = False
                    self.start_time = time.time()
                    self.create_bugs(self.num_bugs)
                elif key == ord(' '):
                    # Space bar skips background collection
                    if self.collecting_bg:
                        print("Skipping background collection")
                        self.collecting_bg = False
        
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
        finally:
            # Clean up
            if not self.demo_mode and hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
            print(f"Game Over! Final Score: {self.score}")

if __name__ == "__main__":
    # Create and run the game
    game = BugSquashGame()
    game.run()