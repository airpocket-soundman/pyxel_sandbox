    def draw_rotated_rocket(self):
        cx = self.rocket_x
        cy = self.rocket_y
        w2 = ROCKET_WIDTH / 2
        h2 = ROCKET_HEIGHT / 2

        sin_a = math.sin(self.rocket_angle)
        cos_a = math.cos(self.rocket_angle)

        # ここで dx = 縦方向、dy = 横方向 にする！
        corners = []
        for dx, dy in [(-h2, -w2), (h2, -w2), (h2, w2), (-h2, w2)]:
            x = cx + dx * cos_a - dy * sin_a
            y = cy + dx * sin_a + dy * cos_a
            corners.append((x, y))

        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            pyxel.line(int(x1), int(y1), int(x2), int(y2), pyxel.COLOR_WHITE)