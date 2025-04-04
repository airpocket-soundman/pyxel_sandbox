import pyxel
import math

WIDTH = 160
HEIGHT = 120
GRAVITY = 0.3

def get_obb_vertices(cx, cy, w, h, angle_deg):
    angle = math.radians(angle_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    dx = w / 2
    dy = h / 2
    corners = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
    return [
        (
            cx + x * cos_a - y * sin_a,
            cy + x * sin_a + y * cos_a
        )
        for (x, y) in corners
    ]

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == dy == 0:
        return math.hypot(px - x1, py - y1), x1, y1
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy
    distance = math.hypot(px - nearest_x, py - nearest_y)
    return distance, nearest_x, nearest_y

def reflect_velocity(vx, vy, nx, ny):
    # 法線ベクトル(nx, ny)に沿って反射する
    dot = vx * nx + vy * ny
    rx = vx - 2 * dot * nx
    ry = vy - 2 * dot * ny
    return rx, ry

class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Circle vs OBB")
        self.ball_x = 80
        self.ball_y = 0
        self.vx = 0.5
        self.vy = 0
        self.radius = 5

        # 斜めのOBBの中心・サイズ・角度
        self.obb_cx = 80
        self.obb_cy = 80
        self.obb_w = 60
        self.obb_h = 10
        self.obb_angle = 30  # degrees

        pyxel.run(self.update, self.draw)

    def update(self):
        self.vy += GRAVITY
        self.ball_x += self.vx
        self.ball_y += self.vy

        # OBBの各辺とボールの最短距離を調べて衝突判定
        vertices = get_obb_vertices(self.obb_cx, self.obb_cy, self.obb_w, self.obb_h, self.obb_angle)
        for i in range(4):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % 4]
            dist, nx, ny = point_to_segment_distance(self.ball_x, self.ball_y, x1, y1, x2, y2)

            if dist < self.radius:
                # 法線ベクトル（辺の垂直方向）
                dx = x2 - x1
                dy = y2 - y1
                edge_len = math.hypot(dx, dy)
                if edge_len == 0:
                    continue
                nxn = -dy / edge_len
                nyn = dx / edge_len

                # 反射処理
                self.vx, self.vy = reflect_velocity(self.vx, self.vy, nxn, nyn)

                # 接触点の外側にボールを出す
                overlap = self.radius - dist
                self.ball_x += nxn * overlap
                self.ball_y += nyn * overlap
                break

    def draw(self):
        pyxel.cls(0)
        # ボール
        pyxel.circ(self.ball_x, self.ball_y, self.radius, 10)

        # OBB（斜めの板）
        vertices = get_obb_vertices(self.obb_cx, self.obb_cy, self.obb_w, self.obb_h, self.obb_angle)
        for i in range(4):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % 4]
            pyxel.line(int(x1), int(y1), int(x2), int(y2), 11)

App()
