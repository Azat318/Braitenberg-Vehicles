import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Braitenberg Vehicle 4 with Obstacle Avoidance")

# Colors
BG_COLOR = (0, 0, 0)
BOT_COLOR = (0, 150, 255)
DETECTOR_COLOR = (255, 100, 100)
OBSTACLE_COLOR = (100, 100, 100)
LABEL_COLOR = (255, 255, 255)
BUMPER_COLOR = (0, 255, 0)  # Green for bumper sensors

# Font
font = pygame.font.SysFont("Arial", 18)

# Settings
FPS = 60
MAX_SPEED = 3.0
VISION_RANGE = 200
OBSTACLE_THRESHOLD = 50
REPULSION_STRENGTH = 0.8

# Obstacle class
class Obstacle:
    def __init__(self, position, radius=30):
        self.position = pygame.Vector2(position)
        self.radius = radius
        
    def render(self, surface):
        pygame.draw.circle(surface, OBSTACLE_COLOR, (int(self.position.x), int(self.position.y)), self.radius)

# Braitenberg Vehicle 4 with crossed inhibitory connections
class BraitenbergVehicle4:
    def __init__(self, position, heading):
        self.position = pygame.Vector2(position)
        self.heading = heading
        self.body_size = 10
        self.detector_size = 5
        self.sensor_distance = 30
        self.sensor_gap = 10
        self.bumper_distance = 25  # Distance for obstacle sensors
        self.bumper_gap = 12       # Side offset for obstacle sensors

        self.left_eye = pygame.Vector2()
        self.right_eye = pygame.Vector2()
        self.left_bumper = pygame.Vector2()
        self.right_bumper = pygame.Vector2()

        # Wheel speeds for rendering
        self.left_wheel_speed = 0
        self.right_wheel_speed = 0

    def update_sensors(self):
        forward = pygame.Vector2(0, -1).rotate(self.heading)
        left = forward.rotate(90)
        right = forward.rotate(-90)
        
        # Light sensors
        self.left_eye = self.position + forward * self.sensor_distance + left * self.sensor_gap
        self.right_eye = self.position + forward * self.sensor_distance + right * self.sensor_gap
        
        # Obstacle sensors (bumpers)
        self.left_bumper = self.position + forward * self.bumper_distance + left * self.bumper_gap
        self.right_bumper = self.position + forward * self.bumper_distance + right * self.bumper_gap

    def get_light_intensity(self, sensor_pos, light_pos):
        distance = sensor_pos.distance_to(light_pos)
        if distance > VISION_RANGE:
            return 0  # Beyond vision range
        intensity = max(0, 1 - (distance / VISION_RANGE))  # Fall-off within vision range
        return intensity

    def get_obstacle_repulsion(self, sensor_pos, obstacle):
        distance = sensor_pos.distance_to(obstacle.position) - obstacle.radius
        if distance > OBSTACLE_THRESHOLD:
            return 0  # Beyond detection range
        
        # Stronger repulsion when closer to obstacle
        if distance <= 0:
            return 1.0  # Maximum repulsion when touching
        return (OBSTACLE_THRESHOLD - distance) / OBSTACLE_THRESHOLD

    def navigate(self, light_sources, obstacles, surface):
        self.update_sensors()

        # Sum light intensities from all sources within vision range
        left_sensor = sum(self.get_light_intensity(self.left_eye, light.location) for light in light_sources)
        right_sensor = sum(self.get_light_intensity(self.right_eye, light.location) for light in light_sources)

        # Sum obstacle repulsions
        left_repulsion = sum(self.get_obstacle_repulsion(self.left_bumper, obs) for obs in obstacles)
        right_repulsion = sum(self.get_obstacle_repulsion(self.right_bumper, obs) for obs in obstacles)

        # Crossed inhibitory connections for lights
        max_signal = 1.0
        left_wheel = max_signal - right_sensor
        right_wheel = max_signal - left_sensor

        # Apply obstacle avoidance
        left_wheel -= left_repulsion * REPULSION_STRENGTH
        right_wheel -= right_repulsion * REPULSION_STRENGTH

        # Clamp wheel speeds to valid range
        left_wheel = max(0, min(max_signal, left_wheel))
        right_wheel = max(0, min(max_signal, right_wheel))

        # Store for rendering
        self.left_wheel_speed = left_wheel
        self.right_wheel_speed = right_wheel

        # Add slight random perturbation
        random_wander_strength = 0.5
        self.heading += random.uniform(-random_wander_strength, random_wander_strength)

        # Turning
        turn_rate = (right_wheel - left_wheel) * 10
        self.heading += turn_rate

        # Forward movement with speed limit
        speed = min(MAX_SPEED, (left_wheel + right_wheel) / 2)
        speed = max(0.1, speed)  # Minimum speed
        movement = pygame.Vector2(0, -1).rotate(self.heading) * speed * 2.0
        self.position += movement

        # Wrap screen
        self.position.x %= SCREEN_WIDTH
        self.position.y %= SCREEN_HEIGHT

        # Info
        telemetry = [
            f"Left Sensor: {left_sensor:.2f}, inhibits Right Wheel",
            f"Right Sensor: {right_sensor:.2f}, inhibits Left Wheel",
            f"Left Repulsion: {left_repulsion:.2f}",
            f"Right Repulsion: {right_repulsion:.2f}",
            f"Left Wheel Speed: {left_wheel:.2f}",
            f"Right Wheel Speed: {right_wheel:.2f}",
            f"Heading: {self.heading:.2f}",
            f"Speed: {speed * 2.0:.2f}",
            f"Vision Range: {VISION_RANGE}",
            f"Max Speed: {MAX_SPEED}"
        ]
        for i, line in enumerate(telemetry):
            debug = font.render(line, True, LABEL_COLOR)
            surface.blit(debug, (10, 10 + i * 20))

    def render(self, surface):
        # Draw body
        pygame.draw.circle(surface, BOT_COLOR, (int(self.position.x), int(self.position.y)), self.body_size)

        # Draw sensors
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.left_eye.x), int(self.left_eye.y)), self.detector_size)
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.right_eye.x), int(self.right_eye.y)), self.detector_size)
        
        # Draw bumpers
        pygame.draw.circle(surface, BUMPER_COLOR, (int(self.left_bumper.x), int(self.left_bumper.y)), 4)
        pygame.draw.circle(surface, BUMPER_COLOR, (int(self.right_bumper.x), int(self.right_bumper.y)), 4)

        # Draw wheels
        forward = pygame.Vector2(0, -1).rotate(self.heading)
        left = forward.rotate(90)
        right = forward.rotate(-90)
        left_wheel_pos = self.position + left * (self.sensor_gap + 5)
        right_wheel_pos = self.position + right * (self.sensor_gap + 5)

        # Brightness reflects wheel speed
        lw_intensity = int(self.left_wheel_speed * 255)
        rw_intensity = int(self.right_wheel_speed * 255)

        pygame.draw.circle(surface, (lw_intensity, lw_intensity, lw_intensity), (int(left_wheel_pos.x), int(left_wheel_pos.y)), 5)
        pygame.draw.circle(surface, (rw_intensity, rw_intensity, rw_intensity), (int(right_wheel_pos.x), int(right_wheel_pos.y)), 5)

        # Label
        tag = font.render("Braitenberg Vehicle 4 with Obstacle Avoidance", True, LABEL_COLOR)
        tag_rect = tag.get_rect(center=(self.position.x, self.position.y - 20))
        surface.blit(tag, tag_rect)

        # Draw vision range (semi-transparent circle)
        vision_surface = pygame.Surface((VISION_RANGE*2, VISION_RANGE*2), pygame.SRCALPHA)
        pygame.draw.circle(vision_surface, (50, 50, 150, 50), (VISION_RANGE, VISION_RANGE), VISION_RANGE)
        surface.blit(vision_surface, (self.position.x - VISION_RANGE, self.position.y - VISION_RANGE))

# GlowTarget class (light source)
class GlowTarget:
    def __init__(self, location):
        self.location = pygame.Vector2(location)

    def render(self, surface):
        pygame.draw.circle(surface, (255, 255, 0), (int(self.location.x), int(self.location.y)), 15)
        # Draw light radius indicator
        light_radius_surface = pygame.Surface((VISION_RANGE*2, VISION_RANGE*2), pygame.SRCALPHA)
        pygame.draw.circle(light_radius_surface, (255, 255, 0, 20), (VISION_RANGE, VISION_RANGE), VISION_RANGE)
        surface.blit(light_radius_surface, (self.location.x - VISION_RANGE, self.location.y - VISION_RANGE))

# Initialization
bot = BraitenbergVehicle4((SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80), -135)
light_sources = [
    GlowTarget((150, 150)),
    GlowTarget((650, 450))
]

# Create obstacles
obstacles = [
    Obstacle((400, 300), 40),
    Obstacle((200, 400), 35),
    Obstacle((600, 200), 45),
    Obstacle((300, 500), 30)
]

# Main Loop
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    window.fill(BG_COLOR)

    # Render all lights
    for light in light_sources:
        light.render(window)
    
    # Render all obstacles
    for obstacle in obstacles:
        obstacle.render(window)

    # Navigate and render bot
    bot.navigate(light_sources, obstacles, window)
    bot.render(window)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()




