import pygame
import math
import random
import time
from collections import deque

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Enhanced Braitenberg Vehicle 6")

# Colors
BG_COLOR = (10, 10, 25)
BOT_COLOR = (0, 150, 255)
DETECTOR_COLOR = (255, 100, 100)
LABEL_COLOR = (220, 220, 255)
OBSTACLE_COLOR = (80, 80, 100)
DANGER_COLOR = (255, 50, 50)
LIGHT_COLOR = (255, 255, 150)
PATH_COLOR = (100, 200, 255, 100)
MEMORY_COLOR = (255, 50, 50, 150)

# Font
font = pygame.font.SysFont("Arial", 16)
title_font = pygame.font.SysFont("Arial", 24, bold=True)

# Settings
FPS = 90
GRID_SIZE = 40  # Size of grid cells for memory map
COLLISION_DECAY = 0.98  # Faster decay for collision memory
MEMORY_SHARING_DISTANCE = 200

# Static obstacles
static_obstacles = [
    pygame.Rect(200, 150, 100, 200),
    pygame.Rect(500, 300, 150, 100),
    pygame.Rect(300, 450, 200, 50),
    pygame.Rect(150, 400, 80, 80),
    pygame.Rect(600, 150, 100, 100),
    pygame.Rect(750, 500, 150, 80)
]

# Collision memory grid (threshold map)
collision_map = [[0 for _ in range(SCREEN_WIDTH // GRID_SIZE)] for _ in range(SCREEN_HEIGHT // GRID_SIZE)]
last_update_time = time.time()

# Create a surface for the memory grid visualization
memory_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

# Braitenberg Vehicle 6
class BraitenbergVehicle6:
    def __init__(self, position, heading, name, index):
        self.name = name
        self.index = index
        self.position = pygame.Vector2(position)
        self.heading = heading
        self.target_heading = heading
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = 0.5
        self.max_speed = 3.5
        
        self.body_size = 12
        self.detector_size = 6
        self.sensor_distance = 40
        self.sensor_gap = 12
        self.max_turn_rate = 4.0  # Max degrees per frame to turn
        
        self.left_eye = pygame.Vector2()
        self.right_eye = pygame.Vector2()
        
        self.left_history = deque([0.0] * 20, maxlen=20)
        self.right_history = deque([0.0] * 20, maxlen=20)
        
        self.left_wheel_speed = 0
        self.right_wheel_speed = 0
        
        self.path = deque(maxlen=100)  # Store recent positions for path drawing
        self.collision_count = 0
        self.last_collision_time = 0
        self.avoidance_vector = pygame.Vector2(0, 0)
        self.avoidance_strength = 0
        self.raycast_points = []

    def update_sensors(self):
        forward = pygame.Vector2(0, -1).rotate(self.heading)
        left = forward.rotate(90)
        right = forward.rotate(-90)
        self.left_eye = self.position + forward * self.sensor_distance + left * self.sensor_gap
        self.right_eye = self.position + forward * self.sensor_distance + right * self.sensor_gap

    def get_light_intensity(self, sensor_pos, light_pos):
        distance = sensor_pos.distance_to(light_pos)
        return max(0, 1 - (distance / 500) ** 1.5)  # Non-linear falloff

    def raycast(self, start, end, obstacles):
        """Cast a ray from start to end and return collision point if any"""
        direction = (end - start)
        max_distance = direction.length()
        direction.normalize_ip()
        
        closest_t = float('inf')
        collision_point = None
        normal = None
        
        for obs in obstacles:
            # Calculate intersection with rectangle
            t_near = pygame.Vector2(
                (obs.left - start.x) / direction.x if direction.x != 0 else float('-inf'),
                (obs.top - start.y) / direction.y if direction.y != 0 else float('-inf')
            )
            t_far = pygame.Vector2(
                (obs.right - start.x) / direction.x if direction.x != 0 else float('inf'),
                (obs.bottom - start.y) / direction.y if direction.y != 0 else float('inf')
            )
            
            if t_near.x > t_far.x: t_near.x, t_far.x = t_far.x, t_near.x
            if t_near.y > t_far.y: t_near.y, t_far.y = t_far.y, t_near.y
            
            t_min = max(t_near.x, t_near.y)
            t_max = min(t_far.x, t_far.y)
            
            if t_min < t_max and 0 < t_min < max_distance and t_min < closest_t:
                closest_t = t_min
                collision_point = start + direction * t_min
                
                # Determine normal based on which side we hit
                if t_min == t_near.x:
                    normal = pygame.Vector2(-1, 0) if direction.x > 0 else pygame.Vector2(1, 0)
                else:
                    normal = pygame.Vector2(0, -1) if direction.y > 0 else pygame.Vector2(0, 1)
        
        return collision_point, normal

    def check_collision(self):
        for obs in static_obstacles:
            if obs.collidepoint(self.position):
                return True
        return False

    def record_collision(self):
        grid_x = int(self.position.x // GRID_SIZE)
        grid_y = int(self.position.y // GRID_SIZE)
        if 0 <= grid_x < len(collision_map[0]) and 0 <= grid_y < len(collision_map):
            # Add more memory strength for recent collisions
            time_factor = max(0.5, 2.0 - (time.time() - self.last_collision_time))
            collision_map[grid_y][grid_x] = min(10.0, collision_map[grid_y][grid_x] + 1.5 * time_factor)
            self.collision_count += 1
            self.last_collision_time = time.time()

    def check_avoidance_zone(self):
        grid_x = int(self.position.x // GRID_SIZE)
        grid_y = int(self.position.y // GRID_SIZE)
        if 0 <= grid_x < len(collision_map[0]) and 0 <= grid_y < len(collision_map):
            return collision_map[grid_y][grid_x]
        return 0

    def share_memory(self, bots):
        """Share collision memory with nearby bots"""
        grid_x = int(self.position.x // GRID_SIZE)
        grid_y = int(self.position.y // GRID_SIZE)
        
        if not (0 <= grid_x < len(collision_map[0]) and 0 <= grid_y < len(collision_map)):
            return
            
        my_value = collision_map[grid_y][grid_x]
        
        for bot in bots:
            if bot is self:
                continue
                
            dist = self.position.distance_to(bot.position)
            if dist < MEMORY_SHARING_DISTANCE:
                bot_grid_x = int(bot.position.x // GRID_SIZE)
                bot_grid_y = int(bot.position.y // GRID_SIZE)
                
                if 0 <= bot_grid_x < len(collision_map[0]) and 0 <= bot_grid_y < len(collision_map):
                    # Average the memory values
                    avg = (my_value + collision_map[bot_grid_y][bot_grid_x]) * 0.5
                    collision_map[grid_y][grid_x] = avg
                    collision_map[bot_grid_y][bot_grid_x] = avg

    def avoid_collision(self, obstacles):
        """More sophisticated collision avoidance using raycasting"""
        self.raycast_points = []
        avoidance_vectors = []
        weights = []
        
        # Cast rays in multiple directions
        for angle in range(0, 360, 45):
            ray_dir = pygame.Vector2(0, -1).rotate(angle)
            end_point = self.position + ray_dir * 100
            
            collision_point, normal = self.raycast(self.position, end_point, obstacles)
            self.raycast_points.append((self.position, end_point, collision_point))
            
            if collision_point:
                dist = self.position.distance_to(collision_point)
                strength = max(0, 1.0 - dist / 100)
                
                if normal:
                    # Move away from the collision normal
                    avoidance_vectors.append(normal)
                    weights.append(strength * 2.0)  # Higher weight for direct obstacles
                else:
                    # If no normal, move away from collision point
                    avoid_dir = (self.position - collision_point).normalize()
                    avoidance_vectors.append(avoid_dir)
                    weights.append(strength)
        
        # Also consider memory-based avoidance
        grid_x = int(self.position.x // GRID_SIZE)
        grid_y = int(self.position.y // GRID_SIZE)
        if 0 <= grid_x < len(collision_map[0]) and 0 <= grid_y < len(collision_map):
            memory_val = collision_map[grid_y][grid_x]
            if memory_val > 2:
                # Find the safest direction (away from danger grid center)
                danger_center = pygame.Vector2(
                    grid_x * GRID_SIZE + GRID_SIZE/2,
                    grid_y * GRID_SIZE + GRID_SIZE/2
                )
                avoid_dir = (self.position - danger_center).normalize()
                avoidance_vectors.append(avoid_dir)
                weights.append(min(1.0, memory_val / 5.0))
        
        # Combine avoidance vectors
        if avoidance_vectors:
            combined = pygame.Vector2(0, 0)
            total_weight = sum(weights)
            
            for vec, weight in zip(avoidance_vectors, weights):
                combined += vec * (weight / total_weight)
            
            combined.normalize_ip()
            self.avoidance_vector = combined
            self.avoidance_strength = min(1.0, sum(weights) / 5.0)
            
            # Set target heading away from obstacles
            avoidance_heading = math.degrees(math.atan2(-combined.y, combined.x))
            self.target_heading = avoidance_heading
        else:
            self.avoidance_vector = pygame.Vector2(0, 0)
            self.avoidance_strength = 0

    def navigate(self, light_sources, surface, obstacles):
        self.update_sensors()
        self.path.append((self.position.x, self.position.y))
        
        # Calculate light intensities
        current_left = sum(self.get_light_intensity(self.left_eye, light.location) for light in light_sources)
        current_right = sum(self.get_light_intensity(self.right_eye, light.location) for light in light_sources)
        
        # Update history
        self.left_history.append(current_left)
        self.right_history.append(current_right)
        
        # Calculate averages
        avg_left = sum(self.left_history) / len(self.left_history)
        avg_right = sum(self.right_history) / len(self.right_history)
        
        # Calculate deltas
        delta_left = current_left - avg_left
        delta_right = current_right - avg_right
        
        # Calculate wheel speeds based on light differences
        max_signal = 1.0
        left_wheel = max_signal - max(0, delta_right)
        right_wheel = max_signal - max(0, delta_left)
        
        self.left_wheel_speed = left_wheel
        self.right_wheel_speed = right_wheel
        
        # Calculate desired turn based on wheel difference
        turn_rate = (right_wheel - left_wheel) * 8.0
        turn_rate = max(-self.max_turn_rate, min(turn_rate, self.max_turn_rate))
        
        # Update target heading
        self.target_heading += turn_rate
        
        # Smooth heading transition
        heading_diff = (self.target_heading - self.heading) % 360
        if heading_diff > 180:
            heading_diff -= 360
            
        max_turn = self.max_turn_rate * 0.8
        actual_turn = max(-max_turn, min(heading_diff, max_turn))
        self.heading += actual_turn
        
        # Check avoidance zones and obstacles
        self.avoid_collision(obstacles)
        avoidance_value = self.check_avoidance_zone()
        
        # Apply avoidance if needed
        if self.avoidance_strength > 0:
            # Blend between light-following and avoidance
            speed_factor = max(0.1, 1.0 - self.avoidance_strength)
            turn_factor = 1.0 + self.avoidance_strength * 3.0
        else:
            speed_factor = 1.0
            turn_factor = 1.0
        
        # Calculate movement speed
        speed = max(0.1, (left_wheel + right_wheel) / 2) * speed_factor
        movement = pygame.Vector2(0, -1).rotate(self.heading) * speed * self.max_speed
        
        # Update velocity with acceleration
        self.velocity = self.velocity * 0.8 + movement * 0.2
        
        # Save previous position for collision recovery
        prev_pos = self.position.copy()
        self.position += self.velocity
        
        # Handle collisions
        if self.check_collision():
            self.record_collision()
            self.position = prev_pos
            
            # Bounce off obstacles
            self.velocity = self.velocity.reflect(self.avoidance_vector) * 0.7
            self.position += self.velocity
            
            # Turn away from collision
            self.target_heading += random.uniform(60, 120)
        
        # Boundary wrapping
        self.position.x = self.position.x % SCREEN_WIDTH
        self.position.y = self.position.y % SCREEN_HEIGHT
        
        # Return telemetry
        telemetry = [
            f"{self.name}",
            f"ΔL: {delta_left:.2f}, ΔR: {delta_right:.2f}",
            f"L: {current_left:.2f}, R: {current_right:.2f}",
            f"Wheels: {left_wheel:.2f}/{right_wheel:.2f}",
            f"Speed: {speed:.2f}, Avoid: {self.avoidance_strength:.2f}",
            f"Collisions: {self.collision_count}"
        ]
        
        return telemetry

    def render(self, surface):
        # Dynamic color based on fear level
        avoidance_value = self.check_avoidance_zone()
        fear_level = min(1.0, avoidance_value / 5.0)
        r = int(BOT_COLOR[0] * (1 - fear_level) + DANGER_COLOR[0] * fear_level)
        g = int(BOT_COLOR[1] * (1 - fear_level) + DANGER_COLOR[1] * fear_level)
        b = int(BOT_COLOR[2] * (1 - fear_level) + DANGER_COLOR[2] * fear_level)
        dynamic_color = (r, g, b)
        
        # Draw path
        if len(self.path) > 1:
            points = [(int(x), int(y)) for x, y in self.path]
            pygame.draw.lines(surface, PATH_COLOR, False, points, 2)
        
        # Draw raycasts
        for start, end, collision_point in self.raycast_points:
            color = (100, 255, 100, 150) if collision_point is None else (255, 100, 100, 200)
            pygame.draw.line(surface, color, start, end, 1)
            if collision_point:
                pygame.draw.circle(surface, (255, 50, 50), (int(collision_point.x), int(collision_point.y)), 4)
        
        # Draw avoidance vector
        if self.avoidance_strength > 0.1:
            end_pos = self.position + self.avoidance_vector * 30 * self.avoidance_strength
            pygame.draw.line(surface, (255, 150, 50), self.position, end_pos, 3)
            pygame.draw.circle(surface, (255, 150, 50), (int(end_pos.x), int(end_pos.y)), 5)
        
        # Body and sensors
        pygame.draw.circle(surface, dynamic_color, (int(self.position.x), int(self.position.y)), self.body_size)
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.left_eye.x), int(self.left_eye.y)), self.detector_size)
        pygame.draw.circle(surface, DETECTOR_COLOR, (int(self.right_eye.x), int(self.right_eye.y)), self.detector_size)
        
        # Direction indicator
        forward = pygame.Vector2(0, -1).rotate(self.heading)
        head_pos = self.position + forward * self.body_size
        pygame.draw.line(surface, (255, 255, 255), self.position, head_pos, 3)
        
        # Tag
        tag = font.render(self.name, True, LABEL_COLOR)
        tag_rect = tag.get_rect(center=(self.position.x, self.position.y - 25))
        surface.blit(tag, tag_rect)

# Light source
class GlowTarget:
    def __init__(self, location):
        self.location = pygame.Vector2(location)
        self.glow_size = 0
        self.glow_dir = 1

    def update(self):
        # Pulsating effect
        self.glow_size += self.glow_dir * 0.3
        if self.glow_size > 5 or self.glow_size < 0:
            self.glow_dir *= -1

    def render(self, surface):
        # Draw glow effect
        pygame.draw.circle(surface, (255, 255, 150, 100), 
                          (int(self.location.x), int(self.location.y)), 
                          25 + self.glow_size)
        pygame.draw.circle(surface, LIGHT_COLOR, 
                          (int(self.location.x), int(self.location.y)), 
                          15)

# Initialization
bots = [
    BraitenbergVehicle6((SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80), -135, "Bot 1", 0),
    BraitenbergVehicle6((100, 100), 45, "Bot 2", 1),
    BraitenbergVehicle6((400, 300), 0, "Bot 3", 2),
    BraitenbergVehicle6((SCREEN_WIDTH - 400, 100), 180, "Bot 4", 3)
]

light_sources = [
    GlowTarget((150, 150)),
    GlowTarget((650, 450)),
    GlowTarget((800, 200))
]

# Main Loop
clock = pygame.time.Clock()
running = True
last_time = time.time()
dirty_rects = []  # For optimized rendering

# Draw static elements once
background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
background.fill(BG_COLOR)
for obs in static_obstacles:
    pygame.draw.rect(background, OBSTACLE_COLOR, obs)
window.blit(background, (0, 0))
pygame.display.flip()

while running:
    current_time = time.time()
    dt = min(0.033, current_time - last_time)  # Cap at 30ms
    last_time = current_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:  # Reset memory
                collision_map = [[0 for _ in range(SCREEN_WIDTH // GRID_SIZE)] 
                                for _ in range(SCREEN_HEIGHT // GRID_SIZE)]
                memory_surface.fill((0, 0, 0, 0))
    
    # Update lights
    for light in light_sources:
        light.update()
    
    # Update collision memory decay
    for y in range(len(collision_map)):
        for x in range(len(collision_map[0])):
            collision_map[y][x] *= COLLISION_DECAY
    
    # Update memory visualization
    memory_surface.fill((0, 0, 0, 0))
    for y in range(len(collision_map)):
        for x in range(len(collision_map[0])):
            danger = collision_map[y][x]
            if danger > 0.1:
                alpha = min(200, int(danger * 25))
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(memory_surface, (255, 50, 50, alpha), rect)
    
    # Draw background and static elements
    window.blit(background, (0, 0))
    window.blit(memory_surface, (0, 0))
    
    # Draw lights
    for light in light_sources:
        light.render(window)
    
    # Update and render vehicles
    telemetry_data = []
    for bot in bots:
        telemetry = bot.navigate(light_sources, window, static_obstacles)
        telemetry_data.append(telemetry)
        bot.share_memory(bots)
        bot.render(window)
    
    # Draw UI
    pygame.draw.rect(window, (30, 30, 50, 200), (0, 0, SCREEN_WIDTH, 100))
    title = title_font.render("Enhanced Braitenberg Vehicle 6 - Memory-Based Navigation", True, LABEL_COLOR)
    window.blit(title, (20, 20))
    
    controls = font.render("R: Reset Memory | ESC: Quit", True, LABEL_COLOR)
    window.blit(controls, (20, 60))
    
    # Draw telemetry
    for i, telemetry in enumerate(telemetry_data):
        for j, line in enumerate(telemetry):
            x_pos = SCREEN_WIDTH - 220
            y_pos = 150 + j * 20 + i * 130
            debug = font.render(line, True, LABEL_COLOR)
            window.blit(debug, (x_pos, y_pos))
    
    # Draw memory info
    total_memory = sum(sum(row) for row in collision_map)
    memory_text = font.render(f"Memory Strength: {total_memory:.1f}", True, LABEL_COLOR)
    window.blit(memory_text, (SCREEN_WIDTH - 220, SCREEN_HEIGHT - 30))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()



