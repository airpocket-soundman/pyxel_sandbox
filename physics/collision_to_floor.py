import pyxel

# 初期設定
WIDTH = 160
HEIGHT = 120
GRAVITY = 0.5
FLOOR_Y = HEIGHT - 10

class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Gravity Test")
        self.x = 50
        self.y = 0
        self.vy = 0  # y方向の速度
        self.radius = 5
        pyxel.run(self.update, self.draw)

    def update(self):
        # 重力を加える
        self.vy += GRAVITY
        self.y += self.vy

        # 衝突判定（床に当たったら反発）
        if self.y + self.radius > FLOOR_Y:
            self.y = FLOOR_Y - self.radius
            self.vy *= -0.6  # 反発係数（跳ね返り）

            # 小さな速度なら停止させる
            if abs(self.vy) < 1:
                self.vy = 0

    def draw(self):
        pyxel.cls(0)
        # 床
        pyxel.rect(0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y, 3)
        # ボール
        pyxel.circ(self.x, self.y, self.radius, 8)

App()
