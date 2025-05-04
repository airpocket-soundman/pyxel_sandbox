import pyxel
import random
import math
import particle

# 定数定義
ROCKET_WIDTH = 8
ROCKET_HEIGHT = 24
GROUND_Y = 240

FRAME_RATE = 60
GRAVITY = 9.8
THRUST = 12.0
SCALE = 0.3
GRAVITY_PER_FRAME = (GRAVITY / FRAME_RATE) * SCALE
THRUST_PER_FRAME = (THRUST / FRAME_RATE) * SCALE

# 回転加速度設定
ROTATION_ACCELERATION = math.radians(0.1)
ROTATION_FRICTION = 0.98

# メインエンジンパーティクル
FLAME_PARTICLE_COUNT = 20
FLAME_PARTICLE_LIFETIME = 7
FLAME_PARTICLE_SPEED = 2.0
FLAME_PARTICLE_DENSITY = 2

# スモーク
SMOKE_PARTICLE_COUNT = 5
SMOKE_PARTICLE_LIFETIME = 7 * 20
SMOKE_PARTICLE_SPEED_MIN = 0.2
SMOKE_PARTICLE_SPEED_MAX = 0.5

# スラスタパーティクル設定（←→）
THRUSTER_PARTICLE_COUNT = 10
THRUSTER_PARTICLE_SPEED = 3
THRUSTER_PARTICLE_LIFETIME = 3
THRUSTER_ANGLE_VARIATION = math.radians(10)

# 衝突判定
RANDING_SPEEED = 0.5  # 衝突判定の閾値（速度）

# 表示設定
SHOW_STAGE2 = True  # 第2段を描画するかどうか（Trueで描画、Falseで非表示）

class RocketStage:
    def __init__(self, x, y, angle, height_offset=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.height_offset = height_offset
        self.width = ROCKET_WIDTH
        self.height = ROCKET_HEIGHT
        self.color = 13 # 爆発時は赤、通常は濃いグレー（カラー13）

    def get_corners(self):
        cx = self.x
        cy = self.y
        w2 = self.width / 2
        h2 = self.height / 2
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        corners = []
        for dx, dy in [(-h2, -w2), (h2, -w2), (h2, w2), (-h2, w2)]:
            x = cx + dx * cos_a - dy * sin_a
            y = cy + dx * sin_a + dy * cos_a
            corners.append((x, y))
        return corners

    def draw(self):
        corners = self.get_corners()
        pyxel.tri(*map(int, corners[0] + corners[1] + corners[2]), self.color)
        pyxel.tri(*map(int, corners[2] + corners[3] + corners[0]), self.color)

class App:
    def __init__(self):
        pyxel.init(256, 256, title="Rocket Launch")
        self.draw_stage2 = SHOW_STAGE2  # ← このように初期化
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        self.rocket_x = 128
        self.rocket_y = GROUND_Y - ROCKET_HEIGHT
        self.rocket_angle = -math.pi / 2
        self.rotation_speed = 0.0
        self.vx = 0
        self.vy = 0
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME
        self.flame_particles = []
        self.smoke_particles = []
        self.thruster_particles = []
        self.last_base_x, self.last_base_y = self.get_rocket_base_position()
        self.fallen = False
        self.exploded = False
        self.exploded_done = False
        self.thrust_level = 1.0

        # ロケットの各段を初期化
        self.stage1 = RocketStage(self.rocket_x, self.rocket_y, self.rocket_angle)
        self.stage2 = RocketStage(self.rocket_x, self.rocket_y - ROCKET_HEIGHT/2, self.rocket_angle, height_offset=ROCKET_HEIGHT)

    def get_rocket_base_position(self):
        base_x = self.rocket_x - (ROCKET_HEIGHT / 2) * math.cos(self.rocket_angle)
        base_y = self.rocket_y - (ROCKET_HEIGHT / 2) * math.sin(self.rocket_angle)
        return base_x, base_y

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
            corners.append(((x, y), dx, dy))
        return corners

    def update(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.reset()

        if self.fallen:
            
            if self.exploded:
                self.trigger_explosion_effect()
                self.exploded = False  # 実行後にフラグをリセット

            # パーティクルだけ更新し続ける
            self.update_particles()

            # パーティクルがすべて消えるまで処理継続（終了せずに待機）
            if not self.flame_particles and not self.smoke_particles and not self.thruster_particles:
                return
            return

        if self.exploded:
            self.trigger_explosion_effect()
            self.exploded_done = True
            self.exploded = False  # 実行後にフラグをリセット
        
        # ↑↓キーで出力（スロットル）を調整
        if pyxel.btn(pyxel.KEY_UP):
            self.thrust_level = min(1.0, self.thrust_level + 0.01)
        if pyxel.btn(pyxel.KEY_DOWN):
            self.thrust_level = max(0.0, self.thrust_level - 0.01)
        self.thrust = THRUST_PER_FRAME * self.thrust_level

        self.last_base_x, self.last_base_y = self.get_rocket_base_position()

        if not self.exploded_done and pyxel.btn(pyxel.KEY_SPACE):
            ax = math.cos(self.rocket_angle) * self.thrust
            ay = math.sin(self.rocket_angle) * self.thrust
            self.vx += ax
            self.vy += ay

        self.vy += self.gravity
        self.rocket_x += self.vx
        self.rocket_y += self.vy

        corners = self.get_rotated_corners()
        grounded = [(pt, dx, dy) for (pt, dx, dy) in corners if pt[1] >= GROUND_Y]
        if grounded:

            # ★着地時の爆発判定（1）
            speed = math.hypot(self.vx, self.vy)
            if speed > RANDING_SPEEED:
                self.exploded = True
                
                # 強制転倒（12°以内なら13°に）
                angle_deg = math.degrees(self.rocket_angle) + 90
                if abs(angle_deg) <= 12:
                    if angle_deg >= 0:
                        self.rocket_angle = math.radians(13 - 90)  # +13°
                    else:
                        self.rocket_angle = math.radians(-13 - 90)  # -13°




            if len(grounded) == 1:
                _, dx, _ = grounded[0]
                angle_deg = math.degrees(self.rocket_angle) + 90
                if abs(dx) > ROCKET_HEIGHT / 2 - 1:
                    if angle_deg > 12:
                        self.rotation_speed += ROTATION_ACCELERATION
                    elif angle_deg < -12:
                        self.rotation_speed -= ROTATION_ACCELERATION
                    elif abs(angle_deg) <= 12:
                        if angle_deg > 0: 
                            self.rotation_speed -= ROTATION_ACCELERATION
                        elif angle_deg < 0:
                            self.rotation_speed += ROTATION_ACCELERATION
                    self.rotation_speed *= ROTATION_FRICTION
                    self.rocket_angle += self.rotation_speed
                    if abs(self.rotation_speed) < 0.00001:
                        self.rotation_speed = 0.0
                        if not self.exploded and not self.exploded_done:
                            self.rocket_angle = -math.pi / 2
                else:
                    self.rotation_speed = 0
            else:
                self.rotation_speed = 0
                if not self.exploded and not self.exploded_done:
                    self.rocket_angle = -math.pi / 2

            is_turning_left = not self.exploded_done and pyxel.btn(pyxel.KEY_LEFT)
            is_turning_right = not self.exploded_done and pyxel.btn(pyxel.KEY_RIGHT)

            if len(grounded) == 1:
                anchor_pt, dx_anchor, dy_anchor = grounded[0]
            else:
                anchor_pt, dx_anchor, dy_anchor = min(grounded, key=lambda g: g[0][0])  # 左端を基準

            if is_turning_left:
                self.rocket_angle -= math.radians(2)
                self.spawn_thruster_particles("right")
            elif is_turning_right:
                self.rocket_angle += math.radians(2)
                self.spawn_thruster_particles("left")

            angle_deg = math.degrees(self.rocket_angle) + 90
            if angle_deg > 90 or angle_deg < -90:
                self.exploded = True  # ★ 横転による爆発
                self.fallen = True
                return

            cos_a = math.cos(self.rocket_angle)
            sin_a = math.sin(self.rocket_angle)
            self.rocket_x = anchor_pt[0] - (dx_anchor * cos_a - dy_anchor * sin_a)
            self.rocket_y = anchor_pt[1] - (dx_anchor * sin_a + dy_anchor * cos_a)

            self.vy = 0
            self.vx *= 0.95

            corrected_corners = self.get_rotated_corners()
            min_dy = min(0, min(GROUND_Y - pt[1] for pt, _, _ in corrected_corners))
            self.rocket_y += min_dy

        else:
            self.rotation_speed = 0
            if not self.fallen:
                if pyxel.btn(pyxel.KEY_LEFT):
                    self.rocket_angle -= math.radians(2)
                    self.spawn_thruster_particles("right")
                if pyxel.btn(pyxel.KEY_RIGHT):
                    self.rocket_angle += math.radians(2)
                    self.spawn_thruster_particles("left")

        if pyxel.btn(pyxel.KEY_SPACE):
            self.spawn_flame_particles_from_base_line()

        # 更新処理
        self.update_particles()

        # ロケットの位置と角度を更新
        self.stage1.x = self.rocket_x
        self.stage1.y = self.rocket_y
        self.stage1.angle = self.rocket_angle
        self.stage2.x = self.rocket_x
        self.stage2.y = self.rocket_y - ROCKET_HEIGHT
        self.stage2.angle = self.rocket_angle

    def spawn_thruster_particles(self, side):
        cx = self.rocket_x
        cy = self.rocket_y

        right_dx = math.cos(self.rocket_angle + math.pi / 2)
        right_dy = math.sin(self.rocket_angle + math.pi / 2)
        up_dx = math.cos(self.rocket_angle)
        up_dy = math.sin(self.rocket_angle)

        for current_side in [side, "right" if side == "left" else "left"]:
            side_sign = -1 if current_side == "left" else 1
            side_offset = side_sign * (ROCKET_WIDTH / 2)
            vertical_offset = ROCKET_HEIGHT * 0.4 if current_side == side else -ROCKET_HEIGHT * 0.4

            origin_x = cx + right_dx * side_offset + up_dx * vertical_offset
            origin_y = cy + right_dy * side_offset + up_dy * vertical_offset

            base_angle = self.rocket_angle + (-math.pi / 2 if current_side == "left" else math.pi / 2)

            for _ in range(THRUSTER_PARTICLE_COUNT):
                variation = random.uniform(-THRUSTER_ANGLE_VARIATION, THRUSTER_ANGLE_VARIATION)
                angle = base_angle + variation
                dx = math.cos(angle) * THRUSTER_PARTICLE_SPEED + self.vx
                dy = math.sin(angle) * THRUSTER_PARTICLE_SPEED + self.vy
                lifetime = THRUSTER_PARTICLE_LIFETIME
                color = random.choice([7, 8, 10])
                # self.thruster_particles.append(Particle(origin_x, origin_y, dx, dy, lifetime, color, smoke=False))
                self.thruster_particles.append(particle.Particle(origin_x, origin_y, dx, dy, lifetime, color, smoke=False))

    def spawn_flame_particles_from_base_line(self):
        prev_x, prev_y = self.last_base_x, self.last_base_y
        curr_x, curr_y = self.get_rocket_base_position()
        dist = math.hypot(curr_x - prev_x, curr_y - prev_y)
        num_lines = max(1, int(dist * FLAME_PARTICLE_DENSITY))
        total_particles = FLAME_PARTICLE_COUNT
        particles_per_line = total_particles // num_lines
        extras = total_particles % num_lines

        for i in range(num_lines):
            t = i / (num_lines - 1) if num_lines > 1 else 0
            bx = prev_x + (curr_x - prev_x) * t
            by = prev_y + (curr_y - prev_y) * t
            count = particles_per_line + (1 if i < extras else 0)
            offsets = [0] + [random.uniform(-ROCKET_WIDTH / 2, ROCKET_WIDTH / 2) for _ in range(count - 1)]

            for offset in offsets:
                px = bx + offset * math.cos(self.rocket_angle + math.pi / 2)
                py = by + offset * math.sin(self.rocket_angle + math.pi / 2)
                angle = self.rocket_angle + math.pi
                dx = math.cos(angle) * FLAME_PARTICLE_SPEED + self.vx
                dy = math.sin(angle) * FLAME_PARTICLE_SPEED + self.vy
                lifetime = int(random.uniform(FLAME_PARTICLE_LIFETIME * 0.7, FLAME_PARTICLE_LIFETIME * 1.3))
                color = random.choice([8, 10, 14])
                # self.flame_particles.append(Particle(px, py, dx, dy, lifetime, color))
                self.flame_particles.append(particle.Particle(px, py, dx, dy, lifetime, color))

    def spawn_smoke_particles(self, x, y):
        particles = []
        for _ in range(SMOKE_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(SMOKE_PARTICLE_SPEED_MIN, SMOKE_PARTICLE_SPEED_MAX)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = int(random.uniform(SMOKE_PARTICLE_LIFETIME * 0.7, SMOKE_PARTICLE_LIFETIME * 1.3))
            # particles.append(Particle(x, y, dx, dy, lifetime, 7, smoke=True))
            particles.append(particle.Particle(x, y, dx, dy, lifetime, 7, smoke=True))
        return particles

    def update_particles(self):
        new_smokes = []
        for p in self.flame_particles[:]:
            if p.update() or p.lifetime <= 0:
                self.flame_particles.remove(p)
                if p.lifetime <= 0:
                    dx = random.uniform(-0.2, 0.0)
                    dy = random.uniform(-0.1, 0.1)
                    # self.smoke_particles.append(
                    #     Particle(p.x, p.y, dx, dy, SMOKE_PARTICLE_LIFETIME, 7, smoke=True)
                    # )
                    self.smoke_particles.append(
                        particle.Particle(p.x, p.y, dx, dy, SMOKE_PARTICLE_LIFETIME, 7, smoke=True)
                    )
                else:
                    new_smokes.extend(self.spawn_smoke_particles(p.x, GROUND_Y))
        self.smoke_particles.extend(new_smokes)

        for p in self.smoke_particles[:]:
            if p.update() or p.lifetime <= 0:
                self.smoke_particles.remove(p)

        for p in self.thruster_particles[:]:
            if p.update() or p.lifetime <= 0:
                self.thruster_particles.remove(p)

    def draw(self):
        pyxel.cls(12)

        # 地面（カラー4：茶色）
        pyxel.rect(0, GROUND_Y, pyxel.width, pyxel.height - GROUND_Y, 4)

        # 発射台（カラー5：グレー）
        pad_width = 40
        pad_height = 8
        pad_x = pyxel.width // 2 - pad_width // 2
        pad_y = GROUND_Y
        pyxel.rect(pad_x, pad_y, pad_width, pad_height, 5)

        # タワー（トラス構造 / 白：カラー7）
        tower_height = int(ROCKET_HEIGHT * 2.5)  # 60
        tower_x = pad_x + pad_width - 7    # 発射台の右側にオフセット
        tower_y_top = GROUND_Y - tower_height
        tower_y_bottom = GROUND_Y

        # 縦の支柱
        pyxel.line(tower_x, tower_y_top, tower_x, tower_y_bottom, 7)
        pyxel.line(tower_x + 6, tower_y_top, tower_x + 6, tower_y_bottom, 7)

        # 横の連結（5ピクセルおき）
        for y in range(tower_y_top, tower_y_bottom, 5):
            pyxel.line(tower_x, y, tower_x + 6, y, 7)

        # 斜めのトラス（交差するX構造）
        for i in range(0, tower_height, 10):
            y1 = tower_y_top + i
            y2 = y1 + 10
            if y2 <= tower_y_bottom:
                pyxel.line(tower_x, y1, tower_x + 6, y2, 7)
                pyxel.line(tower_x + 6, y1, tower_x, y2, 7)

        # ロケット本体
        self.stage1.draw()
        if self.draw_stage2:
            self.stage2.draw()

            # === 第1段と第2段の境界線 ===
            # 第1段の中心位置から、ロケットの「向き」方向に半分の長さだけ移動すれば境界になる
            h2 = ROCKET_HEIGHT / 2
            w2 = ROCKET_WIDTH / 2
            cx = self.rocket_x
            cy = self.rocket_y
            sin_a = math.sin(self.rocket_angle)
            cos_a = math.cos(self.rocket_angle)
            border_x = cx + h2 * cos_a
            border_y = cy + h2 * sin_a

            # 幅の半分で左右に広げて境界線を描く（カラーは白で）
            left_x = border_x - w2 * sin_a
            left_y = border_y + w2 * cos_a
            right_x = border_x + w2 * sin_a
            right_y = border_y - w2 * cos_a

            pyxel.line(int(left_x), int(left_y), int(right_x), int(right_y), 5)

        # HUD描画
        speed = math.hypot(self.vx, self.vy)
        height = GROUND_Y - self.rocket_y
        horizontal = self.rocket_x - 128
        angle_deg = math.degrees(self.rocket_angle) + 90

        lines = [
            f"SPD: {speed: >+9.2f}",
            f"VX : {self.vx: >+9.2f}",
            f"VY : {self.vy: >+9.2f}",
            f"HGT: {height: >+9.2f}",
            f"XOF: {horizontal: >+9.2f}",
            f"ANG: {angle_deg: >+9.2f}",
            f"RSP: {self.rotation_speed: >+9.6f}",
            f"THR: {self.thrust_level: >6.2f}" 
        ]
        for i, line in enumerate(lines):
            pyxel.text(pyxel.width - 60, 4 + i * 8, line, 7)

        # パーティクル描画
        for p in self.flame_particles:
            p.draw()
        for p in self.smoke_particles:
            p.draw()
        for p in self.thruster_particles:
            p.draw()

    def trigger_explosion_effect(self):
        for _ in range(500):  # 爆発パーティクル数（調整可）
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 3.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = random.randint(15, 30)
            color = random.choice([pyxel.COLOR_RED, pyxel.COLOR_ORANGE, pyxel.COLOR_YELLOW])
            # self.flame_particles.append(
            #     Particle(self.rocket_x, self.rocket_y, dx, dy, lifetime, color, smoke=False)
            # )
            self.flame_particles.append(
                particle.Particle(self.rocket_x, self.rocket_y, dx, dy, lifetime, color, smoke=False)
            )

App()
