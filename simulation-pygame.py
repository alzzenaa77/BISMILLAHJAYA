# Import packages
import pygame
import time
import random
import csv
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg
import numpy as np

# Inisialisasi Pygame
pygame.init()
WIDTH, HEIGHT = 1000, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulasi Smart Speed Bump berbasis AI dan IOT")

# Warna
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLUE = (0, 120, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 140, 0)
RED = (255, 50, 50)
GREEN = (0, 200, 0)
WINDOW_COLOR = (135, 206, 250)
YELLOW = (255, 255, 0)

# Font
font = pygame.font.SysFont("Arial", 20)

# Konversi
konversi_m_per_pixel = 5
batas_kecepatan_mps = 30
batas_kecepatan_pixels_ps = batas_kecepatan_mps * konversi_m_per_pixel

# Parameter mobil
car_x = 0
car_speed = random.uniform(batas_kecepatan_pixels_ps-20, batas_kecepatan_pixels_ps)
car_width = 60
car_height = 30
car_roof_height = 15
wheel_radius = 10
car_y = HEIGHT // 2 + 20
car_bounce = 0
deselerasi_aktif = False

# Sensor & Speedbump
sensor1_x = 200
sensor2_x = 400
speedbump_x = sensor2_x + 300
distance_between_sensors_pixel = sensor2_x - sensor1_x

# Perwaktuan duniawi
sensor1_terpicu = False
sensor2_terpicu = False
waktu_tempuh_simulasi = 0

# Speed bump
speedbump_height = 0
speedbump_raise = False
speedbump_max_height = 30
speedbump_width = 60

# Logging
kecepatan_terukur = None
status = ""
log_data = []

# Grafik setup
fig, ax = plt.subplots(figsize=(4, 2))
speeds = []
frame = agg.FigureCanvasAgg(fig)

# Clock
clock = pygame.time.Clock()
running = True
simulasi_count = 0

# Fungsi menggambar
def draw_environment():
    screen.fill(WHITE)
    pygame.draw.rect(screen, GRAY, (0, HEIGHT // 2, WIDTH, 100))

    # Corak garis jalan
    for x in range(0, WIDTH, 40):
        pygame.draw.rect(screen, WHITE, (x, HEIGHT // 2 + 50 - 2, 20, 4))

    # Sensor
    pygame.draw.circle(screen, BLACK, (sensor1_x, HEIGHT // 2 + 50), 10)
    pygame.draw.circle(screen, BLACK, (sensor2_x, HEIGHT // 2 + 50), 10)
    screen.blit(font.render("Sensor 1", True, BLACK), (sensor1_x - 30, HEIGHT // 2 + 70))
    screen.blit(font.render("Sensor 2", True, BLACK), (sensor2_x - 30, HEIGHT // 2 + 70))

    # Speed bump
    bump_color = RED if speedbump_raise else ORANGE
    pygame.draw.rect(screen, bump_color, (speedbump_x, HEIGHT // 2 + 50 - speedbump_height, speedbump_width, speedbump_height))

    # Kamera besar di bawah jalan (tengah bawah layar)
    camera_body_x = WIDTH // 2 - 30 + 200 # Sesuaikan posisi X kamera di sini
    camera_body_y = HEIGHT - 80
    pygame.draw.rect(screen, BLACK, (camera_body_x, camera_body_y, 60, 30))  # body

    # Ubah warna lensa berdasarkan status speed bump
    lensa_color = RED if speedbump_raise else GREEN
    pygame.draw.circle(screen, lensa_color, (camera_body_x + 30, camera_body_y + 15), 8)  # lensa

    pygame.draw.rect(screen, BLACK, (camera_body_x + 25, camera_body_y + 30, 10, 20))  # tiang
    pygame.draw.rect(screen, BLACK, (camera_body_x + 20, camera_body_y + 50, 20, 10))  # base
    screen.blit(font.render("Kamera", True, BLACK), (camera_body_x + 5, camera_body_y - 20))

def draw_car(x, bounce):
    y_bottom = car_y - bounce
    pygame.draw.rect(screen, BLUE, (x, y_bottom - car_height, car_width, car_height))
    pygame.draw.rect(screen, BLUE, (x + 10, y_bottom - car_height - car_roof_height, car_width - 20, car_roof_height))
    window_y = y_bottom - car_height - car_roof_height + 2
    pygame.draw.rect(screen, WINDOW_COLOR, (x + 15, window_y, 15, 10))
    pygame.draw.rect(screen, WINDOW_COLOR, (x + car_width - 30, window_y, 15, 10))
    pygame.draw.circle(screen, BLACK, (int(x + 15), int(y_bottom)), wheel_radius)
    pygame.draw.circle(screen, BLACK, (int(x + 45), int(y_bottom)), wheel_radius)

def display_info(speed, status):
    screen.blit(font.render(f"Batas kecepatan: {batas_kecepatan_mps} km/h", True, BLACK), (10, 60))
    if speed is not None:
        color = RED if speed > batas_kecepatan_pixels_ps else GREEN
        speed_mps = speed / konversi_m_per_pixel
        screen.blit(font.render(f"Kecepatan: {speed_mps:.2f} km/h", True, color), (10, 10))
        screen.blit(font.render(f"Status: {status}", True, color), (10, 35))
    else:
        screen.blit(font.render("Kecepatan: Menunggu...", True, BLACK), (10, 10))
        screen.blit(font.render("Status: Menunggu...", True, BLACK), (10, 35))

def update_graph(speeds):
    ax.clear()
    ax.plot([s / konversi_m_per_pixel for s in speeds], color="blue")
    ax.set_title("Grafik Kecepatan (km/h)")
    ax.set_ylim(0, max([s / konversi_m_per_pixel for s in speeds] + [100]) + 10)
    frame.draw()
    raw_data = frame.buffer_rgba()
    size = frame.get_width_height()
    graph_surf = pygame.image.frombuffer(raw_data, size, "RGBA")
    screen.blit(graph_surf, (WIDTH - 400, 20))

# Simulasi utama
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Mobil bergerak
    car_x += car_speed * dt

    # Deselerasi otomatis jika kecepatan melebihi batas
    if deselerasi_aktif and car_speed > batas_kecepatan_pixels_ps:
        car_speed -= 30 * dt  # deselerasi 5 pixel -> 1 meter per detik
        if car_speed < batas_kecepatan_pixels_ps:
            car_speed = batas_kecepatan_pixels_ps

    # Perhitungan kecepatan
    if sensor1_terpicu is False and car_x + car_width > sensor1_x:
        sensor1_terpicu = True
        waktu_tempuh_simulasi = 0

    # Selama mobil berada di antara sensor 1 dan 2, hitung waktu simulasi
    if sensor1_terpicu and not sensor2_terpicu:
        waktu_tempuh_simulasi += dt

    if sensor1_terpicu and sensor2_terpicu is False and car_x + car_width > sensor2_x:
        sensor2_terpicu = True
        kecepatan_terukur = distance_between_sensors_pixel / waktu_tempuh_simulasi if waktu_tempuh_simulasi > 0 else 0

        # Keputusan saat kecepatan terbaca
        if kecepatan_terukur > batas_kecepatan_pixels_ps:
            speedbump_raise = True
            status = "Terlalu Cepat"
            deselerasi_aktif = True
        else:
            speedbump_raise = False
            status = "Aman"
            deselerasi_aktif = False
        log_data.append([kecepatan_terukur, status])
        speeds.append(kecepatan_terukur)

    # Update speed bump height
    if speedbump_raise and speedbump_height < speedbump_max_height:
        speedbump_height += 30 * dt
        if speedbump_height > speedbump_max_height:
            speedbump_height = speedbump_max_height
    elif not speedbump_raise and speedbump_height > 0:
        speedbump_height -= 30 * dt
        if speedbump_height < 0:
            speedbump_height = 0

    # Car bounce
    wheel_front_x = car_x + 45
    if speedbump_raise and (speedbump_x < wheel_front_x < speedbump_x + speedbump_width) and speedbump_height > 2:
        car_bounce = speedbump_height * 0.5
    else:
        if car_bounce > 0:
            car_bounce -= 5 * dt
            if car_bounce < 0:
                car_bounce = 0

    draw_environment()
    draw_car(car_x, car_bounce)
    display_info(kecepatan_terukur, status)
    update_graph(speeds)
    pygame.display.flip()

    # Reset mobil
    if car_x > WIDTH:
        time.sleep(1)
        car_x = -car_width
        simulasi_count += 1

        if simulasi_count % 2 == 1:
            car_speed = random.uniform(batas_kecepatan_pixels_ps-20, batas_kecepatan_pixels_ps)
        else:
            car_speed = random.uniform(batas_kecepatan_pixels_ps+20, batas_kecepatan_pixels_ps+40)
        
        deselerasi_aktif = False
        sensor1_terpicu = False
        sensor2_terpicu = False
        waktu_tempuh_simulasi = 0
        kecepatan_terukur = None
        status = ""
        speedbump_raise = False

# Simpan ke CSV
with open("log_kecepatan.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Kecepatan (pixel/s)", "Status"])
    writer.writerows(log_data)

pygame.quit()