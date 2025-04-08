import pyxel
import random
import math

# --- 定数定義 ---
ROCKET_WIDTH = 8
ROCKET_HEIGHT = 24
GROUND_Y = 240

FRAME_RATE = 60
GRAVITY = 9.8
THRUST = 12.0
SCALE = 0.3
GRAVITY_PER_FRAME = (GRAVITY / FRAME_RATE) * SCALE
THRUST_PER_FRAME = (THRUST / FRAME_RATE) * SCALE

FLAME_PARTICLE_SPEED = 2.0

AIR_FRICTION = 0.99
GROUND_FRICTION = 0.95

FALL_ANGLE_THRESHOLD = math.radians(20)
ANGLE_ADJUST_SPEED = math.radians(0.5)

TORQUE_FACTOR = 0.02
ANGULAR_DAMPING = 0.98
MAX_FALL_ANGLE = math.radians(90)

FLAME_PARTICLE_LIFETIME = 7         # 🔥 炎のパーティクル寿命
SMOKE_PARTICLE_LIFETIME = 140       # 💨 煙のパーティクル寿命（炎より長い）
SMOKE_PARTICLE_COUNT = 12           # 💨 煙のパーティクル数

class Particle:
    def __init__(self, x, y, dx, dy, lifetime, color, smoke=False):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.lifetime = lifetime
        self.color = color
        self.bounced = False
        self.generate_smoke = not smoke
        self.is_smoke = smoke

    def update(self):
        if self.is_smoke:
            self.dy += 0.001
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1

        if self.generate_smoke and self.y >= GROUND_Y:
            return True

        if self.is_smoke and not self.bounced and self.y >= GROUND_Y:
            self.y = GROUND_Y
            angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25)
            speed = math.sqrt(self.dx ** 2 + self.dy ** 2) * 0.5
            self.dx = math.cos(angle) * speed
            self.dy = math.sin(angle) * speed
            self.bounced = True

        return False

    def draw(self):
        if self.lifetime > 0:
            pyxel.pset(int(self.x), int(self.y), self.color)


class App:
    def __init__(self):
        pyxel.init(256, 256, title="Rocket Launch")
        self.rocket_x = 128
        self.rocket_y = GROUND_Y - ROCKET_HEIGHT // 2
        self.rocket_angle = -math.pi / 2
        self.angular_velocity = 0.0
        self.rotation_speed = math.radians(2)
        self.particles = []

        self.vx = 0
        self.vy = 0
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME

        pyxel.run(self.update, self.draw)

    def get_rotated_corners(self):
        cx = self.rocket_x
        cy = self.rocket_y
        w2 = ROCKET_WIDTH / 2
        h2 = ROCKET_HEIGHT / 2
        sin_a = math.sin(self.rocket_angle)
        cos_a = math.cos(self.rocket_angle)
        corners = []
        for dx, dy in [(-h2, -w2), (h2, -w2), (h2, w2), (-h2, w2)]:
            x = cx + dx * cos_a - dy * sin_a
            y = cy + dx * sin_a + dy * cos_a
            corners.append((x, y))
        return corners

    def get_ground_contact_corner(self):
        corners = self.get_rotated_corners()
        return max(corners, key=lambda c: c[1])

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT):
            self.rocket_angle -= self.rotation_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.rocket_angle += self.rotation_speed

        if pyxel.btn(pyxel.KEY_SPACE):
            ax = math.cos(self.rocket_angle) * self.thrust
            ay = math.sin(self.rocket_angle) * self.thrust
            self.vx += ax
            self.vy += ay

        self.vx *= AIR_FRICTION
        self.vy *= AIR_FRICTION

        self.vy += self.gravity
        self.rocket_x += self.vx
        self.rocket_y += self.vy

        corners = self.get_rotated_corners()
        on_ground = any(y >= GROUND_Y for _, y in corners)
        if on_ground:
            self.vy = 0
            self.vx *= GROUND_FRICTION
            min_dy = min(GROUND_Y - y for _, y in corners)
            self.rocket_y += min_dy

            pivot_x, pivot_y = self.get_ground_contact_corner()
            ideal_upright = -math.pi / 2
            angle_diff = self.rocket_angle - ideal_upright

            if abs(angle_diff) > FALL_ANGLE_THRESHOLD:
                torque = angle_diff * TORQUE_FACTOR
                self.angular_velocity += torque
            else:
                delta = ideal_upright - self.rocket_angle
                delta = max(-ANGLE_ADJUST_SPEED, min(ANGLE_ADJUST_SPEED, delta))
                self.angular_velocity = delta

            self.angular_velocity *= ANGULAR_DAMPING
            self.rocket_angle += self.angular_velocity

            max_angle = ideal_upright + math.pi / 2
            min_angle = ideal_upright - math.pi / 2
            if self.rocket_angle > max_angle:
                self.rocket_angle = max_angle
                self.angular_velocity = 0
            elif self.rocket_angle < min_angle:
                self.rocket_angle = min_angle
                self.angular_velocity = 0

            new_pivot_x, new_pivot_y = self.get_ground_contact_corner()
            self.rocket_x += pivot_x - new_pivot_x
            self.rocket_y += pivot_y - new_pivot_y

        if pyxel.btn(pyxel.KEY_SPACE):
            self.spawn_flame_particles()

        new_particles = []
        for p in self.particles[:]:
            spawn_smoke = p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)
                if not p.is_smoke:
                    dx = random.uniform(-0.2, 0.0)
                    dy = random.uniform(-0.1, 0.1)
                    lifetime = int(random.uniform(SMOKE_PARTICLE_LIFETIME * 0.7,
                                                  SMOKE_PARTICLE_LIFETIME * 1.3))
                    self.particles.append(Particle(p.x, p.y, dx, dy, lifetime, 7, smoke=True))
            elif spawn_smoke:
                self.particles.remove(p)
                new_particles.extend(self.spawn_smoke_particles(p.x, GROUND_Y))
        self.particles.extend(new_particles)

    def spawn_flame_particles(self):
        base_x = self.rocket_x - (ROCKET_HEIGHT / 2) * math.cos(self.rocket_angle)
        base_y = self.rocket_y - (ROCKET_HEIGHT / 2) * math.sin(self.rocket_angle)

        offset = random.uniform(-ROCKET_WIDTH / 2, ROCKET_WIDTH / 2)
        px = base_x + offset * math.cos(self.rocket_angle + math.pi / 2)
        py = base_y + offset * math.sin(self.rocket_angle + math.pi / 2)

        angle = self.rocket_angle + math.pi
        dx = math.cos(angle) * FLAME_PARTICLE_SPEED + self.vx
        dy = math.sin(angle) * FLAME_PARTICLE_SPEED + self.vy

        lifetime = int(random.uniform(FLAME_PARTICLE_LIFETIME * 0.7,
                                      FLAME_PARTICLE_LIFETIME * 1.3))
        color = random.choice([8, 10, 14])
        self.particles.append(Particle(px, py, dx, dy, lifetime, color))

    def spawn_smoke_particles(self, x, y):
        particles = []
        for _ in range(SMOKE_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.2, 0.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = int(random.uniform(SMOKE_PARTICLE_LIFETIME * 0.7,
                                          SMOKE_PARTICLE_LIFETIME * 1.3))
            color = 7
            particles.append(Particle(x, y, dx, dy, lifetime, color, smoke=True))
        return particles

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(0, GROUND_Y, pyxel.width, pyxel.height - GROUND_Y, 4)
        self.draw_rotated_rocket()
        for p in self.particles:
            p.draw()

        angle_deg = math.degrees(self.rocket_angle + math.pi / 2)
        angle_deg = ((angle_deg + 180) % 360) - 180

        info_lines = [
            f"X={self.rocket_x:.1f}",
            f"Y={self.rocket_y:.1f}",
            f"VX={self.vx:.2f}",
            f"VY={-self.vy:.2f}",
            f"ANGLE={angle_deg:.1f}°",
        ]
        for i, line in enumerate(info_lines):
            pyxel.text(pyxel.width - 5 - len(line) * 4, 5 + i * 8, line, 7)

    def draw_rotated_rocket(self):
        corners = self.get_rotated_corners()
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            pyxel.line(int(x1), int(y1), int(x2), int(y2), pyxel.COLOR_WHITE)


# アプリ起動
App()
