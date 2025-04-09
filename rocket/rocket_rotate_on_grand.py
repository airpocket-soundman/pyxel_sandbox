import pyxel
import random
import math

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
ROTATION_ACCELERATION = math.radians(0.1)  # 回転加速度
ROTATION_FRICTION = 0.98  # 回転摩擦係数
ROTATION_EPSILON = math.radians(0.1)  # 回転角度のゼロ許容範囲

# パーティクル設定
FLAME_PARTICLE_COUNT = 20
FLAME_PARTICLE_LIFETIME = 7
FLAME_PARTICLE_SPEED = 2.0
FLAME_PARTICLE_DENSITY = 2

SMOKE_PARTICLE_COUNT = 12
SMOKE_PARTICLE_LIFETIME = FLAME_PARTICLE_LIFETIME * 20
SMOKE_PARTICLE_SPEED_MIN = 0.2
SMOKE_PARTICLE_SPEED_MAX = 0.5

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
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        self.rocket_x = 128
        self.rocket_y = GROUND_Y - ROCKET_HEIGHT // 2
        self.rocket_angle = -math.pi / 2
        self.rotation_speed = 0.0
        self.vx = 0
        self.vy = 0
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME
        self.flame_particles = []
        self.smoke_particles = []
        self.last_base_x, self.last_base_y = self.get_rocket_base_position()
        self.fallen = False

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
            return

        self.last_base_x, self.last_base_y = self.get_rocket_base_position()

        if pyxel.btn(pyxel.KEY_SPACE):
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
            if len(grounded) == 1:
                _, dx, dy = grounded[0]
                angle_deg = math.degrees(self.rocket_angle) + 90
                if abs(dx) > ROCKET_HEIGHT / 2 - 1:
                    if angle_deg > 15:
                        self.rotation_speed += ROTATION_ACCELERATION
                    elif angle_deg < -15:
                        self.rotation_speed -= ROTATION_ACCELERATION
                    elif abs(angle_deg) <= 15:
                        if angle_deg > 0:
                            self.rotation_speed -= ROTATION_ACCELERATION
                        elif angle_deg < 0:
                            self.rotation_speed += ROTATION_ACCELERATION
                    self.rotation_speed *= ROTATION_FRICTION
                    self.rocket_angle += self.rotation_speed

                else:
                    self.rotation_speed = 0

            else:
                self.rotation_speed = 0
                self.rocket_angle = -math.pi / 2

            is_turning_left = pyxel.btn(pyxel.KEY_LEFT)
            is_turning_right = pyxel.btn(pyxel.KEY_RIGHT)

            if len(grounded) == 1:
                anchor_pt, dx_anchor, dy_anchor = grounded[0]
            else:
                if is_turning_right:
                    anchor_pt, dx_anchor, dy_anchor = max(grounded, key=lambda g: g[0][0])
                else:
                    anchor_pt, dx_anchor, dy_anchor = min(grounded, key=lambda g: g[0][0])

            if is_turning_left:
                self.rocket_angle -= math.radians(2)
            elif is_turning_right:
                self.rocket_angle += math.radians(2)

            angle_deg = math.degrees(self.rocket_angle) + 90
            if angle_deg > 90 or angle_deg < -90:
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
            if pyxel.btn(pyxel.KEY_LEFT):
                self.rocket_angle -= math.radians(2)
            if pyxel.btn(pyxel.KEY_RIGHT):
                self.rocket_angle += math.radians(2)

        if pyxel.btn(pyxel.KEY_SPACE):
            self.spawn_flame_particles_from_base_line()

        new_smokes = []
        for p in self.flame_particles[:]:
            if p.update() or p.lifetime <= 0:
                self.flame_particles.remove(p)
                if p.lifetime <= 0:
                    dx = random.uniform(-0.2, 0.0)
                    dy = random.uniform(-0.1, 0.1)
                    self.smoke_particles.append(
                        Particle(p.x, p.y, dx, dy, SMOKE_PARTICLE_LIFETIME, 7, smoke=True)
                    )
                else:
                    new_smokes.extend(self.spawn_smoke_particles(p.x, GROUND_Y))
        self.smoke_particles.extend(new_smokes)

        for p in self.smoke_particles[:]:
            if p.update() or p.lifetime <= 0:
                self.smoke_particles.remove(p)

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

            offsets = [0] + [
                random.uniform(-ROCKET_WIDTH / 2, ROCKET_WIDTH / 2)
                for _ in range(count - 1)
            ]

            for offset in offsets:
                px = bx + offset * math.cos(self.rocket_angle + math.pi / 2)
                py = by + offset * math.sin(self.rocket_angle + math.pi / 2)

                angle = self.rocket_angle + math.pi
                speed = FLAME_PARTICLE_SPEED
                dx = math.cos(angle) * speed + self.vx
                dy = math.sin(angle) * speed + self.vy

                lifetime = int(random.uniform(FLAME_PARTICLE_LIFETIME * 0.7, FLAME_PARTICLE_LIFETIME * 1.3))
                color = random.choice([8, 10, 14])
                self.flame_particles.append(Particle(px, py, dx, dy, lifetime, color))

    def spawn_smoke_particles(self, x, y):
        particles = []
        for _ in range(SMOKE_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(SMOKE_PARTICLE_SPEED_MIN, SMOKE_PARTICLE_SPEED_MAX)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = int(random.uniform(SMOKE_PARTICLE_LIFETIME * 0.7, SMOKE_PARTICLE_LIFETIME * 1.3))
            particles.append(Particle(x, y, dx, dy, lifetime, 7, smoke=True))
        return particles

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(0, GROUND_Y, pyxel.width, pyxel.height - GROUND_Y, 4)
        self.draw_rotated_rocket()
        for p in self.flame_particles:
            p.draw()
        for p in self.smoke_particles:
            p.draw()

        # HUDの描画
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
            f"RSP: {self.rotation_speed: >+9.6f}"
        ]
        for i, line in enumerate(lines):
            pyxel.text(pyxel.width - 80, 4 + i * 8, line, 7)

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