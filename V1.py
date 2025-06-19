import pygame
import random
import math

# Initialize Pygame
pygame.init()
pygame.font.init()

# Constants
WIDTH, HEIGHT = 600, 600
FPS = 120


WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Screen & Font
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Random Microbe Vehicle")
font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()


class Circle:
    def __init__(self, position, radius=50, color=WHITE):
        self.position = pygame.math.Vector2(position)
        self.radius = radius
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.position, self.radius)


class Vehicle:
    def __init__(self, position, radius=30, color=YELLOW):
        self.position = pygame.math.Vector2(position)
        self.radius = radius
        self.color = color

        self.speed = random.uniform(1, 3)
        self.direction = random.uniform(0, 360)
        self.sensor_radius = 10
        self.sensor_offset = self.radius + self.sensor_radius
        self.sensor_color = GREEN
        self.detected_object = None

        self.update_sensor_position()

    def update_sensor_position(self):
        offset_vector = pygame.math.Vector2(0, -self.sensor_offset).rotate(self.direction)
        self.sensor_position = self.position + offset_vector

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.position, self.radius)
        
        # Change sensor color if detecting something
        sensor_color = RED if self.detected_object else GREEN
        pygame.draw.circle(surface, sensor_color, self.sensor_position, self.sensor_radius)
        
        pygame.draw.line(surface, WHITE, self.position, self.sensor_position, 2)

    def check_sensor(self, objects):
        self.detected_object = None
        for obj in objects:
            distance = self.sensor_position.distance_to(obj.position)
            if distance < obj.radius + self.sensor_radius:
                self.detected_object = obj
                return True
        return False

    def move(self, objects):
        # Check sensor first
        self.check_sensor(objects)
        
        # If detecting something, avoid it
        if self.detected_object:
            # Calculate vector away from detected object
            avoid_vector = self.position - self.detected_object.position
            self.direction = avoid_vector.angle_to(pygame.math.Vector2(1, 0))
        else:
            # Random movement if nothing detected
            self.direction += random.uniform(-10, 10)
        
        self.direction %= 360
        
        direction_vector = pygame.math.Vector2(1, 0).rotate(self.direction)
        self.position += direction_vector * self.speed
        self.position.x %= WIDTH
        self.position.y %= HEIGHT
        
        self.update_sensor_position()


# Create objects
sun = Circle((WIDTH // 2, HEIGHT // 2), radius=50, color=WHITE)
obstacles = [Circle((random.randint(0, WIDTH), random.randint(0, HEIGHT)), 
              radius=random.randint(10, 30), 
              color=BLUE) for _ in range(5)]
vehicle = Vehicle((300, 500), radius=30, color=YELLOW)

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    # Update and draw objects
    sun.draw(screen)
    for obstacle in obstacles:
        obstacle.draw(screen)
    
    vehicle.move([sun] + obstacles)
    vehicle.draw(screen)

    # Debug info
    screen.blit(font.render(f"Direction: {vehicle.direction:.2f}", True, WHITE), (10, 10))
    screen.blit(font.render(f"Detecting: {'Yes' if vehicle.detected_object else 'No'}", True, WHITE), (10, 40))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()



