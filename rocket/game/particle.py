import pyxel
import random
import math

# 定数定義
GROUND_Y = 240

SMOKE_PARTICLE_LIFETIME = 7 * 20

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
