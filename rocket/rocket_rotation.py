import pyxel
import random
import math

# 定数定義
ROCKET_WIDTH = 8        # ロケットの幅
ROCKET_HEIGHT = 24      # ロケットの高さ
PARTICLE_LIFETIME = 7   # パーティクルの寿命（フレーム数）
GROUND_Y = 240          # 地面のY座標

FRAME_RATE = 60         # フレームレート
GRAVITY = 9.8           # 重力加速度
THRUST = 12.0           # 推力
SCALE = 0.3             # シミュレーション全体のスケール係数
GRAVITY_PER_FRAME = (GRAVITY / FRAME_RATE) * SCALE
THRUST_PER_FRAME = (THRUST / FRAME_RATE) * SCALE

# パーティクルクラス（炎や煙の表現に使用）
class Particle:
    def __init__(self, x, y, dx, dy, lifetime, color, smoke=False):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.lifetime = lifetime
        self.color = color
        self.bounced = False          # 煙が地面で跳ね返ったかどうか
        self.generate_smoke = not smoke  # 煙でなければtrue（煙を生成するか）
        self.is_smoke = smoke         # 煙パーティクルかどうか

    def update(self):
        # 煙は少し上昇する（浮遊感の演出）
        if self.is_smoke:
            self.dy += 0.001

        # パーティクルの移動
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1

        # 地面に到達した炎パーティクルは煙を発生させる
        if self.generate_smoke and self.y >= GROUND_Y:
            return True

        # 煙が初めて地面に当たったとき、ランダム方向に跳ね返す
        if self.is_smoke and not self.bounced and self.y >= GROUND_Y:
            self.y = GROUND_Y
            angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25)
            speed = math.sqrt(self.dx ** 2 + self.dy ** 2) * 0.5
            self.dx = math.cos(angle) * speed
            self.dy = math.sin(angle) * speed
            self.bounced = True

        return False

    def draw(self):
        # 寿命が残っている間は描画
        if self.lifetime > 0:
            pyxel.pset(int(self.x), int(self.y), self.color)

# アプリ本体
class App:
    def __init__(self):
        pyxel.init(256, 256, title="Rocket Launch")  # ウィンドウ初期化
        self.rocket_x = 128
        self.rocket_y = GROUND_Y - ROCKET_HEIGHT // 2
        self.rocket_angle = -math.pi / 2  # ロケット初期角度（上向き）
        self.rotation_speed = math.radians(2)  # 回転速度
        self.particles = []  # パーティクルのリスト

        self.vx = 0
        self.vy = 0
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME

        # パーティクル発生用にロケットの下部位置を保存
        self.last_base_x, self.last_base_y = self.get_rocket_base_position()

        pyxel.run(self.update, self.draw)

    # ロケットの噴射口（底部）の座標を取得
    def get_rocket_base_position(self):
        base_x = self.rocket_x - (ROCKET_HEIGHT / 2) * math.cos(self.rocket_angle)
        base_y = self.rocket_y - (ROCKET_HEIGHT / 2) * math.sin(self.rocket_angle)
        return base_x, base_y

    def update(self):
        # 前フレームのロケット底部位置を記録
        self.last_base_x, self.last_base_y = self.get_rocket_base_position()

        # 左右キーでロケットを回転
        if pyxel.btn(pyxel.KEY_LEFT):
            self.rocket_angle -= self.rotation_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.rocket_angle += self.rotation_speed

        # スペースキーで推力を与える
        if pyxel.btn(pyxel.KEY_SPACE):
            ax = math.cos(self.rocket_angle) * self.thrust
            ay = math.sin(self.rocket_angle) * self.thrust
            self.vx += ax
            self.vy += ay

        # 重力を加算し、位置更新
        self.vy += self.gravity
        self.rocket_x += self.vx
        self.rocket_y += self.vy

        # 地面との衝突判定
        bottom_y = self.rocket_y + ROCKET_HEIGHT / 2
        if bottom_y >= GROUND_Y:
            self.rocket_y = GROUND_Y - ROCKET_HEIGHT / 2
            self.vy = 0
            self.vx *= 0.95  # 横方向の減速（摩擦の演出）

        # 推力中はパーティクルを発生
        if pyxel.btn(pyxel.KEY_SPACE):
            self.spawn_particles_from_base_line()

        # パーティクルの更新処理
        new_particles = []
        for p in self.particles[:]:
            spawn_smoke = p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)
                if not p.is_smoke:
                    # 炎が寿命を迎えたら煙に変わる
                    lifetime = PARTICLE_LIFETIME * 20
                    dx = random.uniform(-0.2, 0.0)
                    dy = random.uniform(-0.1, 0.1)
                    self.particles.append(Particle(p.x, p.y, dx, dy, lifetime, 7, smoke=True))
            elif spawn_smoke:
                self.particles.remove(p)
                new_particles.extend(self.spawn_smoke_particles(p.x, GROUND_Y))
        self.particles.extend(new_particles)

    # ロケットの噴射位置からパーティクルを連続的に発生させる
    def spawn_particles_from_base_line(self):
        current_base_x, current_base_y = self.get_rocket_base_position()
        dist = math.hypot(current_base_x - self.last_base_x, current_base_y - self.last_base_y)
        steps = max(1, int(dist * 20))  # 距離に応じてステップ数を決定

        for i in range(steps):
            t = i / steps
            bx = self.last_base_x + (current_base_x - self.last_base_x) * t
            by = self.last_base_y + (current_base_y - self.last_base_y) * t

            # パーティクルをランダムに左右にずらす
            offset = random.uniform(-ROCKET_WIDTH / 2, ROCKET_WIDTH / 2)
            px = bx + offset * math.cos(self.rocket_angle + math.pi / 2)
            py = by + offset * math.sin(self.rocket_angle + math.pi / 2)

            # 噴射方向と逆方向にパーティクルを飛ばす
            angle = self.rocket_angle + math.pi
            speed = 2
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed

            lifetime = int(random.uniform(PARTICLE_LIFETIME * 0.7, PARTICLE_LIFETIME * 1.3))
            color = random.choice([8, 10, 14])  # 色は炎っぽく（オレンジ・黄・赤）
            self.particles.append(Particle(px, py, dx, dy, lifetime, color))

    # 煙のパーティクルを地面に生成
    def spawn_smoke_particles(self, x, y):
        particles = []
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.2, 0.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = int(random.uniform(PARTICLE_LIFETIME * 0.7, PARTICLE_LIFETIME * 1.3)) * 20
            color = 7  # 煙は白
            particles.append(Particle(x, y, dx, dy, lifetime, color, smoke=True))
        return particles

    # 描画処理
    def draw(self):
        pyxel.cls(0)  # 背景を黒でクリア
        pyxel.rect(0, GROUND_Y, pyxel.width, pyxel.height - GROUND_Y, 4)  # 地面を描画（緑）
        self.draw_rotated_rocket()  # ロケットを回転状態で描画
        for p in self.particles:
            p.draw()

    # ロケットを現在の角度で回転描画
    def draw_rotated_rocket(self):
        cx = self.rocket_x
        cy = self.rocket_y
        w2 = ROCKET_WIDTH / 2
        h2 = ROCKET_HEIGHT / 2
        sin_a = math.sin(self.rocket_angle)
        cos_a = math.cos(self.rocket_angle)

        # 4隅の座標を回転して計算
        corners = []
        for dx, dy in [(-h2, -w2), (h2, -w2), (h2, w2), (-h2, w2)]:
            x = cx + dx * cos_a - dy * sin_a
            y = cy + dx * sin_a + dy * cos_a
            corners.append((int(x), int(y)))

        # 線で囲んでロケットを描画
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            pyxel.line(x1, y1, x2, y2, pyxel.COLOR_WHITE)

# アプリ起動
App()
