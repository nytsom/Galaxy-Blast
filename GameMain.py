import math
import os
import random
import pygame

#=========================================================
#Initialize pygame
#=========================================================
pygame.init()

try:
    pygame.mixer.init()
    AUDIO_ENABLED = True
except pygame.error:
    AUDIO_ENABLED = False

# =========================================================
# WINDOW / TIMING
# =========================================================
WIDTH, HEIGHT = 1280, 720
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galaxy Blast")
clock = pygame.time.Clock()

# =========================================================
# FONTS
# =========================================================
font_big = pygame.font.Font(None, 72)
font_med = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 26)
font_tiny = pygame.font.Font(None, 20)

# =========================================================
# COLORS
# =========================================================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
DARK_RED = (120, 20, 20)
GREEN = (60, 220, 120)
DARK_GREEN = (20, 120, 60)
ENEMY_GREEN_OUTER = (10, 90, 35)
ENEMY_GREEN_INNER = (5, 55, 20)
BLUE = (80, 160, 255)
YELLOW = (255, 220, 80)
ORANGE = (255, 140, 50)
CYAN = (100, 240, 255)
GRAY = (180, 180, 180)
PANEL = (25, 25, 40)
PANEL2 = (40, 40, 60)

# =========================================================
# GAME CONSTANTS
# =========================================================
PLAYER_RADIUS = 18
PLAYER_ACCELERATION = 0.45
PLAYER_MAX_SPEED = 7.0
PLAYER_FRICTION = 0.94

BULLET_RADIUS = 5
BULLET_SPEED = 12
SHOOT_DELAY = 8

ENEMY_RADIUS = 16
ENEMY_DAMAGE = 10
NORMAL_ENEMY_HP = 1
RED_ENEMY_HP = 5

HEALTH_PICKUP_RADIUS = 10
HEALTH_PICKUP_HEAL = 25
HEALTH_PICKUP_CHANCE = 0.25

NORMAL_START_AMMO = 10
NORMAL_MAX_AMMO = 100
NORMAL_SPAWN_INTERVAL = 75
NORMAL_MAX_HEALTH = 100

MASTER_START_AMMO = 1
MASTER_MAX_AMMO = 2
MASTER_SPAWN_INTERVAL = 60
MASTER_MAX_HEALTH = 1

DAMAGE_FLASH_DURATION = 10

WINDOW_SIZES = [
    (960, 540),
    (1280, 720),
    (1600, 900),
    (1920, 1080),
    (2540, 1440),
]

# =========================================================
# RUNTIME STATE
# =========================================================
circle_x = WIDTH // 2
circle_y = HEIGHT // 2
circle_radius = PLAYER_RADIUS

player_acceleration = PLAYER_ACCELERATION
max_player_speed = PLAYER_MAX_SPEED
friction = PLAYER_FRICTION
player_vx = 0.0
player_vy = 0.0

health = NORMAL_MAX_HEALTH
max_health = NORMAL_MAX_HEALTH

bullets = []
bullet_radius = BULLET_RADIUS
bullet_speed = BULLET_SPEED
ammo = NORMAL_START_AMMO
max_ammo = NORMAL_MAX_AMMO
shoot_direction = 1
shoot_cooldown = 0
shoot_delay = SHOOT_DELAY

enemies = []
enemy_radius = ENEMY_RADIUS
enemy_spawn_timer = 0
spawn_interval = NORMAL_SPAWN_INTERVAL
enemy_damage = ENEMY_DAMAGE

health_pickups = []
pickup_spawn_chance = HEALTH_PICKUP_CHANCE

particles = []
damage_flash_timer = 0
damage_flash_duration = DAMAGE_FLASH_DURATION

kill_count = 0
wave = 1
difficulty_increment = 0

game_paused = False
game_over = False
settings_open = False
running = True
game_over_sound_played = False
sound_enabled = True

master_mode = False

current_window_size_index = 1  # starts at 1280x720

# =========================================================
# AUDIO
# =========================================================
music_path = "background_music.mp3"


def load_sound(filename, volume=0.5):
    if not AUDIO_ENABLED:
        return None
    try:
        if os.path.exists(filename):
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(volume)
            return sound
    except pygame.error:
        return None
    return None


def play_sound(sound):
    if AUDIO_ENABLED and sound_enabled and sound is not None:
        sound.play()


def update_music_state():
    if not AUDIO_ENABLED:
        return

    try:
        if sound_enabled:
            if os.path.exists(music_path):
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(0.3)
                    pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.pause()
    except pygame.error:
        pass


shoot_sound = load_sound("shoot.mp3", 0.35)
hit_sound = load_sound("hit.mp3", 0.4)
kill_sound = load_sound("kill.mp3", 0.5)
pickup_sound = load_sound("pickup.mp3", 0.5)
game_over_sound = load_sound("game_over.mp3", 0.7)
quack_sound = load_sound("quack.mp3", 0.8)

if AUDIO_ENABLED and os.path.exists(music_path):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass

update_music_state()

# =========================================================
# GENERAL HELPERS
# =========================================================
def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)


def rebuild_ui_rects():
    global settings_button, close_button, master_mode_button, sound_button, window_size_button, setting_controls

    settings_button = pygame.Rect(WIDTH - 125, 8, 110, 34)
    close_button = pygame.Rect(WIDTH // 2 + 165, 120, 100, 38)
    master_mode_button = pygame.Rect(WIDTH // 2 - 245, 170, 490, 40)
    sound_button = pygame.Rect(WIDTH // 2 - 245, 215, 490, 40)
    window_size_button = pygame.Rect(WIDTH // 2 - 245, 260, 490, 40)


    setting_controls = {
        "Max Speed": {
            "value_ref": "max_player_speed",
            "min": 3.0,
            "max": 12.0,
            "step": 0.5,
            "minus": pygame.Rect(WIDTH // 2 + 90, 330, 35, 35),
            "plus": pygame.Rect(WIDTH // 2 + 235, 330, 35, 35),
        },
        "Acceleration": {
            "value_ref": "player_acceleration",
            "min": 0.10,
            "max": 1.20,
            "step": 0.05,
            "minus": pygame.Rect(WIDTH // 2 + 90, 370, 35, 35),
            "plus": pygame.Rect(WIDTH // 2 + 235, 370, 35, 35),
        },
        "Friction": {
            "value_ref": "friction",
            "min": 0.80,
            "max": 0.99,
            "step": 0.01,
            "minus": pygame.Rect(WIDTH // 2 + 90, 410, 35, 35),
            "plus": pygame.Rect(WIDTH // 2 + 235, 410, 35, 35),
        },
        "Bullet Speed": {
            "value_ref": "bullet_speed",
            "min": 6,
            "max": 25,
            "step": 1,
            "minus": pygame.Rect(WIDTH // 2 + 90, 450, 35, 35),
            "plus": pygame.Rect(WIDTH // 2 + 235, 450, 35, 35),
        },
        "Enemy Damage": {
            "value_ref": "enemy_damage",
            "min": 1,
            "max": 30,
            "step": 1,
            "minus": pygame.Rect(WIDTH // 2 + 90, 490, 35, 35),
            "plus": pygame.Rect(WIDTH // 2 + 235, 490, 35, 35),
        },
        "Shoot Delay": {
            "value_ref": "shoot_delay",
            "min": 2,
            "max": 20,
            "step": 1,
            "minus": pygame.Rect(WIDTH // 2 + 90, 530, 35, 35),
            "plus": pygame.Rect(WIDTH // 2 + 235, 530, 35, 35),
        },
    }


def apply_window_size(size_index):
    global WIDTH, HEIGHT, screen, circle_x, circle_y, current_window_size_index

    current_window_size_index = size_index
    WIDTH, HEIGHT = WINDOW_SIZES[current_window_size_index]
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    circle_x = clamp(circle_x, circle_radius, WIDTH - circle_radius)
    circle_y = clamp(circle_y, circle_radius + 50, HEIGHT - circle_radius)

    rebuild_ui_rects()


rebuild_ui_rects()

# =========================================================
# GAME MODE / SETTINGS
# =========================================================
def apply_mode_settings(reset_ammo=False):
    global ammo, max_ammo, spawn_interval, health, max_health

    if master_mode:
        max_ammo = MASTER_MAX_AMMO
        spawn_interval = MASTER_SPAWN_INTERVAL
        max_health = MASTER_MAX_HEALTH
        if reset_ammo:
            ammo = MASTER_START_AMMO
            health = max_health
        else:
            ammo = min(ammo, max_ammo)
            health = min(health, max_health)
    else:
        max_ammo = NORMAL_MAX_AMMO
        spawn_interval = NORMAL_SPAWN_INTERVAL
        max_health = NORMAL_MAX_HEALTH
        if reset_ammo:
            ammo = NORMAL_START_AMMO
            health = max_health
        else:
            ammo = min(ammo, max_ammo)
            health = min(health, max_health)


def get_setting_value(name):
    return globals()[setting_controls[name]["value_ref"]]


def change_setting(name, direction):
    ref = setting_controls[name]["value_ref"]
    step = setting_controls[name]["step"]
    min_val = setting_controls[name]["min"]
    max_val = setting_controls[name]["max"]

    value = globals()[ref]
    value += step * direction
    value = max(min_val, min(max_val, value))

    if isinstance(step, float):
        value = round(value, 2)

    globals()[ref] = value


def format_setting_value(name, value):
    if name in ("Acceleration", "Friction", "Max Speed"):
        return f"{value:.2f}"
    return str(value)


# =========================================================
# DRAW HELPERS
# =========================================================
def draw_text(text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)


def draw_button(rect, text, bg, fg=WHITE):
    pygame.draw.rect(screen, bg, rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
    draw_text(text, font_small, fg, rect.centerx, rect.centery, center=True)


def draw_glow_circle(surface, color, pos, radius, glow_radius=16):
    for i in range(3, 0, -1):
        glow_surf = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
        alpha = 25 * i
        pygame.draw.circle(
            glow_surf,
            (*color, alpha),
            (glow_surf.get_width() // 2, glow_surf.get_height() // 2),
            radius + glow_radius * i // 2,
        )
        surface.blit(
            glow_surf,
            (pos[0] - glow_surf.get_width() // 2, pos[1] - glow_surf.get_height() // 2),
        )
    pygame.draw.circle(surface, color, pos, radius)


def draw_background():
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(10 + 20 * t)
        g = int(10 + 25 * t)
        b = int(25 + 55 * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    random.seed(7)
    for _ in range(45):
        star_x = random.randint(0, WIDTH)
        star_y = random.randint(40, HEIGHT)
        pygame.draw.circle(screen, WHITE, (star_x, star_y), 1)
    random.seed()


def draw_particles():
    for p in particles:
        alpha = clamp(p["life"] * 8, 0, 255)
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*p["color"], alpha), (10, 10), int(p["size"]))
        screen.blit(surf, (p["x"] - 10, p["y"] - 10))


def draw_settings_menu():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(WIDTH // 2 - 290, 90, 580, 520)
    pygame.draw.rect(screen, PANEL, panel_rect, border_radius=18)
    pygame.draw.rect(screen, WHITE, panel_rect, 2, border_radius=18)

    draw_text("Settings", font_big, CYAN, WIDTH // 2, 130, center=True)
    draw_button(close_button, "Close", PANEL2)

    mode_color = DARK_RED if master_mode else PANEL2
    mode_text = "Master Mode: ON" if master_mode else "Master Mode: OFF"
    draw_button(master_mode_button, mode_text, mode_color)

    sound_color = DARK_GREEN if sound_enabled else DARK_RED
    sound_text = "Sound: ON" if sound_enabled else "Sound: OFF"
    draw_button(sound_button, sound_text, sound_color)

    window_text = f"Window Size: {WIDTH}x{HEIGHT}"
    draw_button(window_size_button, window_text, PANEL2)

    y_positions = {
        "Max Speed": 335,
        "Acceleration": 375,
        "Friction": 415,
        "Bullet Speed": 455,
        "Enemy Damage": 495,
        "Shoot Delay": 535,
    }

    for name, y in y_positions.items():
        value = get_setting_value(name)
        draw_text(
            name,
            font_small,
            WHITE,
            WIDTH // 2 - 210,
            y,
        )
        draw_text(
            format_setting_value(name, value),
            font_small,
            YELLOW,
            WIDTH // 2 + 165,
            y,
            center=True,
        )
        draw_button(setting_controls[name]["minus"], "-", DARK_RED)
        draw_button(setting_controls[name]["plus"], "+", DARK_GREEN)

    info_font = pygame.font.Font(None, 22)
    info_text = f"Mode ammo: {ammo}/{max_ammo}    Spawn: {spawn_interval} frames    Max HP: {max_health}"
    draw_text(info_text, info_font, GRAY, WIDTH // 2, 585, center=True)


def draw_hud():
    panel = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
    panel.fill((20, 20, 30, 180))
    screen.blit(panel, (0, 0))
    pygame.draw.line(screen, (80, 80, 100), (0, 50), (WIDTH, 50), 2)

    ammo_color = (255, 120, 120) if ammo <= 1 else WHITE if ammo > 4 else (255, 180, 120)
    draw_text(f"Ammo: {ammo}/{max_ammo}", font_med, ammo_color, 16, 11)
    draw_text(f"Score: {kill_count}", font_med, WHITE, WIDTH // 2, 25, center=True)
    draw_text(f"Wave {wave}", font_med, CYAN, WIDTH - 250, 11)

    if master_mode:
        draw_text("MASTER", font_small, RED, WIDTH - 360, 14)

    draw_button(settings_button, "Settings", PANEL2)

    bar_x, bar_y = 18, HEIGHT - 34
    bar_w, bar_h = 210, 22
    pygame.draw.rect(screen, (50, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=8)

    health_ratio = max(0, health / max_health)
    health_w = int(bar_w * health_ratio)
    pygame.draw.rect(screen, (50, 220, 90), (bar_x, bar_y, health_w, bar_h), border_radius=8)
    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=8)
    draw_text(f"HP {health}", font_small, WHITE, bar_x + bar_w + 14, HEIGHT - 36)

    ammo_bar_x, ammo_bar_y = WIDTH - 190, HEIGHT - 34
    ammo_bar_w, ammo_bar_h = 160, 18
    pygame.draw.rect(screen, (50, 50, 60), (ammo_bar_x, ammo_bar_y, ammo_bar_w, ammo_bar_h), border_radius=8)
    ammo_ratio = max(0, min(1, ammo / max_ammo))
    pygame.draw.rect(
        screen,
        YELLOW,
        (ammo_bar_x, ammo_bar_y, int(ammo_bar_w * ammo_ratio), ammo_bar_h),
        border_radius=8,
    )
    pygame.draw.rect(screen, WHITE, (ammo_bar_x, ammo_bar_y, ammo_bar_w, ammo_bar_h), 2, border_radius=8)

    draw_text("P = Pause   ESC = Quit", font_tiny, GRAY, WIDTH - 180, HEIGHT - 56)


def draw_pickups():
    for pickup in health_pickups:
        px, py = int(pickup["x"]), int(pickup["y"])
        draw_glow_circle(screen, CYAN, (px, py), 10, 12)

        diamond_points = [
            (px, py - 10),
            (px + 10, py),
            (px, py + 10),
            (px - 10, py),
        ]
        pygame.draw.polygon(screen, (80, 255, 220), diamond_points)
        pygame.draw.polygon(screen, WHITE, diamond_points, 2)

        pygame.draw.rect(screen, WHITE, (px - 2, py - 6, 4, 12), border_radius=2)
        pygame.draw.rect(screen, WHITE, (px - 6, py - 2, 12, 4), border_radius=2)


def draw_enemies():
    for enemy in enemies:
        ex, ey = int(enemy["x"]), int(enemy["y"])
        if enemy["type"] == "red":
            draw_glow_circle(screen, RED, (ex, ey), enemy_radius, 12)
            draw_text(str(enemy["hp"]), font_tiny, WHITE, ex - 5, ey - 8)
        else:
            draw_glow_circle(screen, ENEMY_GREEN_OUTER, (ex, ey), enemy_radius, 8)
            pygame.draw.circle(screen, ENEMY_GREEN_INNER, (ex, ey), enemy_radius - 4)


def draw_bullets():
    for bullet in bullets:
        draw_glow_circle(screen, YELLOW, (int(bullet["x"]), int(bullet["y"])), bullet_radius, 8)


def draw_player():
    pygame.draw.circle(screen, BLACK, (int(circle_x) + 4, int(circle_y) + 6), circle_radius + 2)
    draw_glow_circle(screen, CYAN, (int(circle_x), int(circle_y)), circle_radius, 14)
    pygame.draw.circle(screen, WHITE, (int(circle_x), int(circle_y)), circle_radius - 6)


# =========================================================
# PARTICLES
# =========================================================
def spawn_particles(x, y, color, count, speed_range=(1, 4), size_range=(2, 5)):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(*speed_range)
        particles.append({
            "x": x,
            "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(18, 35),
            "size": random.randint(*size_range),
            "color": color,
        })


def update_particles():
    remove_list = []
    for i, p in enumerate(particles):
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        p["size"] = max(1, p["size"] - 0.03)
        p["vx"] *= 0.97
        p["vy"] *= 0.97
        if p["life"] <= 0:
            remove_list.append(i)

    for i in reversed(remove_list):
        particles.pop(i)


# =========================================================
# GAME HELPERS
# =========================================================
def reset_game():
    global circle_x, circle_y, health, kill_count, wave, ammo
    global difficulty_increment, enemy_spawn_timer, game_over
    global damage_flash_timer, shoot_direction, shoot_cooldown
    global player_vx, player_vy, game_over_sound_played, max_health

    circle_x = WIDTH // 2
    circle_y = HEIGHT // 2
    player_vx = 0.0
    player_vy = 0.0
    max_health = MASTER_MAX_HEALTH if master_mode else NORMAL_MAX_HEALTH
    health = max_health

    enemies.clear()
    bullets.clear()
    health_pickups.clear()
    particles.clear()

    kill_count = 0
    wave = 1
    difficulty_increment = 0
    enemy_spawn_timer = 0
    damage_flash_timer = 0
    shoot_direction = 1
    shoot_cooldown = 0
    game_over = False
    game_over_sound_played = False

    apply_mode_settings(reset_ammo=True)


def spawn_red_enemy():
    enemies.append({
        "x": random.randint(60, WIDTH - 60),
        "y": random.randint(90, HEIGHT - 60),
        "vx": random.choice([-2, -1, 1, 2]),
        "vy": random.choice([-2, -1, 1, 2]),
        "type": "red",
        "hp": RED_ENEMY_HP,
    })


def spawn_normal_enemy():
    enemies.append({
        "x": random.randint(60, WIDTH - 60),
        "y": random.randint(90, HEIGHT - 60),
        "vx": random.choice([-2, -1, 1, 2]),
        "vy": random.choice([-2, -1, 1, 2]),
        "type": "normal",
        "hp": NORMAL_ENEMY_HP,
    })


def handle_player_movement():
    global circle_x, circle_y, player_vx, player_vy, shoot_direction

    keys = pygame.key.get_pressed()

    if keys[pygame.K_w]:
        player_vy -= player_acceleration
    if keys[pygame.K_s]:
        player_vy += player_acceleration
    if keys[pygame.K_a]:
        player_vx -= player_acceleration
        shoot_direction = -1
    if keys[pygame.K_d]:
        player_vx += player_acceleration
        shoot_direction = 1

    player_vx *= friction
    player_vy *= friction

    player_vx = clamp(player_vx, -max_player_speed, max_player_speed)
    player_vy = clamp(player_vy, -max_player_speed, max_player_speed)

    circle_x += player_vx
    circle_y += player_vy

    if circle_x < circle_radius:
        circle_x = circle_radius
        player_vx = 0
    elif circle_x > WIDTH - circle_radius:
        circle_x = WIDTH - circle_radius
        player_vx = 0

    if circle_y < circle_radius + 50:
        circle_y = circle_radius + 50
        player_vy = 0
    elif circle_y > HEIGHT - circle_radius:
        circle_y = HEIGHT - circle_radius
        player_vy = 0

    return keys


def handle_shooting(keys):
    global ammo, shoot_cooldown

    if keys[pygame.K_SPACE] and shoot_cooldown <= 0 and ammo > 0:
        bullets.append({
            "x": circle_x,
            "y": circle_y,
            "vx": bullet_speed * shoot_direction,
            "vy": 0,
        })
        ammo -= 1
        shoot_cooldown = shoot_delay
        spawn_particles(circle_x, circle_y, YELLOW, 5, (1, 2), (2, 3))
        play_sound(shoot_sound)

    if shoot_cooldown > 0:
        shoot_cooldown -= 1


def handle_bullet_collisions():
    global kill_count, ammo, wave, difficulty_increment

    bullets_to_remove = []
    enemies_to_remove = []
    special_spawn = False

    for i, bullet in enumerate(bullets):
        bullet["x"] += bullet["vx"]
        bullet["y"] += bullet["vy"]

        if bullet["x"] < -20 or bullet["x"] > WIDTH + 20:
            bullets_to_remove.append(i)
            continue

        for j, enemy in enumerate(enemies):
            if distance(bullet["x"], bullet["y"], enemy["x"], enemy["y"]) < bullet_radius + enemy_radius:
                bullets_to_remove.append(i)
                spawn_particles(bullet["x"], bullet["y"], ORANGE, 8)

                enemy["hp"] -= 1
                if enemy["hp"] <= 0:
                    enemies_to_remove.append(j)
                    kill_count += 1
                    ammo = min(max_ammo, ammo + 3)
                    play_sound(kill_sound)

                    if kill_count % 10 == 0:
                        special_spawn = True

                    wave = (kill_count // 5) + 1
                    difficulty_increment = (kill_count // 10) * 5

                    spawn_particles(
                        enemy["x"],
                        enemy["y"],
                        RED if enemy["type"] == "red" else ENEMY_GREEN_OUTER,
                        18,
                        (1, 5),
                        (2, 5),
                    )

                    if random.random() < pickup_spawn_chance:
                        health_pickups.append({"x": enemy["x"], "y": enemy["y"]})
                break

    for i in reversed(sorted(set(bullets_to_remove))):
        if 0 <= i < len(bullets):
            bullets.pop(i)

    for i in reversed(sorted(set(enemies_to_remove))):
        if 0 <= i < len(enemies):
            enemies.pop(i)

    return special_spawn


def handle_enemy_spawning(special_spawn):
    global enemy_spawn_timer

    enemy_spawn_timer += 1
    current_spawn_interval = max(22, spawn_interval - difficulty_increment)

    if special_spawn:
        spawn_red_enemy()

    if enemy_spawn_timer >= current_spawn_interval:
        enemy_spawn_timer = 0
        spawn_normal_enemy()


def update_enemies():
    for enemy in enemies:
        enemy["x"] += enemy["vx"]
        enemy["y"] += enemy["vy"]

        if enemy["x"] < enemy_radius or enemy["x"] > WIDTH - enemy_radius:
            enemy["vx"] *= -1
        if enemy["y"] < enemy_radius + 55 or enemy["y"] > HEIGHT - enemy_radius:
            enemy["vy"] *= -1

        enemy["x"] = clamp(enemy["x"], enemy_radius, WIDTH - enemy_radius)
        enemy["y"] = clamp(enemy["y"], enemy_radius + 55, HEIGHT - enemy_radius)


def handle_player_enemy_collisions():
    global health, game_over, damage_flash_timer

    enemies_to_remove = []

    for i, enemy in enumerate(enemies):
        if distance(circle_x, circle_y, enemy["x"], enemy["y"]) < circle_radius + enemy_radius:
            damage_flash_timer = damage_flash_duration
            spawn_particles(circle_x, circle_y, RED, 16, (1, 5), (2, 5))
            play_sound(hit_sound)

            if enemy["type"] == "red":
                health = 0
                game_over = True
                break
            else:
                health -= enemy_damage
                enemies_to_remove.append(i)

    for i in reversed(sorted(set(enemies_to_remove))):
        if 0 <= i < len(enemies):
            enemies.pop(i)


def handle_pickups():
    global health

    pickups_to_remove = []

    for i, pickup in enumerate(health_pickups):
        if distance(circle_x, circle_y, pickup["x"], pickup["y"]) < circle_radius + 12:
            health = min(max_health, health + HEALTH_PICKUP_HEAL)
            pickups_to_remove.append(i)
            spawn_particles(pickup["x"], pickup["y"], CYAN, 15, (1, 4), (2, 4))
            play_sound(pickup_sound)

    for i in reversed(pickups_to_remove):
        health_pickups.pop(i)


def update_game_state():
    global health, game_over, damage_flash_timer, game_over_sound_played

    keys = handle_player_movement()
    handle_shooting(keys)
    special_spawn = handle_bullet_collisions()
    handle_enemy_spawning(special_spawn)
    update_enemies()
    handle_player_enemy_collisions()
    handle_pickups()

    if damage_flash_timer > 0:
        damage_flash_timer -= 1

    update_particles()

    if health <= 0:
        health = 0
        game_over = True

    if ammo <= 0 and len(bullets) == 0:
        game_over = True

    if game_over and not game_over_sound_played:
        play_sound(game_over_sound)
        game_over_sound_played = True


def handle_mouse_click(mouse_pos):
    global settings_open, master_mode, sound_enabled, current_window_size_index

    if settings_button.collidepoint(mouse_pos) and not game_over:
        settings_open = not settings_open

    if not settings_open:
        return

    if close_button.collidepoint(mouse_pos):
        settings_open = False
    elif master_mode_button.collidepoint(mouse_pos):
        master_mode = not master_mode
        apply_mode_settings(reset_ammo=True)
    elif sound_button.collidepoint(mouse_pos):
        sound_enabled = not sound_enabled
        update_music_state()
    elif window_size_button.collidepoint(mouse_pos):
        next_index = (current_window_size_index + 1) % len(WINDOW_SIZES)
        apply_window_size(next_index)

    for name, control in setting_controls.items():
        if control["minus"].collidepoint(mouse_pos):
            change_setting(name, -1)
        if control["plus"].collidepoint(mouse_pos):
            change_setting(name, 1)


def draw_game():
    draw_background()

    if damage_flash_timer > 0:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(90 * (damage_flash_timer / damage_flash_duration))
        flash.fill((255, 0, 0, alpha))
        screen.blit(flash, (0, 0))

    if not game_over:
        draw_pickups()
        draw_enemies()
        draw_bullets()
        draw_player()
        draw_particles()
        draw_hud()

    if game_paused and not game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        draw_text("PAUSED", font_big, WHITE, WIDTH // 2, HEIGHT // 2 - 25, center=True)
        draw_text("Press P to resume", font_med, GRAY, WIDTH // 2, HEIGHT // 2 + 30, center=True)

    if settings_open and not game_over:
        draw_settings_menu()

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 0, 0, 190))
        screen.blit(overlay, (0, 0))
        draw_text("GAME OVER", font_big, RED, WIDTH // 2, HEIGHT // 2 - 70, center=True)
        draw_text(f"Final Score: {kill_count}", font_med, WHITE, WIDTH // 2, HEIGHT // 2, center=True)
        draw_text(f"Wave Reached: {wave}", font_med, CYAN, WIDTH // 2, HEIGHT // 2 + 40, center=True)
        if master_mode:
            draw_text("MASTER MODE", font_small, RED, WIDTH // 2, HEIGHT // 2 + 70, center=True)
        draw_text("Press ENTER to Restart", font_small, GRAY, WIDTH // 2, HEIGHT // 2 + 95, center=True)


# =========================================================
# MAIN LOOP
# =========================================================
apply_mode_settings(reset_ammo=False)

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if settings_open:
                    settings_open = False
                else:
                    running = False

            elif event.key == pygame.K_p and not game_over and not settings_open:
                game_paused = not game_paused

            elif event.key == pygame.K_RETURN and game_over:
                reset_game()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_mouse_click(event.pos)

    if not game_over and not game_paused and not settings_open:
        update_game_state()

    draw_game()
    pygame.display.flip()

pygame.quit()