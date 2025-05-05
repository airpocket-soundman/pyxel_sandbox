import pyxel
import random
import math

# --------------------------------------------------
# パーティクルシステム設定
# --------------------------------------------------
"""メインエンジンの噴射効果に関する設定"""
FLAME_PARTICLE_COUNT = 20  # 1フレームあたりの炎パーティクル数
FLAME_PARTICLE_LIFETIME = 7  # パーティクルの生存期間（フレーム）
FLAME_PARTICLE_SPEED = 2.0  # パーティクルの基本速度
FLAME_PARTICLE_DENSITY = 2  # パーティクルの密度（線形補間用）

"""着陸時のスモーク効果に関する設定"""
SMOKE_PARTICLE_COUNT = 5  # 1回の衝突あたりのスモークパーティクル数
SMOKE_PARTICLE_LIFETIME = FLAME_PARTICLE_LIFETIME * 20  # 生存期間（炎より長く）
SMOKE_PARTICLE_SPEED_MIN = 0.2  # 最小拡散速度
SMOKE_PARTICLE_SPEED_MAX = 0.5  # 最大拡散速度

"""姿勢制御用スラスタのパーティクル設定"""
THRUSTER_PARTICLE_COUNT = 10  # 1回の噴射あたりのパーティクル数
THRUSTER_PARTICLE_SPEED = 3  # パーティクルの基本速度
THRUSTER_PARTICLE_LIFETIME = 3  # 生存期間（フレーム）
THRUSTER_ANGLE_VARIATION = math.radians(10)  # 噴射角度のばらつき

# --------------------------------------------------
# パーティクルクラス
# --------------------------------------------------
class Particle:
    """
    パーティクルを管理するクラス
    
    Attributes:
        x (float): X座標
        y (float): Y座標
        dx (float): X方向速度
        dy (float): Y方向速度
        lifetime (int): 生存期間（フレーム数）
        color (int): 表示色
        bounced (bool): 地面反射フラグ
        generate_smoke (bool): スモーク生成フラグ
        is_smoke (bool): スモークパーティクル判定
        stage (int): 現在のステージ
        stage1_cleared (bool): ステージ1クリアフラグ
        stage1_clear_display (bool): クリア表示フラグ
    """
    def __init__(self, x, y, dx, dy, lifetime, color, smoke=False):
        """
        パーティクルの初期化
        
        Args:
            x (float): 初期X座標
            y (float): 初期Y座標
            dx (float): X方向初速
            dy (float): Y方向初速
            lifetime (int): 生存期間（フレーム数）
            color (int): パーティクル色
            smoke (bool): スモークパーティクルかどうか
        """
        self.show_chopsticks = False  # ステージ2専用のチョップスティック表示フラグ
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.lifetime = lifetime
        self.color = color
        self.bounced = False
        self.generate_smoke = not smoke
        self.is_smoke = smoke
        self.stage = 1  # 現在のステージ（1: 離陸, 2: 着陸）
        self.stage1_cleared = False  # ステージ1がクリアされたか
        self.stage1_clear_display = False  # 表示フラグ

    def update(self, ground_y):
        """
        パーティクルの状態を更新
        
        Args:
            ground_y (int): 地面のY座標
            
        Returns:
            bool: パーティクルが寿命終了または地面衝突した場合True
        """
        if self.is_smoke:
            self.dy += 0.001  # スモークの浮遊効果

        # 位置と生存時間の更新
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1

        # 地面衝突判定
        if self.generate_smoke and self.y >= ground_y:
            return True  # スモーク生成要求

        # スモークの地面反射処理
        if self.is_smoke and not self.bounced and self.y >= ground_y:
            self.y = ground_y
            angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25)
            speed = math.sqrt(self.dx ** 2 + self.dy ** 2) * 0.5
            self.dx = math.cos(angle) * speed  # 反射後のX速度
            self.dy = math.sin(angle) * speed  # 反射後のY速度
            self.bounced = True  # 反射済みフラグ

        return self.lifetime <= 0  # 生存期間終了判定

    def draw(self):
        """パーティクルを画面に描画"""
        if self.lifetime > 0:
            pyxel.pset(int(self.x), int(self.y), self.color)

# --------------------------------------------------
# パーティクル管理クラス
# --------------------------------------------------
class ParticleManager:
    """
    パーティクルシステムを管理するクラス
    """
    def __init__(self, ground_y):
        """
        パーティクルマネージャーの初期化
        
        Args:
            ground_y (int): 地面のY座標
        """
        self.ground_y = ground_y
        self.flame_particles = []
        self.smoke_particles = []
        self.thruster_particles = []
    
    def clear_particles(self):
        """すべてのパーティクルをクリア"""
        self.flame_particles.clear()
        self.smoke_particles.clear()
        self.thruster_particles.clear()
    
    def spawn_thruster_particles(self, side, rocket_x, rocket_y, rocket_angle, vx, vy, rocket_width):
        """
        姿勢制御スラスタのパーティクルを生成
        
        Args:
            side (str): 噴射側（"left" or "right"）
            rocket_x (float): ロケットのX座標
            rocket_y (float): ロケットのY座標
            rocket_angle (float): ロケットの角度（ラジアン）
            vx (float): ロケットのX方向速度
            vy (float): ロケットのY方向速度
            rocket_width (int): ロケットの幅
        """
        cx = rocket_x
        cy = rocket_y

        right_dx = math.cos(rocket_angle + math.pi / 2)
        right_dy = math.sin(rocket_angle + math.pi / 2)
        up_dx = math.cos(rocket_angle)
        up_dy = math.sin(rocket_angle)

        for current_side in [side, "right" if side == "left" else "left"]:
            side_sign = -1 if current_side == "left" else 1
            side_offset = side_sign * (rocket_width / 2)
            vertical_offset = rocket_width * 3 * 0.4 if current_side == side else -rocket_width * 3 * 0.4

            origin_x = cx + right_dx * side_offset + up_dx * vertical_offset
            origin_y = cy + right_dy * side_offset + up_dy * vertical_offset

            base_angle = rocket_angle + (-math.pi / 2 if current_side == "left" else math.pi / 2)

            for _ in range(THRUSTER_PARTICLE_COUNT):
                variation = random.uniform(-THRUSTER_ANGLE_VARIATION, THRUSTER_ANGLE_VARIATION)
                angle = base_angle + variation
                dx = math.cos(angle) * THRUSTER_PARTICLE_SPEED + vx
                dy = math.sin(angle) * THRUSTER_PARTICLE_SPEED + vy
                lifetime = THRUSTER_PARTICLE_LIFETIME
                color = random.choice([7, 8, 10])
                self.thruster_particles.append(Particle(origin_x, origin_y, dx, dy, lifetime, color, smoke=False))

    def spawn_flame_particles_from_base_line(self, prev_x, prev_y, curr_x, curr_y, rocket_angle, rocket_width):
        """
        ロケットの基底線に沿って炎パーティクルを生成
        
        Args:
            prev_x (float): 前フレームの基底X座標
            prev_y (float): 前フレームの基底Y座標
            curr_x (float): 現在の基底X座標
            curr_y (float): 現在の基底Y座標
            rocket_angle (float): ロケットの角度（ラジアン）
            rocket_width (int): ロケットの幅
        """
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
            offsets = [0] + [random.uniform(-rocket_width / 2, rocket_width / 2) for _ in range(count - 1)]

            for offset in offsets:
                # 側方オフセット（ロケット左右方向）
                base_px = bx + offset * math.cos(rocket_angle + math.pi / 2)
                base_py = by + offset * math.sin(rocket_angle + math.pi / 2)

                # パーティクルの進行方向（真後ろ）
                angle = rocket_angle + math.pi
                dx = math.cos(angle) * FLAME_PARTICLE_SPEED
                dy = math.sin(angle) * FLAME_PARTICLE_SPEED

                # 追加：速度方向に沿って、最大で1フレーム分だけ逆方向にばらけさせる
                back_offset = random.uniform(0, FLAME_PARTICLE_SPEED * 3)
                px = base_px + dx / FLAME_PARTICLE_SPEED * back_offset 
                py = base_py + dy / FLAME_PARTICLE_SPEED * back_offset

                # パーティクルの寿命と色
                lifetime = int(random.uniform(FLAME_PARTICLE_LIFETIME * 0.7, FLAME_PARTICLE_LIFETIME * 1.3))
                color = random.choice([8, 10, 14])

                self.flame_particles.append(Particle(px, py, dx, dy, lifetime, color))

    def spawn_smoke_particles(self, x, y):
        """
        スモークパーティクルを生成
        
        Args:
            x (float): 発生X座標
            y (float): 発生Y座標
            
        Returns:
            list: 生成されたスモークパーティクルのリスト
        """
        particles = []
        for _ in range(SMOKE_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(SMOKE_PARTICLE_SPEED_MIN, SMOKE_PARTICLE_SPEED_MAX)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = int(random.uniform(SMOKE_PARTICLE_LIFETIME * 0.7, SMOKE_PARTICLE_LIFETIME * 1.3))
            particles.append(Particle(x, y, dx, dy, lifetime, 7, smoke=True))
        return particles

    def update_particles(self):
        """
        すべてのパーティクルを更新
        """
        new_smokes = []
        for p in self.flame_particles[:]:
            if p.update(self.ground_y) or p.lifetime <= 0:
                self.flame_particles.remove(p)
                if p.lifetime <= 0:
                    dx = random.uniform(-0.2, 0.0)
                    dy = random.uniform(-0.1, 0.1)
                    self.smoke_particles.append(
                        Particle(p.x, p.y, dx, dy, SMOKE_PARTICLE_LIFETIME, 7, smoke=True)
                    )
                else:
                    new_smokes.extend(self.spawn_smoke_particles(p.x, self.ground_y))
        self.smoke_particles.extend(new_smokes)

        for p in self.smoke_particles[:]:
            if p.update(self.ground_y) or p.lifetime <= 0:
                self.smoke_particles.remove(p)

        for p in self.thruster_particles[:]:
            if p.update(self.ground_y) or p.lifetime <= 0:
                self.thruster_particles.remove(p)
    
    def trigger_explosion_effect(self, x, y):
        """
        爆発エフェクトを生成
        
        Args:
            x (float): 爆発中心X座標
            y (float): 爆発中心Y座標
        """
        for _ in range(500):  # 爆発パーティクル数
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 3.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = random.randint(15, 30)
            color = random.choice([pyxel.COLOR_RED, 
                                   pyxel.COLOR_ORANGE, 
                                   pyxel.COLOR_YELLOW])
            self.flame_particles.append(Particle(x, y, dx, dy, lifetime, color, smoke=False))
    
    def draw_particles(self):
        """
        すべてのパーティクルを描画
        """
        for p in self.flame_particles:
            p.draw()
        for p in self.smoke_particles:
            p.draw()
        for p in self.thruster_particles:
            p.draw()
