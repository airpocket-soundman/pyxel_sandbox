            if self.draw_stage2:
                # 第1段の中心位置から、ロケットの「向き」方向に半分の長さだけ移動すれば境界になる
                border_x = cx + h2 * cos_a
                border_y = cy + h2 * sin_a

                # 幅の半分で左右に広げて境界線を描く（カラーは白で）
                left_x = border_x - w2 * sin_a
                left_y = border_y + w2 * cos_a
                right_x = border_x + w2 * sin_a
                right_y = border_y - w2 * cos_a

                pyxel.line(int(left_x), int(left_y), int(right_x), int(right_y), pyxel.COLOR_WHITE)