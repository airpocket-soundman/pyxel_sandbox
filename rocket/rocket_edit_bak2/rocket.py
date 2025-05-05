import pyxel
import random
import math
from particle import ParticleManager
from rocket_object import RocketObject

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
        rocket (RocketObject): ロケットオブジェクト
        thrust (float): 現在の推力
        gravity (float): 重力加速度
        particle_manager (ParticleManager): パーティクル管理オブジェクト
        thrust_level (float): スロットルレベル（0.0～1.0）
        stage (int): 現在のステージ
    """
    def __init__(self):
        """アプリケーションの初期化"""
        pyxel.init(256, 256, title="Rocket Launch")
        self.game_started = False
        self.countdown = 0
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        """ゲーム状態をリセット"""
        self.game_started = False
        self.countdown = 0
        
        # ロケットオブジェクトの初期化
        initial_x = 128
        initial_y = GROUND_Y - ROCKET_HEIGHT // 2
        self.rocket = RocketObject(initial_x, initial_y, ROCKET_WIDTH, ROCKET_HEIGHT, GROUND_Y)
        self.rocket.draw_stage2 = SHOW_STAGE2
        
        self.thrust = THRUST_PER_FRAME
        self.gravity = GRAVITY_PER_FRAME
        self.particle_manager = ParticleManager(GROUND_Y)
        self.last_base_x, self.last_base_y = self.rocket.get_base_position()
        self.thrust_level = 1.0
        self.stage = 1
        self.stage1_cleared = False
        self.stage1_clear_display = False
        self.stage2_cleared = False
        self.stage2_clear_display = False
        
        # ぶら下がり機構破壊メッセージ用
        self.show_mechanism_broken = False
        self.mechanism_broken_timer = 0

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
        if self.rocket.exploded:
            self.particle_manager.trigger_explosion_effect(self.rocket.x, self.rocket.y)
            self.rocket.exploded = False

        # パーティクル更新
        self.particle_manager.update_particles()

        # 転倒状態ではキー入力無効だが物理演算は継続
        if self.rocket.fallen:
            if self.rocket.exploded:
                self.particle_manager.trigger_explosion_effect(self.rocket.x, self.rocket.y)
                self.rocket.exploded = False
            
            # 転倒時の物理演算
            self.rocket.handle_fallen_state(GROUND_Y)
            self.particle_manager.update_particles()
            return

        if self.rocket.exploded:
            self.particle_manager.trigger_explosion_effect(self.rocket.x, self.rocket.y)
            self.rocket.exploded_done = True
            self.rocket.exploded = False  # 実行後にフラグをリセット
        
        # ↑↓キーで出力（スロットル）を調整
        if not self.stage2_clear_display and not self.rocket.exploded_done and pyxel.btn(pyxel.KEY_UP):
            self.thrust_level = min(1.0, self.thrust_level + 0.01)
        if not self.stage2_clear_display and not self.rocket.exploded_done and pyxel.btn(pyxel.KEY_DOWN):
            self.thrust_level = max(0.0, self.thrust_level - 0.01)
        self.thrust = THRUST_PER_FRAME * self.thrust_level

        self.last_base_x, self.last_base_y = self.rocket.get_base_position()

        # スペースキーで推進
        if not self.stage2_clear_display and not self.rocket.exploded_done and pyxel.btn(pyxel.KEY_SPACE):
            self.rocket.apply_thrust(self.thrust)

        # 位置の更新
        self.rocket.update_position(self.gravity)

        # ステージ2でチョップスティックとの衝突判定
        if self.stage == 2 and self.rocket.show_chopsticks:
            # タワーとチョップスティックの位置情報を取得
            pad_width = 40
            pad_x = pyxel.width // 2 - pad_width // 2
            tower_height = int(ROCKET_HEIGHT * 2.5)  # 60
            tower_x = pad_x + pad_width - 7    # 発射台の右側にオフセット
            
            # チョップスティックの位置情報
            chopstick_length = 30
            chopstick_width = 4
            chopstick_y = GROUND_Y - tower_height + 10
            chopstick_x = tower_x - chopstick_length
            
            # 衝突判定前の速度を記録
            prev_speed = math.hypot(self.rocket.vx, self.rocket.vy)
            
            # 衝突判定
            collision_result = self.rocket.check_chopstick_collision(chopstick_x, chopstick_y, chopstick_width, chopstick_length)
            
            # 衝突後の速度を確認
            curr_speed = math.hypot(self.rocket.vx, self.rocket.vy)
            
            # 速度が半減していれば、ぶら下がり機構破壊と判定
            if prev_speed > 0 and curr_speed < prev_speed * 0.9 and not self.rocket.hanging:
                self.show_mechanism_broken = True
                self.mechanism_broken_timer = 120  # 2秒間表示

        # 地面との衝突判定
        if self.rocket.handle_ground_collision(GROUND_Y, ROTATION_ACCELERATION, ROTATION_FRICTION, RANDING_SPEEED):
            self.rocket.exploded = True
            if self.stage == 1:
                self.particle_manager.trigger_explosion_effect(self.rocket.x, self.rocket.y)
            return

        # 空中での回転制御
        if not self.rocket.fallen:
            if not self.stage2_clear_display and not self.rocket.exploded_done and pyxel.btn(pyxel.KEY_LEFT):
                self.rocket.rotate(-math.radians(2))
                self.particle_manager.spawn_thruster_particles("right", self.rocket.x, self.rocket.y, 
                                                              self.rocket.angle, self.rocket.vx, self.rocket.vy, ROCKET_WIDTH)
            if not self.stage2_clear_display and not self.rocket.exploded_done and pyxel.btn(pyxel.KEY_RIGHT):
                self.rocket.rotate(math.radians(2))
                self.particle_manager.spawn_thruster_particles("left", self.rocket.x, self.rocket.y, 
                                                             self.rocket.angle, self.rocket.vx, self.rocket.vy, ROCKET_WIDTH)

        # メインエンジン噴射時のパーティクル生成
        if not self.stage2_clear_display and not self.rocket.exploded_done and pyxel.btn(pyxel.KEY_SPACE):
            prev_x, prev_y = self.last_base_x, self.last_base_y
            curr_x, curr_y = self.rocket.get_base_position()
            self.particle_manager.spawn_flame_particles_from_base_line(prev_x, prev_y, curr_x, curr_y, 
                                                                      self.rocket.angle, ROCKET_WIDTH)

        # 更新処理
        self.particle_manager.update_particles()

        # ステージ1クリア条件チェック（高度が一定値以上）
        if self.stage == 1 and not self.stage1_cleared:
            height = GROUND_Y - self.rocket.y
            if height >= STAGE1_CLEAR_HEIGHT:
                self.stage1_cleared = True
                self.stage1_clear_display = True  # 表示開始

        if self.stage == 1 and self.stage1_cleared:
            if pyxel.btnp(pyxel.KEY_RETURN):  # ← エンターキーに変更
                self.stage = 2
                print("切り離し！着陸フェーズへ")

                # ステージ2へ移行時の初期化
                self.rocket.draw_stage2 = False  # ★ステージ2では第2段を非表示にする
                self.rocket.x = STAGE2_INITIAL_X
                self.rocket.y = STAGE2_INITIAL_Y
                self.rocket.angle = STAGE2_INITIAL_ANGLE
                self.rocket.vx = STAGE2_INITIAL_VX
                self.rocket.vy = STAGE2_INITIAL_VY
                self.rocket.rotation_speed = 0.0
                self.rocket.show_chopsticks = True  # ★ メカジラのチョップスティックを表示！

                # パーティクルもクリア
                self.particle_manager.clear_particles()

                # 表示を消す
                self.stage1_clear_display = False
            
        # ステージ2クリア条件チェック
        if self.stage == 2 and not self.stage2_cleared:
            # 条件1: 地面に着陸成功
            corners = self.rocket.get_rotated_corners()
            grounded = [(pt, dx, dy) for (pt, dx, dy) in corners if pt[1] >= GROUND_Y]
            if grounded and not self.rocket.exploded_done and self.rocket.vx <= 0.0001 and self.rocket.vy <= 0.0001:
                # 発射台中央からのXオフセット
                center_offset = abs(self.rocket.x - 128)
                print("着陸", center_offset)
                if center_offset <= LANDING_TOLERANCE_PX:
                    self.stage2_cleared = True
                    self.stage2_clear_display = True
            
            # 条件2: チョップスティックにぶら下がり成功
            if self.rocket.hanging and not self.stage2_cleared:
                print("ぶら下がり成功！")
                self.stage2_cleared = True
                self.stage2_clear_display = True
                # ぶら下がり状態でもシミュレーションは継続（即時終了しない）


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
        self.rocket.draw()

        # HUD描画
        speed = math.hypot(self.rocket.vx, self.rocket.vy)
        height = GROUND_Y - self.rocket.y
        horizontal = self.rocket.x - 128
        angle_deg = math.degrees(self.rocket.angle) + 90

        lines = [
            f"SPD: {speed: >+9.2f}",
            f"VX : {self.rocket.vx: >+9.2f}",
            f"VY : {-self.rocket.vy: >+9.2f}",  # 重力方向と表示を合わせるため符号反転
            f"HGT: {height: >+9.2f}",
            f"XOF: {horizontal: >+9.2f}",
            f"ANG: {angle_deg: >+9.2f}",
            f"RSP: {self.rocket.rotation_speed: >+9.6f}",
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

        if not self.rocket.exploded_done and self.stage2_clear_display:
            msg1 = "STAGE 2 LANDING SUCCESS!"
            msg2 = "(PRESS ENTER TO RESTART)"
            x1 = (pyxel.width - len(msg1) * 4) // 2
            x2 = (pyxel.width - len(msg2) * 4) // 2
            pyxel.text(x1, pyxel.height // 2 + 16, msg1, 10)
            pyxel.text(x2, pyxel.height // 2 + 26, msg2, 7)
            
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()

        if self.rocket.exploded_done:
            msg1 = "MISSION FAILED!"
            msg2 = "(press ENTER to reset)"
            x1 = (pyxel.width - len(msg1) * 4) // 2
            x2 = (pyxel.width - len(msg2) * 4) // 2
            pyxel.text(x1, pyxel.height // 2 + 16, msg1, 10)
            pyxel.text(x2, pyxel.height // 2 + 26, msg2, 7)
            
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()

        if self.rocket.show_chopsticks:
            chopstick_length = 30
            chopstick_width = 4  # ここで太さを指定
            chopstick_y = GROUND_Y - tower_height + 10
            pyxel.rect(tower_x - chopstick_length, chopstick_y, chopstick_length, chopstick_width, 7)
            
            # 接続点の強調表示は不要
        
        # ぶら下がり機構破壊メッセージ
        if self.show_mechanism_broken:
            msg = "HANGING MECHANISM BROKEN!"
            x = (pyxel.width - len(msg) * 4) // 2
            pyxel.text(x, 50, msg, 8)
            
            self.mechanism_broken_timer -= 1
            if self.mechanism_broken_timer <= 0:
                self.show_mechanism_broken = False

App()
