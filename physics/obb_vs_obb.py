import pyxel
import math

WIDTH = 160
HEIGHT = 120

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

def get_axes(vertices):
    axes = []
    for i in range(4):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % 4]
        dx = x2 - x1
        dy = y2 - y1
        # 法線（直交ベクトル）
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        nx = -dy / length
        ny = dx / length
        axes.append((nx, ny))
    return axes

def project(vertices, axis):
    min_proj = max_proj = None
    for x, y in vertices:
        dot = x * axis[0] + y * axis[1]
        if min_proj is None or dot < min_proj:
            min_proj = dot
        if max_proj is None or dot > max_proj:
            max_proj = dot
    return min_proj, max_proj

def overlap(min1, max1, min2, max2):
    return not (max1 < min2 or max2 < min1)

def sat_collision(obb1, obb2):
    axes1 = get_axes(obb1)
    axes2 = get_axes(obb2)
    for axis in axes1 + axes2:
        min1, max1 = project(obb1, axis)
        min2, max2 = project(obb2, axis)
        if not overlap(min1, max1, min2, max2):
            return False
    return True

class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="OBB vs OBB - SAT")
        self.angle1 = 30
        self.angle2 = 0
        pyxel.run(self.update, self.draw)

    def update(self):
        # OBB2をマウス位置に移動
        self.cx1 = 60
        self.cy1 = 60
        self.cx2 = pyxel.mouse_x
        self.cy2 = pyxel.mouse_y

        # 左右キーで角度変更（回転）
        if pyxel.btn(pyxel.KEY_LEFT):
            self.angle2 -= 2
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.angle2 += 2

    def draw(self):
        pyxel.cls(0)

        # OBBの頂点
        obb1 = get_obb_vertices(self.cx1, self.cy1, 40, 20, self.angle1)
        obb2 = get_obb_vertices(self.cx2, self.cy2, 40, 20, self.angle2)

        # 衝突判定
        is_colliding = sat_collision(obb1, obb2)

        # 描画（衝突時は赤、そうでなければ緑）
        color1 = 8 if is_colliding else 11
        color2 = 9 if is_colliding else 10
        for i in range(4):
            x1, y1 = obb1[i]
            x2, y2 = obb1[(i + 1) % 4]
            pyxel.line(int(x1), int(y1), int(x2), int(y2), color1)

        for i in range(4):
            x1, y1 = obb2[i]
            x2, y2 = obb2[(i + 1) % 4]
            pyxel.line(int(x1), int(y1), int(x2), int(y2), color2)

        pyxel.text(5, 5, f"Angle2: {self.angle2}", 7)
        if is_colliding:
            pyxel.text(5, 15, "COLLISION!", pyxel.frame_count % 16)

App()
