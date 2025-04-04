import pyxel
import math

class App:
    def __init__(self):
        pyxel.init(256, 256, title="Ball Shooter")
        self.reset()
        self.gravity_on = False  # 重力の初期状態はオフ
        self.gravity = 0.1  # 重力加速度
        self.scale_factor = 0.5  # スケールを50%に設定
        pyxel.run(self.update, self.draw)

    def reset(self):
        self.ball_x = pyxel.width // 2
        self.ball_y = pyxel.height - 10
        self.angle_deg = 90  # 初期角度を真上に
        self.speed = 50
        self.launched = False
        self.vx = 0
        self.vy = 0

    def update(self):
        if not self.launched:
            # 角度調整（左: +、右: -）
            if pyxel.btn(pyxel.KEY_LEFT):
                self.angle_deg = min(180, self.angle_deg + 1)
            if pyxel.btn(pyxel.KEY_RIGHT):
                self.angle_deg = max(0, self.angle_deg - 1)
            # 速度調整
            if pyxel.btn(pyxel.KEY_DOWN):
                self.speed = max(0, self.speed - 1)
            if pyxel.btn(pyxel.KEY_UP):
                self.speed = min(100, self.speed + 1)
            # 発射（Fキー）
            if pyxel.btnp(pyxel.KEY_F):
                rad = math.radians(self.angle_deg)
                self.vx = self.speed * math.cos(rad)
                self.vy = -self.speed * math.sin(rad)
                self.launched = True
        else:
            # 重力がオンの場合、Y軸に加速度を加える
            if self.gravity_on:
                self.vy += self.gravity

            # 無重力で直線移動
            self.ball_x += self.vx * 0.1
            self.ball_y += self.vy * 0.1

            # 画面外に出た場合、ボールを再装填
            if (self.ball_x < 0 or self.ball_x > pyxel.width or
                self.ball_y < 0 or self.ball_y > pyxel.height):
                self.reset()

        # Gキーで重力のオン/オフを切り替え
        if pyxel.btnp(pyxel.KEY_G):
            self.gravity_on = not self.gravity_on

    def draw(self):
        pyxel.cls(0)

        # ボール
        pyxel.circ(self.ball_x, self.ball_y, 3, 8)

        # 矢印
        if not self.launched:
            length = 20
            rad = math.radians(self.angle_deg)
            end_x = self.ball_x + length * math.cos(rad)
            end_y = self.ball_y - length * math.sin(rad)
            pyxel.line(self.ball_x, self.ball_y, end_x, end_y, 11)

        # 情報表示
        pyxel.text(5, 5, f"Angle: {self.angle_deg} deg", 7)
        pyxel.text(5, 15, f"Speed: {self.speed}", 7)
        if not self.launched:
            pyxel.text(5, 25, "Press F to shoot", 6)

        # 重力状態表示
        gravity_status = "ON" if self.gravity_on else "OFF"
        pyxel.text(5, 35, f"Gravity: {gravity_status}", 7)

        # vx, vy, vtotal表示
        pyxel.text(5, 45, f"vx: {self.vx:.2f}", 7)
        pyxel.text(5, 55, f"vy: {self.vy:.2f}", 7)

        # 合成速度 (vtotal) の計算
        vtotal = math.sqrt(self.vx**2 + self.vy**2)
        pyxel.text(5, 65, f"vtotal: {vtotal:.2f}", 7)

App()
