import pygame
import math
import random
import numpy as np

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Enhanced Braitenberg Vehicle 3 (Crossed Wiring)")

# Colors
BG_COLOR = (10, 10, 30)
BOT_BODY = (100, 255, 100)
BOT_WHEELS = (70, 200, 70)
DETECTOR_COLOR = (255, 100, 100)
LIGHT_COLOR = (255, 255, 200)
LIGHT_GLOW = (255, 255, 150, 100)
LIGHT_CORE = (255, 255, 220)
TEXT_COLOR = (220, 220, 255)
UI_BG = (30, 30, 50, 200)
UI_BORDER = (80, 80, 120)

# Font
title_font = pygame.font.SysFont("Arial", 28, bold=True)
font = pygame.font.SysFont("Arial", 16)
small_font = pygame.font.SysFont("Arial", 14)

# Settings
FPS = 60
NUM_LIGHTS = 3
LIGHT_RADIUS = 25
LIGHT_INTENSITY = 400

# --- Braitenberg Vehicle 3 with crossed connections ---
class BraitenbergVehicle3:
    def __init__(self, position, heading):
        self.position = pygame.Vector2(position)
        self.heading = heading
        self.body_size = 15
        self.wheel_size = 8
        self.detector_size = 6
        self.sensor_distance = 35
        self.sensor_gap = 15
        self.trail = []
        self.max_trail_length = 100

        self.left_eye = pygame.Vector2()
        self.right_eye = pygame.Vector2()
        
        # Vehicle characteristics
        self.speed_multiplier = 2.5
        self.turn_sensitivity = 12
        self.wander_strength = 1.2

    def update_sensors(self):
        forward = pygame.Vector2(0, -1).rotate(self.heading)
        left = forward.rotate(90)
        right = forward.rotate(-90)
        self.left_eye = self.position + forward * self.sensor_distance + left * self.sensor_gap
        self.right_eye = self.position + forward * self.sensor_distance + right * self.sensor_gap

    def get_light_intensity(self, sensor_pos, light_pos):
        distance = sensor_pos.distance_to(light_pos)
        # Inverse square law for light intensity
        intensity = max(0, LIGHT_INTENSITY / (distance**2 + 1) - 0.01)
        return min(intensity, 1.0)  # Cap at 1.0

    def navigate(self, light_sources, surface):
        self.update_sensors()
        
        # Get light intensity for each sensor from all light sources
        left_sensor = 0
        right_sensor = 0
        
        for light in light_sources:
            left_sensor += self.get_light_intensity(self.left_eye, light.location)
            right_sensor += self.get_light_intensity(self.right_eye, light.location)

        # Crossed sensor-motor connection
        left_wheel = right_sensor
        right_wheel = left_sensor

        # Add slight random perturbation
        random_wander = random.uniform(-self.wander_strength, self.wander_strength)
        
        # Calculate turning based on wheel difference
        turn_rate = (right_wheel - left_wheel) * self.turn_sensitivity
        self.heading += turn_rate + random_wander

        # Forward movement based on average sensor input
        speed = (left_wheel + right_wheel) / 2
        speed = max(0.1, speed) * self.speed_multiplier
        movement = pygame.Vector2(0, -1).rotate(self.heading) * speed
        self.position += movement

        # Add current position to trail
        self.trail.append((self.position.x, self.position.y))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

        # Wrap screen
        self.position.x %= SCREEN_WIDTH
        self.position.y %= SCREEN_HEIGHT

        # Debug info
        telemetry = [
            f"Left Sensor → Right Wheel: {right_sensor:.3f}",
            f"Right Sensor → Left Wheel: {left_sensor:.3f}",
            f"Heading: {self.heading % 360:.1f}°",
            f"Speed: {speed:.2f}",
            f"Turn Rate: {turn_rate:.2f}°/frame"
        ]
        
        # Draw debug panel
        debug_surface = pygame.Surface((300, 150), pygame.SRCALPHA)
        debug_surface.fill(UI_BG)
        pygame.draw.rect(debug_surface, UI_BORDER, debug_surface.get_rect(), 2)
        
        title = title_font.render("Vehicle 3: Crossed Wiring", True, TEXT_COLOR)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 15))
        
        for i, line in enumerate(telemetry):
            debug = font.render(line, True, TEXT_COLOR)
            debug_surface.blit(debug, (15, 20 + i * 25))
        
        surface.blit(debug_surface, (15, 15))
        
        # Draw instructions
        instructions = [
            "CONTROLS:",
            "R - Reset Vehicle",
            "L - Add Light Source",
            "C - Clear Light Sources",
            "Mouse - Move Light Source",
            "1/2 - Adjust Sensitivity",
            "3/4 - Adjust Speed",
            "5/6 - Adjust Wander"
        ]
        
        for i, line in enumerate(instructions):
            text = small_font.render(line, True, TEXT_COLOR)
            surface.blit(text, (SCREEN_WIDTH - text.get_width() - 20, 20 + i * 20))

    def render(self, surface):
        # Draw movement trail
        if len(self.trail) > 1:
            pygame.draw.lines(surface, (50, 150, 50, 150), False, self.trail, 2)
        
        # Draw body
        pygame.draw.circle(surface, BOT_BODY, (int(self.position.x), int(self.position.y)), self.body_size)
        pygame.draw.circle(surface, BOT_WHEELS, (int(self.position.x), int(self.position.y)), self.body_size, 2)
        
        # Draw heading indicator
        heading_vector = pygame.Vector2(0, -self.body_size).rotate(self.heading)
        pygame.draw.line(surface, BOT_WHEELS, self.position, self.position + heading_vector, 2)
        
        # Draw detectors
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.left_eye.x), int(self.left_eye.y)), self.detector_size)
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.right_eye.x), int(self.right_eye.y)), self.detector_size)
        
        # Draw connections to wheels
        wheel_offset = pygame.Vector2(0, -self.body_size).rotate(self.heading - 90)
        left_wheel_pos = self.position + wheel_offset
        right_wheel_pos = self.position - wheel_offset
        
        pygame.draw.line(surface, (200, 100, 100), self.left_eye, right_wheel_pos, 1)
        pygame.draw.line(surface, (200, 100, 100), self.right_eye, left_wheel_pos, 1)
        
        pygame.draw.circle(surface, BOT_WHEELS, (int(left_wheel_pos.x), int(left_wheel_pos.y)), self.wheel_size)
        pygame.draw.circle(surface, BOT_WHEELS, (int(right_wheel_pos.x), int(right_wheel_pos.y)), self.wheel_size)

# GlowTarget class (light source)
class GlowTarget:
    def __init__(self, location):
        self.location = pygame.Vector2(location)
        self.radius = LIGHT_RADIUS
        self.pulse = 0
        self.pulse_speed = 0.05
        self.pulse_range = 5

    def update(self):
        self.pulse = (self.pulse + self.pulse_speed) % (2 * math.pi)

    def render(self, surface):
        # Create glow effect
        current_radius = self.radius + math.sin(self.pulse) * self.pulse_range
        
        # Draw glow
        glow_surface = pygame.Surface((current_radius*4, current_radius*4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, LIGHT_GLOW, 
                          (current_radius*2, current_radius*2), 
                          current_radius*2)
        surface.blit(glow_surface, (self.location.x - current_radius*2, 
                                   self.location.y - current_radius*2))
        
        # Draw light core
        pygame.draw.circle(surface, LIGHT_CORE, (int(self.location.x), int(self.location.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 150), (int(self.location.x), int(self.location.y)), self.radius, 2)

# --- Initialization ---
bot = BraitenbergVehicle3((SCREEN_WIDTH - 150, SCREEN_HEIGHT - 150), -135)
lights = [GlowTarget((SCREEN_WIDTH // 2 - 100 + i*100, SCREEN_HEIGHT // 2)) for i in range(NUM_LIGHTS)]
selected_light = None

# --- Main Loop ---
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle mouse events for light movement
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
            for light in lights:
                if mouse_pos.distance_to(light.location) < light.radius:
                    selected_light = light
                    break
        
        elif event.type == pygame.MOUSEBUTTONUP:
            selected_light = None
        
        elif event.type == pygame.MOUSEMOTION and selected_light:
            selected_light.location = pygame.Vector2(pygame.mouse.get_pos())
        
        # Keyboard controls
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # Reset vehicle
                bot = BraitenbergVehicle3((SCREEN_WIDTH - 150, SCREEN_HEIGHT - 150), -135)
            
            elif event.key == pygame.K_l:  # Add light
                lights.append(GlowTarget(pygame.Vector2(
                    random.randint(100, SCREEN_WIDTH-100),
                    random.randint(100, SCREEN_HEIGHT-100)
                )))
            
            elif event.key == pygame.K_c:  # Clear lights
                lights = []
            
            # Sensitivity controls
            elif event.key == pygame.K_1:
                bot.turn_sensitivity = max(1, bot.turn_sensitivity - 1)
            elif event.key == pygame.K_2:
                bot.turn_sensitivity = min(20, bot.turn_sensitivity + 1)
            
            # Speed controls
            elif event.key == pygame.K_3:
                bot.speed_multiplier = max(1.0, bot.speed_multiplier - 0.5)
            elif event.key == pygame.K_4:
                bot.speed_multiplier = min(5.0, bot.speed_multiplier + 0.5)
            
            # Wander controls
            elif event.key == pygame.K_5:
                bot.wander_strength = max(0.1, bot.wander_strength - 0.2)
            elif event.key == pygame.K_6:
                bot.wander_strength = min(3.0, bot.wander_strength + 0.2)

    # Update
    for light in lights:
        light.update()
    
    window.fill(BG_COLOR)
    
    # Draw grid background
    grid_color = (30, 30, 50)
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(window, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(window, grid_color, (0, y), (SCREEN_WIDTH, y), 1)
    
    # Draw center lines
    pygame.draw.line(window, (50, 50, 80), (SCREEN_WIDTH//2, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT), 2)
    pygame.draw.line(window, (50, 50, 80), (0, SCREEN_HEIGHT//2), (SCREEN_WIDTH, SCREEN_HEIGHT//2), 2)
    
    # Render lights
    for light in lights:
        light.render(window)
    
    # Update and render vehicle
    bot.navigate(lights, window)
    bot.render(window)
    
    # Draw light counter
    light_text = font.render(f"Lights: {len(lights)} (L to add, C to clear)", True, TEXT_COLOR)
    window.blit(light_text, (SCREEN_WIDTH - light_text.get_width() - 20, SCREEN_HEIGHT - 30))
    
    # Draw parameters
    params = [
        f"Sensitivity: {bot.turn_sensitivity} (1/2)",
        f"Speed: {bot.speed_multiplier} (3/4)",
        f"Wander: {bot.wander_strength:.1f} (5/6)"
    ]
    
    for i, param in enumerate(params):
        text = font.render(param, True, TEXT_COLOR)
        window.blit(text, (20, SCREEN_HEIGHT - 80 + i * 25))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()





