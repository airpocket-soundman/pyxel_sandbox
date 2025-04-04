import pyxel
import random
import math

# === グローバル定数 ===
ROCKET_WIDTH = 8
ROCKET_HEIGHT = 24
PARTICLE_LIFETIME = 7
GROUND_Y = 240

FRAME_RATE = 60
GRAVITY = 9.8
THRUST = 12.0
GRAVITY_PER_FRAME = GRAVITY / FRAME_RATE
THRUST_PER_FRAME = THRUST / FRAME_RATE

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
        self.rocket_x = pyxel.width // 2
        self.rocket_y = GROUND_Y - ROCKET_HEIGHT // 2
        self.rocket_angle = -math.pi / 2  # 上向き
        self.particle_per_burst = 10
        self.particles = []

        self.vx = 0
        self.vy = 0
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME

        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btn(pyxel.KEY_SPACE):
            ax = math.cos(self.rocket_angle) * self.thrust
            ay = math.sin(self.rocket_angle) * self.thrust
            self.vx += ax
            self.vy += ay
            self.spawn_particles()

        self.vy += self.gravity
        self.rocket_x += self.vx
        self.rocket_y += self.vy

        bottom_y = self.rocket_y + ROCKET_HEIGHT // 2
        if bottom_y >= GROUND_Y:
            self.rocket_y = GROUND_Y - ROCKET_HEIGHT // 2
            self.vy = 0
            self.vx *= 0.95

        new_particles = []
        for p in self.particles[:]:
            spawn_smoke = p.update()

            if p.lifetime <= 0:
                self.particles.remove(p)

                # 🔁 炎 → 白い煙（左方向に流れる風効果）
                if not p.is_smoke:
                    lifetime = PARTICLE_LIFETIME * 20
                    dx = random.uniform(-0.2, 0.0)  # ← 左に流れる風
                    dy = random.uniform(-0.1, 0.1)  # ↑↓ 微妙に揺らぐ
                    self.particles.append(Particle(p.x, p.y, dx, dy, lifetime, 7, smoke=True))

            elif spawn_smoke:
                self.particles.remove(p)
                new_particles.extend(self.spawn_smoke_particles(p.x, GROUND_Y))

        self.particles.extend(new_particles)

    def spawn_particles(self):
        for _ in range(self.particle_per_burst):
            base_x = self.rocket_x - (ROCKET_HEIGHT / 2) * math.cos(self.rocket_angle)
            base_y = self.rocket_y - (ROCKET_HEIGHT / 2) * math.sin(self.rocket_angle)

            offset = random.uniform(-ROCKET_WIDTH / 2, ROCKET_WIDTH / 2)
            px = base_x + offset * math.cos(self.rocket_angle + math.pi / 2)
            py = base_y + offset * math.sin(self.rocket_angle + math.pi / 2)

            angle = self.rocket_angle + math.pi
            speed = 2
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed

            lifetime = int(random.uniform(PARTICLE_LIFETIME * 0.7, PARTICLE_LIFETIME * 1.3))
            color = random.choice([8, 10, 14])
            self.particles.append(Particle(px, py, dx, dy, lifetime, color))

    def spawn_smoke_particles(self, x, y):
        particles = []
        for _ in range(self.particle_per_burst * 2):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.2, 0.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = int(random.uniform(PARTICLE_LIFETIME * 20 * 0.7, PARTICLE_LIFETIME * 2 * 1.3))
            color = 7
            particles.append(Particle(x, y, dx, dy, lifetime, color, smoke=True))
        return particles

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(0, GROUND_Y, pyxel.width, pyxel.height - GROUND_Y, 4)

        pyxel.rect(self.rocket_x - ROCKET_WIDTH // 2,
                   self.rocket_y - ROCKET_HEIGHT // 2,
                   ROCKET_WIDTH, ROCKET_HEIGHT,
                   pyxel.COLOR_WHITE)

        for p in self.particles:
            p.draw()

App()
