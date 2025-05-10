import pygame
import random
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.backends.backend_agg as agg

pygame.init()

# --- Konstanta
WIDTH, HEIGHT = 1000, 600
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
WINDOW_COLOR = (135, 206, 250)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulasi Sensor Kecepatan Multi-Mobil")

# Mobil
car_width, car_height = 60, 30
car_roof_height = 10
wheel_radius = 10
car_y = 250

# Sensor
sensor1_x = 300
sensor2_x = 600
distance_between_sensors_pixel = sensor2_x - sensor1_x

# Konversi
konversi_m_per_pixel = 5
batas_kecepatan_mps = 30
batas_kecepatan_pixels_ps = batas_kecepatan_mps * konversi_m_per_pixel

# Speed bump
speedbump_x = 750
speedbump_width = 40
speedbump_height = 0
speedbump_max_height = 1.5 * konversi_m_per_pixel
speedbump_raise = False

log_data = []
speeds = []

font = pygame.font.SysFont("Arial", 16)

class Car:
    def __init__(self, x, speed, color):
        self.x = x
        self.y = HEIGHT // 2 + 20
        self.speed = speed
        self.original_speed = speed
        self.color = color
        self.bounce = 0
        self.status = "Menunggu..."
        self.kecepatan_terukur = None
        self.sensor1_triggered = False
        self.sensor2_triggered = False
        self.waktu_tempuh = 0
        self.deselerasi = False

    def update(self, dt):
        self.x += self.speed * dt
        if self.deselerasi and self.speed > batas_kecepatan_pixels_ps:
            self.speed -= 30 * dt
            if self.speed < batas_kecepatan_pixels_ps:
                self.speed = batas_kecepatan_pixels_ps

    def draw(self):
        y_bottom = self.y - self.bounce
        pygame.draw.rect(screen, self.color, (self.x, y_bottom - car_height, car_width, car_height))
        pygame.draw.rect(screen, self.color, (self.x + 10, y_bottom - car_height - car_roof_height, car_width - 20, car_roof_height))
        window_y = y_bottom - car_height - car_roof_height + 2
        pygame.draw.rect(screen, WINDOW_COLOR, (self.x + 15, window_y, 15, 10))
        pygame.draw.rect(screen, WINDOW_COLOR, (self.x + car_width - 30, window_y, 15, 10))
        pygame.draw.circle(screen, BLACK, (int(self.x + 15), int(y_bottom)), wheel_radius)
        pygame.draw.circle(screen, BLACK, (int(self.x + 45), int(y_bottom)), wheel_radius)

    def check_sensors(self, dt):
        if not self.sensor1_triggered and self.x + car_width > sensor1_x:
            self.sensor1_triggered = True
            self.waktu_tempuh = 0
        if self.sensor1_triggered and not self.sensor2_triggered:
            self.waktu_tempuh += dt
        if self.sensor1_triggered and not self.sensor2_triggered and self.x + car_width > sensor2_x:
            self.sensor2_triggered = True
            self.kecepatan_terukur = distance_between_sensors_pixel / self.waktu_tempuh if self.waktu_tempuh > 0 else 0
            self.status = "Terlalu Cepat" if self.kecepatan_terukur > batas_kecepatan_pixels_ps else "Aman"
            self.deselerasi = self.kecepatan_terukur > batas_kecepatan_pixels_ps
            return self.kecepatan_terukur, self.status
        return None, None

    def check_bounce(self, dt):
        wheel_front_x = self.x + 45
        if speedbump_raise and (speedbump_x < wheel_front_x < speedbump_x + speedbump_width) and speedbump_height > 2:
            self.bounce = speedbump_height * 0.5
        elif self.bounce > 0:
            self.bounce -= 5 * dt
            if self.bounce < 0:
                self.bounce = 0

cars = []
start_x = 200
colors = [BLUE, ORANGE, GREEN, YELLOW, (160, 32, 240)]
for i in range(5):
    if i % 2 == 0:
        speed = random.uniform(batas_kecepatan_pixels_ps - 20, batas_kecepatan_pixels_ps)  # lambat
    else:
        speed = random.uniform(batas_kecepatan_pixels_ps + 20, batas_kecepatan_pixels_ps + 40)  # cepat
    cars.append(Car(start_x - i * 80, speed, colors[i % len(colors)]))  # mobil berdekatan

def draw_environment():
    screen.fill(WHITE)
    # Jalan
    pygame.draw.rect(screen, GREY, (0, car_y + 20, WIDTH, 100))

    # Sensor
    pygame.draw.line(screen, RED, (sensor1_x, car_y + 20), (sensor1_x, car_y + 120), 2)
    pygame.draw.line(screen, RED, (sensor2_x, car_y + 20), (sensor2_x, car_y + 120), 2)

    # Speed bump
    if speedbump_height > 0:
        pygame.draw.rect(screen, (200, 100, 0), (speedbump_x, HEIGHT // 2 + 50 - speedbump_height, speedbump_width, speedbump_height))
   
    # Kamera besar di bawah jalan (tengah bawah layar)
    camera_body_x = WIDTH // 2 - 30 + 200 
    camera_body_y = HEIGHT - 80
    pygame.draw.rect(screen, BLACK, (camera_body_x, camera_body_y, 60, 30))
    
    # Ubah warna lensa berdasarkan status speed bump
    lensa_color = RED if speedbump_raise else GREEN
    pygame.draw.circle(screen, lensa_color, (camera_body_x + 30, camera_body_y + 15), 8)
    pygame.draw.rect(screen, BLACK, (camera_body_x + 25, camera_body_y + 30, 10, 20))  # tiang
    pygame.draw.rect(screen, BLACK, (camera_body_x + 20, camera_body_y + 50, 20, 10))  # base
    screen.blit(font.render("Kamera", True, BLACK), (camera_body_x + 5, camera_body_y - 20))

def display_info(speed, status):
    if speed:
        speed_mps = speed / konversi_m_per_pixel
        color = RED if speed > batas_kecepatan_pixels_ps else GREEN
        screen.blit(font.render(f"Kecepatan: {speed_mps:.2f} km/h", True, color), (10, 10))
        screen.blit(font.render(f"Status: {status}", True, color), (10, 30))
        if status == "Aman" and speed > batas_kecepatan_pixels_ps:
            screen.blit(font.render("Mobil cepat lolos karena terlalu dekat dengan mobil lambat!", True, RED), (10.50))

def update_graph(data):
    hasil = list(map(lambda x: x / konversi_m_per_pixel, data))
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.plot(hasil, color="blue", label="Kecepatan")
    ax.axhline(y=batas_kecepatan_pixels_ps, color="red", linestyle="--", label="Batas")
    ax.set_ylim(20, 40)
    ax.set_title("Riwayat Kecepatan")
    ax.set_xlabel("Deteksi ke-")
    ax.set_ylabel("Kecepatan (km/h)")
    ax.legend()
    fig.tight_layout()
    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    raw_data = canvas.buffer_rgba()
    size = canvas.get_width_height()
    surf = pygame.image.frombuffer(raw_data, size, "RGBA")
    screen.blit(surf, (10, HEIGHT - 170))
    plt.close(fig)

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(10) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_environment()
    speedbump_raise = False

    for car in cars:
        car.update(dt)
        speed, status = car.check_sensors(dt)
        if speed:
            log_data.append([speed, status])
            speeds.append(speed)
        if car.kecepatan_terukur and car.kecepatan_terukur > batas_kecepatan_pixels_ps:
            speedbump_raise = True
        car.check_bounce(dt)
        car.draw()
        display_info(speed, status)

    if speedbump_raise and speedbump_height < speedbump_max_height:
        speedbump_height += 1000 * dt
        if speedbump_height > speedbump_max_height:
            speedbump_height = speedbump_max_height
    elif not speedbump_raise and speedbump_height > 0:
        speedbump_height -= 1000 * dt
        if speedbump_height < 0:
            speedbump_height = 0

    display_info(None, "Multi-mobil aktif")
    update_graph(speeds)
    pygame.display.flip()

    for car in cars:
        if car.x > WIDTH:
            car.x = -random.randint(100, 500)
            car.speed = random.uniform(batas_kecepatan_pixels_ps - 20, batas_kecepatan_pixels_ps + 40)
            car.sensor1_triggered = False
            car.sensor2_triggered = False
            car.kecepatan_terukur = None
            car.status = "Menunggu..."
            car.waktu_tempuh = 0
            car.deselerasi = False

pygame.quit()