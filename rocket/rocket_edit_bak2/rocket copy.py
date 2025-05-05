import pyxel
import random
import math
from particle import ParticleManager

# --------------------------------------------------
# ゲーム定数設定
# --------------------------------------------------
"""ロケットと物理演算に関する基本定数"""
ROCKET_WIDTH = 8  # ロケットの幅（ピクセル）
ROCKET_HEIGHT = 24  # ロケットの高さ（ピクセル）
GROUND_Y = 240  # 地面のY座標

# 物理演算定数
FRAME_RATE = 60  # フレームレート（FPS）
GRAVITY = 9.8  # 重力加速度（m/s²）
THRUST = 12.0  # スラスト力（ニュートン）
SCALE = 0.3  # 表示スケール（物理計算と表示の比率調整）
GRAVITY_PER_FRAME = (GRAVITY / FRAME_RATE) * SCALE  # 1フレームあたりの重力
THRUST_PER_FRAME = (THRUST / FRAME_RATE) * SCALE  # 1フレームあたりの推力

# 回転制御パラメータ
ROTATION_ACCELERATION = math.radians(0.1)  # 回転加速度（ラジアン/フレーム²）
ROTATION_FRICTION = 0.98  # 回転摩擦係数（0.0～1.0）

# --------------------------------------------------
# ゲームプレイ設定
# --------------------------------------------------
"""衝突判定の閾値設定"""
RANDING_SPEEED = 0.5  # 安全着陸と判定する最大速度（ピクセル/フレーム）

"""ゲームの表示関連設定"""
SHOW_STAGE2 = True  # 第2段ロケットの表示フラグ

"""ゲームステージ管理用定数"""
STAGE_LAUNCH = 1     # 離陸ステージ識別子
STAGE_LANDING = 2    # 着陸ステージ識別子

# ステージ1（離陸）クリア条件
STAGE1_CLEAR_HEIGHT = 200  # クリアに必要な最低高度

# ステージ2（着陸）クリア条件
LANDING_TOLERANCE_PX = 10  # 着陸位置の許容誤差（中央からのピクセル数）

"""ステージ2（着陸）の初期状態設定"""
STAGE2_INITIAL_X = 50           # 初期X座標（画面中央は128）
STAGE2_INITIAL_Y = 100          # 初期Y座標
STAGE2_INITIAL_ANGLE = -math.pi / 2  # 初期角度（垂直上向き）
STAGE2_INITIAL_VX = 0.0         # 初期X方向速度
STAGE2_INITIAL_VY = 0.0         # 初期Y方向速度

# --------------------------------------------------
# メインアプリケーションクラス
# --------------------------------------------------
class App:
    """
    メインゲームアプリケーションを管理するクラス
    
    Attributes:
        rocket_x (float): ロケットのX座標
        rocket_y (float): ロケットのY座標
        rocket_angle (float): ロケットの角度（ラジアン）
        rotation_speed (float): 回転速度
        vx (float): X方向速度
        vy (float): Y方向速度
        thrust (float): 現在の推力
        gravity (float): 重力加速度
        particle_manager (ParticleManager): パーティクル管理オブジェクト
        fallen (bool): 転倒フラグ
        exploded (bool): 爆発フラグ
        thrust_level (float): スロットルレベル（0.0～1.0）
        stage (int): 現在のステージ
    """
    def __init__(self):
        """アプリケーションの初期化"""
        pyxel.init(256, 256, title="Rocket Launch")
        self.draw_stage2 = SHOW_STAGE2  # 第2段表示フラグ
        self.game_started = False
        self.countdown = 0
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        """ゲーム状態をリセット"""
        self.game_started = False
        self.countdown = 0
        self.rocket_x = 128
        self.rocket_y = GROUND_Y - ROCKET_HEIGHT // 2
        self.rocket_angle = -math.pi / 2
        self.rotation_speed = 0.0
        self.vx = 0
        self.vy = 0
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME
        self.particle_manager = ParticleManager(GROUND_Y)
        self.last_base_x, self.last_base_y = self.get_rocket_base_position()
        self.fallen = False
        self.exploded = False
        self.exploded_done = False
        self.thrust_level = 1.0
        self.stage = 1
        self.stage1_cleared = False
        self.stage1_clear_display = False
        self.stage2_cleared = False
        self.stage2_clear_display = False
        self.show_chopsticks = False  # ステージ2限定の表示フラグ
        self.draw_stage2 = True

    def get_rocket_base_position(self):
        """
        ロケットの基底座標を計算
        
        Returns:
            tuple: (base_x, base_y) 基底座標
        """
        base_x = self.rocket_x - (ROCKET_HEIGHT / 2) * math.cos(self.rocket_angle)
        base_y = self.rocket_y - (ROCKET_HEIGHT / 2) * math.sin(self.rocket_angle)
        return base_x, base_y

    def get_rotated_corners(self):
        """
        回転後のロケットコーナー座標を計算
        
        Returns:
            list: 4つのコーナー座標とオフセットを含むタプルのリスト
        """
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
        """
        ゲーム状態を更新するメインループ
        
        処理内容:
        - 入力処理
        - 物理計算
        - 衝突判定
        - パーティクル更新
        - ステージ遷移管理
        """
        if pyxel.btnp(pyxel.KEY_R):
            self.reset()

        # ゲーム開始前の処理
        if not self.game_started:
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.game_started = True
                self.countdown = 180  # 3秒 (60fps * 3)
            return

        # カウントダウン処理
        if self.countdown > 0:
            self.countdown -= 1
            if self.countdown == 0:
                # カウントダウン終了、ゲーム開始
                pass
            return

        # 爆発エフェクト処理
        if self.exploded:
            self.particle_manager.trigger_explosion_effect(self.rocket_x, self.rocket_y)
            self.exploded = False

        # パーティクル更新
        self.particle_manager.update_particles()

        # 転倒状態ではキー入力無効だが物理演算は継続
        if self.fallen:
            if self.exploded:
                self.particle_manager.trigger_explosion_effect(self.rocket_x, self.rocket_y)
                self.exploded = False
            
            # 転倒時の物理演算
            corners = self.get_rotated_corners()
            grounded = [(pt, dx, dy) for (pt, dx, dy) in corners if pt[1] >= GROUND_Y]
            if grounded:
                if len(grounded) == 1:
                    _, dx, _ = grounded[0]
                    if abs(dx) > ROCKET_HEIGHT / 2 - 1:
                        # 長辺側で1点接地 - 回転速度を強く減衰
                        #self.rotation_speed *= ROTATION_FRICTION * 0.9
                        self.rocket_angle += self.rotation_speed
                elif len(grounded) >= 2:
                    # 長辺側で2点以上接地 - 完全に停止
                    self.rotation_speed = 0
                    # 地面に密着させる
                    min_y = min(pt[1] for pt, _, _ in grounded)
                    if min_y > GROUND_Y:
                        self.rocket_y -= (min_y - GROUND_Y)
            
            self.particle_manager.update_particles()
            return

        if self.exploded:
            self.particle_manager.trigger_explosion_effect(self.rocket_x, self.rocket_y)
            self.exploded_done = True
            self.exploded = False  # 実行後にフラグをリセット
        
        # ↑↓キーで出力（スロットル）を調整
        if not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_UP):
            self.thrust_level = min(1.0, self.thrust_level + 0.01)
        if not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_DOWN):
            self.thrust_level = max(0.0, self.thrust_level - 0.01)
        self.thrust = THRUST_PER_FRAME * self.thrust_level

        self.last_base_x, self.last_base_y = self.get_rocket_base_position()

        if not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_SPACE):
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

            is_turning_left = not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_LEFT)
            is_turning_right = not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_RIGHT)

            if len(grounded) == 1:
                anchor_pt, dx_anchor, dy_anchor = grounded[0]
            else:
                anchor_pt, dx_anchor, dy_anchor = min(grounded, key=lambda g: g[0][0])  # 左端を基準

            if is_turning_left:
                self.rocket_angle -= math.radians(2)
                self.particle_manager.spawn_thruster_particles("right", self.rocket_x, self.rocket_y, 
                                                              self.rocket_angle, self.vx, self.vy, ROCKET_WIDTH)
            elif is_turning_right:
                self.rocket_angle += math.radians(2)
                self.particle_manager.spawn_thruster_particles("left", self.rocket_x, self.rocket_y, 
                                                             self.rocket_angle, self.vx, self.vy, ROCKET_WIDTH)

            angle_deg = math.degrees(self.rocket_angle) + 90
            if angle_deg > 90 or angle_deg < -90:
                self.exploded = True  # ★ 横転による爆発
                self.fallen = True
                self.rotation_speed = 0  # 回転速度を0に
                self.vx = 0  # X方向速度を0に
                self.vy = 0  # Y方向速度を0に
                if self.stage == 1:
                    self.particle_manager.trigger_explosion_effect(self.rocket_x, self.rocket_y)
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
                if not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_LEFT):
                    self.rocket_angle -= math.radians(2)
                    self.particle_manager.spawn_thruster_particles("right", self.rocket_x, self.rocket_y, 
                                                                  self.rocket_angle, self.vx, self.vy, ROCKET_WIDTH)
                if not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_RIGHT):
                    self.rocket_angle += math.radians(2)
                    self.particle_manager.spawn_thruster_particles("left", self.rocket_x, self.rocket_y, 
                                                                 self.rocket_angle, self.vx, self.vy, ROCKET_WIDTH)

        if not self.stage2_clear_display and not self.exploded_done and pyxel.btn(pyxel.KEY_SPACE):
            prev_x, prev_y = self.last_base_x, self.last_base_y
            curr_x, curr_y = self.get_rocket_base_position()
            self.particle_manager.spawn_flame_particles_from_base_line(prev_x, prev_y, curr_x, curr_y, 
                                                                      self.rocket_angle, ROCKET_WIDTH)

        # 更新処理
        self.particle_manager.update_particles()

        # ステージ1クリア条件チェック（高度が一定値以上）
        if self.stage == 1 and not self.stage1_cleared:
            height = GROUND_Y - self.rocket_y
            if height >= STAGE1_CLEAR_HEIGHT:
                self.stage1_cleared = True
                self.stage1_clear_display = True  # 表示開始

        if self.stage == 1 and self.stage1_cleared:
            if pyxel.btnp(pyxel.KEY_RETURN):  # ← エンターキーに変更
                self.stage = 2
                print("切り離し！着陸フェーズへ")

                # ステージ2へ移行時の初期化
                self.draw_stage2 = False  # ★ステージ2では第2段を非表示にする
                self.rocket_x = STAGE2_INITIAL_X
                self.rocket_y = STAGE2_INITIAL_Y
                self.rocket_angle = STAGE2_INITIAL_ANGLE
                self.vx = STAGE2_INITIAL_VX
                self.vy = STAGE2_INITIAL_VY
                self.rotation_speed = 0.0
                self.show_chopsticks = True  # ★ メカジラのチョップスティックを表示！

                # パーティクルもクリア
                self.particle_manager.clear_particles()

                # 表示を消す
                self.stage1_clear_display = False
            

        # ステージ2クリア条件チェック（爆発しておらず、中央付近に着陸）
        if self.stage == 2 and not self.stage2_cleared:
            # 地面に接地していて、爆発しておらず
            if grounded and not self.exploded_done and self.vx <= 0.0001 and self.vy <= 0.0001:
                # 発射台中央からのXオフセット
                center_offset = abs(self.rocket_x - 128)
                print("着陸",center_offset)
                if center_offset <= LANDING_TOLERANCE_PX:
                    self.stage2_cleared = True
                    self.stage2_clear_display = True

    def draw(self):
        pyxel.cls(12)

        # ゲーム開始前の表示
        if not self.game_started:
            msg = "PUSH SPACE TO GAME START"
            x = (pyxel.width - len(msg) * 4) // 2
            y = pyxel.height // 2
            pyxel.text(x, y, msg, 7)
            return

        # カウントダウン表示
        if self.countdown > 0:
            count = (self.countdown // 60) + 1  # 3,2,1
            msg = str(count)
            x = (pyxel.width - len(msg) * 8) // 2
            y = pyxel.height // 2
            pyxel.text(x, y, msg, 7)
            return

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
        self.draw_rotated_rocket()

        # HUD描画
        speed = math.hypot(self.vx, self.vy)
        height = GROUND_Y - self.rocket_y
        horizontal = self.rocket_x - 128
        angle_deg = math.degrees(self.rocket_angle) + 90

        lines = [
            f"SPD: {speed: >+9.2f}",
            f"VX : {self.vx: >+9.2f}",
            f"VY : {-self.vy: >+9.2f}",  # 重力方向と表示を合わせるため符号反転
            f"HGT: {height: >+9.2f}",
            f"XOF: {horizontal: >+9.2f}",
            f"ANG: {angle_deg: >+9.2f}",
            f"RSP: {self.rotation_speed: >+9.6f}",
            f"THR: {self.thrust_level: >6.2f}" 
        ]

        for i, line in enumerate(lines):
            pyxel.text(pyxel.width - 60, 4 + i * 8, line, 7)
        
        pyxel.text(4, 4, f"STAGE: {'LAUNCH' if self.stage == STAGE_LAUNCH else 'LANDING'}", 7)

        # パーティクル描画
        self.particle_manager.draw_particles()

        if self.stage1_clear_display:
            msg1 = "STAGE 1 CLEAR!"
            msg2 = "(press ENTER to continue)"
            x1 = (pyxel.width - len(msg1) * 4) // 2
            x2 = (pyxel.width - len(msg2) * 4) // 2
            pyxel.text(x1, pyxel.height // 2 - 4, msg1, 7)
            pyxel.text(x2, pyxel.height // 2 + 4, msg2, 6)

        if not self.exploded_done and self.stage2_clear_display:
            msg1 = "STAGE 2 LANDING SUCCESS!"
            msg2 = "(PRESS ENTER TO RESTART)"
            x1 = (pyxel.width - len(msg1) * 4) // 2
            x2 = (pyxel.width - len(msg2) * 4) // 2
            pyxel.text(x1, pyxel.height // 2 + 16, msg1, 10)
            pyxel.text(x2, pyxel.height // 2 + 26, msg2, 7)
            
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()

        if self.exploded_done:
            msg1 = "MISSION FAILED!"
            msg2 = "(press ENTER to reset)"
            x1 = (pyxel.width - len(msg1) * 4) // 2
            x2 = (pyxel.width - len(msg2) * 4) // 2
            pyxel.text(x1, pyxel.height // 2 + 16, msg1, 10)
            pyxel.text(x2, pyxel.height // 2 + 26, msg2, 7)
            
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()


        if self.show_chopsticks:
            chopstick_length = 30
            chopstick_width = 4  # ここで太さを指定
            chopstick_y = GROUND_Y - tower_height + 10
            pyxel.rect(tower_x - chopstick_length, chopstick_y, chopstick_length, chopstick_width, 7)

    def draw_rotated_rocket(self):
        cx = self.rocket_x
        cy = self.rocket_y
        w2 = ROCKET_WIDTH / 2
        h2 = ROCKET_HEIGHT / 2
        sin_a = math.sin(self.rocket_angle)
        cos_a = math.cos(self.rocket_angle)

        # 色：爆発時は赤、通常は濃いグレー（カラー13）
        color = pyxel.COLOR_RED if self.exploded else 1

        # === 第1段ロケット ===
        stage1_corners = []
        for dx, dy in [(-h2, -w2), (h2, -w2), (h2, w2), (-h2, w2)]:
            x = cx + dx * cos_a - dy * sin_a
            y = cy + dx * sin_a + dy * cos_a
            stage1_corners.append((x, y))

        # 三角形2枚で塗りつぶす
        pyxel.tri(*map(int, stage1_corners[0] + stage1_corners[1] + stage1_corners[2]), color)
        pyxel.tri(*map(int, stage1_corners[2] + stage1_corners[3] + stage1_corners[0]), color)

        # === 第2段ロケット（オプション） ===
        if self.draw_stage2:
            offset_x = ROCKET_HEIGHT * cos_a
            offset_y = ROCKET_HEIGHT * sin_a
            stage2_cx = cx + offset_x
            stage2_cy = cy + offset_y

            stage2_corners = []
            for dx, dy in [(-h2, -w2), (h2, -w2), (h2, w2), (-h2, w2)]:
                x = stage2_cx + dx * cos_a - dy * sin_a
                y = stage2_cy + dx * sin_a + dy * cos_a
                stage2_corners.append((x, y))

            # 第2段も塗りつぶし（三角形2枚）
            pyxel.tri(*map(int, stage2_corners[0] + stage2_corners[1] + stage2_corners[2]), color)
            pyxel.tri(*map(int, stage2_corners[2] + stage2_corners[3] + stage2_corners[0]), color)

            # === 第1段と第2段の境界線 ===
            if self.draw_stage2:
                # 第1段の中心位置から、ロケットの「向き」方向に半分の長さだけ移動すれば境界になる
                border_x = cx + h2 * cos_a
                border_y = cy + h2 * sin_a

                # 幅の半分で左右に広げて境界線を描く（カラーは白で）
                left_x = border_x - w2 * sin_a
                left_y = border_y + w2 * cos_a
                right_x = border_x + w2 * sin_a
                right_y = border_y - w2 * cos_a

                pyxel.line(int(left_x), int(left_y), int(right_x), int(right_y), 5)

App()
