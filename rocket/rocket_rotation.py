import pyxel
import random
import math

ROCKET_WIDTH = 8
ROCKET_HEIGHT = 24
PARTICLE_LIFETIME = 7
GROUND_Y = 240

FRAME_RATE = 60
GRAVITY = 9.8
THRUST = 12.0
SCALE = 0.3  # スケール係数
GRAVITY_PER_FRAME = (GRAVITY / FRAME_RATE) * SCALE
THRUST_PER_FRAME = (THRUST / FRAME_RATE) * SCALE

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
        self.rotation_speed = math.radians(2)
        self.particles = []

        self.vx = 0
        self.vy = 0
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME

        self.last_base_x, self.last_base_y = self.get_rocket_base_position()

        pyxel.run(self.update, self.draw)

    def get_rocket_base_position(self):
        base_x = self.rocket_x - (ROCKET_HEIGHT / 2) * math.cos(self.rocket_angle)
        base_y = self.rocket_y - (ROCKET_HEIGHT / 2) * math.sin(self.rocket_angle)
        return base_x, base_y

    def update(self):
        self.last_base_x, self.last_base_y = self.get_rocket_base_position()

        if pyxel.btn(pyxel.KEY_LEFT):
            self.rocket_angle -= self.rotation_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.rocket_angle += self.rotation_speed

        if pyxel.btn(pyxel.KEY_SPACE):
            ax = math.cos(self.rocket_angle) * self.thrust
            ay = math.sin(self.rocket_angle) * self.thrust
            self.vx += ax
            self.vy += ay

        self.vy += self.gravity
        self.rocket_x += self.vx
        self.rocket_y += self.vy

        bottom_y = self.rocket_y + ROCKET_HEIGHT / 2
        if bottom_y >= GROUND_Y:
            self.rocket_y = GROUND_Y - ROCKET_HEIGHT / 2
            self.vy = 0
            self.vx *= 0.95

        if pyxel.btn(pyxel.KEY_SPACE):
            self.spawn_particles_from_base_line()

        new_particles = []
        for p in self.particles[:]:
            spawn_smoke = p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)
                if not p.is_smoke:
                    lifetime = PARTICLE_LIFETIME * 20
                    dx = random.uniform(-0.2, 0.0)
                    dy = random.uniform(-0.1, 0.1)
                    self.particles.append(Particle(p.x, p.y, dx, dy, lifetime, 7, smoke=True))
            elif spawn_smoke:
                self.particles.remove(p)
                new_particles.extend(self.spawn_smoke_particles(p.x, GROUND_Y))
        self.particles.extend(new_particles)

    def spawn_particles_from_base_line(self):
        current_base_x, current_base_y = self.get_rocket_base_position()
        dist = math.hypot(current_base_x - self.last_base_x, current_base_y - self.last_base_y)
        steps = max(1, int(dist*20))

        for i in range(steps):
            t = i / steps
            bx = self.last_base_x + (current_base_x - self.last_base_x) * t
            by = self.last_base_y + (current_base_y - self.last_base_y) * t

            offset = random.uniform(-ROCKET_WIDTH / 2, ROCKET_WIDTH / 2)
            px = bx + offset * math.cos(self.rocket_angle + math.pi / 2)
            py = by + offset * math.sin(self.rocket_angle + math.pi / 2)

            angle = self.rocket_angle + math.pi
            speed = 2
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed

            lifetime = int(random.uniform(PARTICLE_LIFETIME * 0.7, PARTICLE_LIFETIME * 1.3))
            color = random.choice([8, 10, 14])
            self.particles.append(Particle(px, py, dx, dy, lifetime, color))

    def spawn_smoke_particles(self, x, y):
        particles = []
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.2, 0.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = int(random.uniform(PARTICLE_LIFETIME * 0.7, PARTICLE_LIFETIME * 1.3)) * 20
            color = 7
            particles.append(Particle(x, y, dx, dy, lifetime, color, smoke=True))
        return particles

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(0, GROUND_Y, pyxel.width, pyxel.height - GROUND_Y, 4)
        self.draw_rotated_rocket()
        for p in self.particles:
            p.draw()

    def draw_rotated_rocket(self):
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
            corners.append((int(x), int(y)))
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            pyxel.line(x1, y1, x2, y2, pyxel.COLOR_WHITE)

App()