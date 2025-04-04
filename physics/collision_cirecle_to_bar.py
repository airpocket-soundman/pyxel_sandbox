import pyxel
import math

WIDTH = 160
HEIGHT = 120
GRAVITY = 0.3

class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Circle vs Line")
        self.x = 40
        self.y = 0
        self.vx = 1
        self.vy = 0
        self.radius = 5
        self.line_y = 80  # 線の高さ（水平）
        pyxel.run(self.update, self.draw)

    def update(self):
        # 重力適用
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        # 衝突判定：円と水平線
        if self.y + self.radius > self.line_y:
            self.y = self.line_y - self.radius

            # 反射ベクトル計算（法線は (0, -1) ）
            dot = self.vx * 0 + self.vy * -1
            self.vx = self.vx
            self.vy = self.vy - 2 * dot * -1

            # 減衰
            self.vx *= 0.9
            self.vy *= 0.6

    def draw(self):
        pyxel.cls(0)
        pyxel.line(0, self.line_y, WIDTH, self.line_y, 11)
        pyxel.circ(self.x, self.y, self.radius, 10)

App()
