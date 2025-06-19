import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Braitenberg Vehicle 2b (Coward)")

# Colors
BG_COLOR = (0, 0, 0)         # Background color (black)
BOT_COLOR = (0, 255, 0)      # Bot color (green)
DETECTOR_COLOR = (255, 0, 0) # Sensor color (red)
LABEL_COLOR = (255, 255, 255) # Text color (white)

# Fonts for debugging info
font = pygame.font.SysFont("Arial", 18)

# Settings
FPS = 60

# Braitenberg Vehicle 2b (Coward) class
class BraitenbergVehicle:
    def __init__(self, position, heading):
        self.position = pygame.Vector2(position)
        self.heading = heading
        self.body_size = 10
        self.detector_size = 5
        self.sensor_distance = 30
        self.sensor_gap = 10

        self.left_eye = pygame.Vector2()
        self.right_eye = pygame.Vector2()

    def update_sensors(self):
        forward = pygame.Vector2(0, -1).rotate(self.heading)
        left = forward.rotate(90)
        right = forward.rotate(-90)
        self.left_eye = self.position + forward * self.sensor_distance + left * self.sensor_gap
        self.right_eye = self.position + forward * self.sensor_distance + right * self.sensor_gap

    def get_light_intensity(self, sensor_pos, light_pos):
        """Calculate the light intensity based on distance from light source."""
        distance = sensor_pos.distance_to(light_pos)
        # Simple inverse linear drop-off
        intensity = max(0, 1 - (distance / 400))  # 400 is light range
        return intensity

    def navigate(self, target_pos, surface):
        self.update_sensors()

        # Get the light intensity from both sensors
        left_intensity = self.get_light_intensity(self.left_eye, target_pos)
        right_intensity = self.get_light_intensity(self.right_eye, target_pos)

        # Vehicle 2b (Coward) behavior:
        # Crossed connections: left sensor controls right motor, right sensor controls left motor
        left_motor = right_intensity  # Right sensor controls left motor
        right_motor = left_intensity  # Left sensor controls right motor
        
        # Calculate turn based on motor difference
        turn = (right_motor - left_motor) * 3.0  # Increased turn sensitivity
        
        # Add random wandering
        random_wander_strength = 1.5  # Degrees per frame
        turn += random.uniform(-random_wander_strength, random_wander_strength)
        
        # Apply turn to heading
        self.heading += turn
        
        # Base speed is average of both motors
        motor_speed = (left_motor + right_motor) / 2
        motor_speed = max(0.1, motor_speed)  # Ensure minimum movement

        # Move forward
        forward = pygame.Vector2(0, -1).rotate(self.heading)
        movement = forward * motor_speed * 2.0  # Speed scale
        self.position += movement

        # Wrap around screen
        self.position.x %= SCREEN_WIDTH
        self.position.y %= SCREEN_HEIGHT

        # Debug telemetry
        telemetry = [
            f"L-Sensor: {left_intensity:.2f}",
            f"R-Sensor: {right_intensity:.2f}",
            f"L-Motor: {left_motor:.2f}",
            f"R-Motor: {right_motor:.2f}",
            f"Turn: {turn:.2f}°",
            f"Speed: {motor_speed * 2.0:.2f}",
            f"Heading: {self.heading:.2f}°"
        ]
        for i, line in enumerate(telemetry):
            debug = font.render(line, True, LABEL_COLOR)
            surface.blit(debug, (10, 10 + i * 20))

    def render(self, surface):
        pygame.draw.circle(surface, BOT_COLOR, (int(self.position.x), int(self.position.y)), self.body_size)
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.left_eye.x), int(self.left_eye.y)), self.detector_size)
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.right_eye.x), int(self.right_eye.y)), self.detector_size)

        tag = font.render("Braitenberg Vehicle 2b: Coward", True, LABEL_COLOR)
        tag_rect = tag.get_rect(center=(self.position.x, self.position.y - 25))
        surface.blit(tag, tag_rect)

# GlowTarget class
class GlowTarget:
    def __init__(self, location):
        self.location = pygame.Vector2(location)

    def render(self, surface):
        pygame.draw.circle(surface, (255, 255, 0), (int(self.location.x), int(self.location.y)), 15)

# --- Initialization ---
bot = BraitenbergVehicle((SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80), -135)
beacon = GlowTarget((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

# --- Main Loop ---
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    window.fill(BG_COLOR)
    beacon.render(window)
    bot.navigate(beacon.location, window)
    bot.render(window)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()













