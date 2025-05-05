import pyxel
import math

class RocketObject:
    """
    ロケット本体のオブジェクトを管理するクラス
    
    Attributes:
        x (float): ロケットのX座標
        y (float): ロケットのY座標
        angle (float): ロケットの角度（ラジアン）
        rotation_speed (float): 回転速度
        vx (float): X方向速度
        vy (float): Y方向速度
        width (int): ロケットの幅
        height (int): ロケットの高さ
        draw_stage2 (bool): 第2段ロケットの表示フラグ
        fallen (bool): 転倒フラグ
        exploded (bool): 爆発フラグ
        exploded_done (bool): 爆発完了フラグ
        hanging (bool): チョップスティックにぶら下がっているかのフラグ
        hanging_point_x (float): ぶら下がり判定点のX座標
        hanging_point_y (float): ぶら下がり判定点のY座標
    """
    
    def __init__(self, x, y, width, height, ground_y):
        """
        ロケットオブジェクトの初期化
        
        Args:
            x (float): 初期X座標
            y (float): 初期Y座標
            width (int): ロケットの幅
            height (int): ロケットの高さ
            ground_y (int): 地面のY座標
        """
        self.x = x
        self.y = y
        self.angle = -math.pi / 2  # 初期角度（垂直上向き）
        self.rotation_speed = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.width = width
        self.height = height
        self.ground_y = ground_y
        self.draw_stage2 = True
        self.fallen = False
        self.exploded = False
        self.exploded_done = False
        self.last_base_x, self.last_base_y = self.get_base_position()
        self.show_chopsticks = False  # ステージ2限定の表示フラグ
        self.hanging = False  # チョップスティックにぶら下がっているかのフラグ
        self.hanging_point_x = 0.0  # ぶら下がり判定点のX座標
        self.hanging_point_y = 0.0  # ぶら下がり判定点のY座標
        self.hanging_mechanism_broken = False  # ぶら下がり機構破壊フラグ
        self.pendulum_angle_velocity = 0.0  # 振り子の角速度
        self.pendulum_damping = 0.995  # 振り子の減衰係数（大きいほど長くぶらぶらする）
        self.update_hanging_point()  # ぶら下がり判定点の初期化
    
    def reset(self, x, y):
        """
        ロケットの状態をリセット
        
        Args:
            x (float): リセット後のX座標
            y (float): リセット後のY座標
        """
        self.x = x
        self.y = y
        self.angle = -math.pi / 2
        self.rotation_speed = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.fallen = False
        self.exploded = False
        self.exploded_done = False
        self.draw_stage2 = True
        self.last_base_x, self.last_base_y = self.get_base_position()
        self.show_chopsticks = False
        self.hanging = False
        self.hanging_mechanism_broken = False
        self.pendulum_angle_velocity = 0.0
        self.update_hanging_point()
    
    def update_hanging_point(self):
        """
        ロケットの上辺からロケットの長さの1/10のところにある当たり判定点の座標を更新
        """
        # ロケットの上端から1/10の位置
        offset = self.height * 0.1
        
        # ロケットの中心から上方向にheight/2 - offsetの距離にある点
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        
        # ロケットの中心から上方向へのベクトル
        up_x = cos_a
        up_y = sin_a
        
        # 当たり判定点の座標
        self.hanging_point_x = self.x + up_x * (self.height / 2 - offset)
        self.hanging_point_y = self.y + up_y * (self.height / 2 - offset)
    
    def get_base_position(self):
        """
        ロケットの基底座標を計算
        
        Returns:
            tuple: (base_x, base_y) 基底座標
        """
        base_x = self.x - (self.height / 2) * math.cos(self.angle)
        base_y = self.y - (self.height / 2) * math.sin(self.angle)
        return base_x, base_y
    
    def get_rotated_corners(self):
        """
        回転後のロケットコーナー座標を計算
        
        Returns:
            list: 4つのコーナー座標とオフセットを含むタプルのリスト
        """
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
            corners.append(((x, y), dx, dy))
        return corners
    
    def update_position(self, gravity):
        """
        ロケットの位置を更新
        
        Args:
            gravity (float): 重力加速度
        """
        # ぶら下がっている場合は振り子の物理演算
        if self.hanging:
            # 振り子の物理演算
            # 垂直下向きからの角度
            pendulum_angle = self.angle - math.pi/2
            
            # 振り子の運動方程式: d²θ/dt² = -(g/L)sinθ
            # ここでは簡略化して角度に比例する力を適用
            pendulum_acceleration = -0.05 * math.sin(pendulum_angle)  # 重力による角加速度
            
            # 角速度の更新
            self.pendulum_angle_velocity += pendulum_acceleration
            
            # 減衰（空気抵抗など）
            self.pendulum_angle_velocity *= self.pendulum_damping
            
            # 角度の更新
            self.angle += self.pendulum_angle_velocity
            
            # 角度の制限（-45度～45度）
            max_angle = math.radians(45)
            min_angle = math.radians(-45)
            adjusted_angle = self.angle - math.pi/2
            
            if adjusted_angle > max_angle:
                self.angle = math.pi/2 + max_angle
                self.pendulum_angle_velocity *= -0.5  # 壁に当たったような反発
            elif adjusted_angle < min_angle:
                self.angle = math.pi/2 + min_angle
                self.pendulum_angle_velocity *= -0.5  # 壁に当たったような反発
            
            # 当たり判定点の更新
            self.update_hanging_point()
            return
            
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.update_hanging_point()
    
    def apply_thrust(self, thrust_force):
        """
        推力を適用
        
        Args:
            thrust_force (float): 適用する推力
        """
        # ぶら下がっている場合は推力を無効化
        if self.hanging:
            return
            
        ax = math.cos(self.angle) * thrust_force
        ay = math.sin(self.angle) * thrust_force
        self.vx += ax
        self.vy += ay
    
    def handle_ground_collision(self, ground_y, rotation_acceleration, rotation_friction, landing_speed):
        """
        地面との衝突処理
        
        Args:
            ground_y (int): 地面のY座標
            rotation_acceleration (float): 回転加速度
            rotation_friction (float): 回転摩擦係数
            landing_speed (float): 安全着陸と判定する最大速度
            
        Returns:
            bool: 爆発が発生したかどうか
        """
        # ぶら下がっている場合は地面との衝突判定をスキップ
        if self.hanging:
            return False
            
        corners = self.get_rotated_corners()
        grounded = [(pt, dx, dy) for (pt, dx, dy) in corners if pt[1] >= ground_y]
        
        if not grounded:
            return False
        
        # 着地時の爆発判定
        speed = math.hypot(self.vx, self.vy)
        exploded = False
        
        if speed > landing_speed:
            exploded = True
            
            # 強制転倒（12°以内なら13°に）
            angle_deg = math.degrees(self.angle) + 90
            if abs(angle_deg) <= 12:
                if angle_deg >= 0:
                    self.angle = math.radians(13 - 90)  # +13°
                else:
                    self.angle = math.radians(-13 - 90)  # -13°
        
        if len(grounded) == 1:
            _, dx, _ = grounded[0]
            angle_deg = math.degrees(self.angle) + 90
            if abs(dx) > self.height / 2 - 1:
                if angle_deg > 12:
                    self.rotation_speed += rotation_acceleration
                elif angle_deg < -12:
                    self.rotation_speed -= rotation_acceleration
                elif abs(angle_deg) <= 12:
                    if angle_deg > 0: 
                        self.rotation_speed -= rotation_acceleration
                    elif angle_deg < 0:
                        self.rotation_speed += rotation_acceleration
                self.rotation_speed *= rotation_friction
                self.angle += self.rotation_speed
                if abs(self.rotation_speed) < 0.00001:
                    self.rotation_speed = 0.0
                    if not exploded and not self.exploded_done:
                        self.angle = -math.pi / 2
            else:
                self.rotation_speed = 0
        else:
            self.rotation_speed = 0
        
        # 横転判定
        angle_deg = math.degrees(self.angle) + 90
        if angle_deg > 90 or angle_deg < -90:
            exploded = True
            self.fallen = True
            self.rotation_speed = 0
            self.vx = 0
            self.vy = 0
            return exploded
        
        # 地面に接地させる処理
        if len(grounded) == 1:
            anchor_pt, dx_anchor, dy_anchor = grounded[0]
        else:
            anchor_pt, dx_anchor, dy_anchor = min(grounded, key=lambda g: g[0][0])  # 左端を基準
        
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        self.x = anchor_pt[0] - (dx_anchor * cos_a - dy_anchor * sin_a)
        self.y = anchor_pt[1] - (dx_anchor * sin_a + dy_anchor * cos_a)
        
        self.vy = 0
        self.vx *= 0.95
        
        # 地面に密着させる補正
        corrected_corners = self.get_rotated_corners()
        min_dy = min(0, min(ground_y - pt[1] for pt, _, _ in corrected_corners))
        self.y += min_dy
        
        # 当たり判定点の更新
        self.update_hanging_point()
        
        return exploded
    
    def handle_fallen_state(self, ground_y):
        """
        転倒状態の処理
        
        Args:
            ground_y (int): 地面のY座標
        """
        if not self.fallen:
            return
        
        corners = self.get_rotated_corners()
        grounded = [(pt, dx, dy) for (pt, dx, dy) in corners if pt[1] >= ground_y]
        
        if grounded:
            if len(grounded) == 1:
                _, dx, _ = grounded[0]
                if abs(dx) > self.height / 2 - 1:
                    self.angle += self.rotation_speed
            elif len(grounded) >= 2:
                self.rotation_speed = 0
                # 地面に密着させる
                min_y = min(pt[1] for pt, _, _ in grounded)
                if min_y > ground_y:
                    self.y -= (min_y - ground_y)
        
        # 当たり判定点の更新
        self.update_hanging_point()
    
    def check_chopstick_collision(self, chopstick_x, chopstick_y, chopstick_width, chopstick_length):
        """
        チョップスティックとの衝突判定
        
        Args:
            chopstick_x (float): チョップスティックの左端X座標
            chopstick_y (float): チョップスティックのY座標
            chopstick_width (int): チョップスティックの幅
            chopstick_length (int): チョップスティックの長さ
            
        Returns:
            bool: 衝突している場合True
        """
        # すでにぶら下がっている場合は判定不要
        if self.hanging:
            return True
            
        # 機構破壊済みの場合は衝突判定を行わない
        if self.hanging_mechanism_broken:
            return False
            
        # チョップスティックの範囲内にぶら下がり判定点があるか
        in_x_range = chopstick_x <= self.hanging_point_x <= chopstick_x + chopstick_length
        in_y_range = chopstick_y <= self.hanging_point_y <= chopstick_y + chopstick_width
        
        if in_x_range and in_y_range:
            # 衝突時の速度を計算
            speed = math.hypot(self.vx, self.vy)
            
            # 速度が一定値以上の場合、ぶら下がり機構が破壊されたと判定
            MAX_SAFE_SPEED = 0.3  # 安全にぶら下がれる最大速度
            
            if speed > MAX_SAFE_SPEED:
                print(f"ぶら下がり機構破壊！速度: {speed:.2f}")
                
                # 速度を半分に減速して落下継続
                self.vx *= 0.5
                self.vy *= 0.5
                
                # 機構破壊フラグをセット
                self.hanging_mechanism_broken = True
                
                return False  # ぶら下がらない
            
            # 速度が十分に遅い場合、ぶら下がり成功
            self.hanging = True
            
            # 速度をリセット
            self.vx = 0
            self.vy = 0
            
            # ロケットの位置を調整（ぶら下がり判定点がチョップスティックの中央に来るように）
            chopstick_center_y = chopstick_y + chopstick_width / 2
            
            # ロケットの角度を調整（垂直下向き）
            self.angle = math.pi / 2
            
            # ロケットの位置を再計算
            offset = self.height * 0.1  # 上端から1/10の位置
            distance = self.height / 2 - offset  # 中心からの距離
            
            # 新しい位置を計算
            self.x = self.hanging_point_x
            self.y = chopstick_center_y + distance
            
            # ぶら下がり判定点を更新
            self.update_hanging_point()
            
            print(f"ぶら下がり成功！速度: {speed:.2f}")
            return True
        
        return False
    
    def rotate(self, angle_change):
        """
        ロケットを回転させる
        
        Args:
            angle_change (float): 回転角度の変化量（ラジアン）
        """
        # ぶら下がっている場合は回転を制限
        if self.hanging:
            # ぶら下がり状態では、振り子のような動きを許可
            # キー入力による回転は角速度に影響を与える
            self.pendulum_angle_velocity += angle_change * 0.1
            
            # 角速度の上限を設定
            max_velocity = 0.1
            if self.pendulum_angle_velocity > max_velocity:
                self.pendulum_angle_velocity = max_velocity
            elif self.pendulum_angle_velocity < -max_velocity:
                self.pendulum_angle_velocity = -max_velocity
        else:
            self.angle += angle_change
        
        self.update_hanging_point()
    
    def draw(self):
        """
        ロケットを描画
        """
        cx = self.x
        cy = self.y
        w2 = self.width / 2
        h2 = self.height / 2
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        
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
            offset_x = self.height * cos_a
            offset_y = self.height * sin_a
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
            # 第1段の中心位置から、ロケットの「向き」方向に半分の長さだけ移動すれば境界になる
            border_x = cx + h2 * cos_a
            border_y = cy + h2 * sin_a
            
            # 幅の半分で左右に広げて境界線を描く（カラーは白で）
            left_x = border_x - w2 * sin_a
            left_y = border_y + w2 * cos_a
            right_x = border_x + w2 * sin_a
            right_y = border_y - w2 * cos_a
            
            pyxel.line(int(left_x), int(left_y), int(right_x), int(right_y), 5)
        
        # === ぶら下がり判定点の描画は不要 ===
        # デバッグ表示を削除
