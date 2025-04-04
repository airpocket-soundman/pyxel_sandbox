import pyxel
import math

WIDTH = 160
HEIGHT = 120
SUBSTEPS = 4  # サブステップ数

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
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        nx = -dy / length
        ny = dx / length
        axes.append((nx, ny))
    return axes

def project(vertices, axis):
    dots = [x * axis[0] + y * axis[1] for x, y in vertices]
    return min(dots), max(dots)

def overlap(min1, max1, min2, max2):
    return not (max1 < min2 or max2 < min1), min(max1, max2) - max(min1, min2)

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1), x1, y1
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    dist = math.hypot(px - closest_x, py - closest_y)
    return dist, closest_x, closest_y

class OBB:
    def __init__(self, cx, cy, w, h, angle=0.0, mass=1.0):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.angle = math.radians(angle)
        self.vx = 0
        self.vy = 0
        self.omega = 0
        self.mass = mass
        self.inertia = (1 / 12) * self.mass * (self.w ** 2 + self.h ** 2)

    def move(self, dt):
        self.cx += self.vx * dt
        self.cy += self.vy * dt
        self.angle += self.omega * dt
        self.omega *= 0.98  # 摩擦減衰

    def apply_torque(self, torque):
        alpha = torque / self.inertia
        self.omega += alpha

    def get_vertices(self):
        return get_obb_vertices(self.cx, self.cy, self.w, self.h, math.degrees(self.angle))

    def radius(self):
        return math.hypot(self.w, self.h) / 2

class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="OBB Collision (Substeps Fix)")
        self.obb1 = OBB(60, 60, 40, 20, angle=10)
        self.obb2 = OBB(120, 50, 40, 20, angle=-5)
        self.obb2.vx = -4.0  # 高速でもトン抜けしない！
        self.obb2.vy = 0.7
        pyxel.run(self.update, self.draw)

    def update(self):
        for _ in range(SUBSTEPS):
            self.simulate(1 / SUBSTEPS)

    def simulate(self, dt):
        self.obb1.move(dt)
        self.obb2.move(dt)

        v1 = self.obb1.get_vertices()
        v2 = self.obb2.get_vertices()

        is_colliding, overlap_amt, axis, contact_point = self.sat_collision_response(v1, v2)

        if is_colliding:
            m1 = self.obb1.mass
            m2 = self.obb2.mass

            rvx = self.obb2.vx - self.obb1.vx
            rvy = self.obb2.vy - self.obb1.vy
            rel_vel = rvx * axis[0] + rvy * axis[1]

            if rel_vel < 0:
                impulse = (2 * rel_vel) / (1/m1 + 1/m2)
                ix = impulse * axis[0]
                iy = impulse * axis[1]

                self.obb1.vx += ix / m1
                self.obb1.vy += iy / m1
                self.obb2.vx -= ix / m2
                self.obb2.vy -= iy / m2

                for obb, sign in zip([self.obb1, self.obb2], [+1, -1]):
                    r_x = contact_point[0] - obb.cx
                    r_y = contact_point[1] - obb.cy
                    torque = r_x * iy - r_y * ix
                    obb.apply_torque(sign * torque)

                # 補正強化（半分ずつ押し戻す）
                correction = overlap_amt
                self.obb1.cx -= axis[0] * (correction / 2)
                self.obb1.cy -= axis[1] * (correction / 2)
                self.obb2.cx += axis[0] * (correction / 2)
                self.obb2.cy += axis[1] * (correction / 2)

        for obb in [self.obb1, self.obb2]:
            r = obb.radius()
            if obb.cx - r < 0 or obb.cx + r > WIDTH:
                obb.vx *= -1
                obb.cx = max(r, min(WIDTH - r, obb.cx))
            if obb.cy - r < 0 or obb.cy + r > HEIGHT:
                obb.vy *= -1
                obb.cy = max(r, min(HEIGHT - r, obb.cy))

            speed = math.hypot(obb.vx, obb.vy)
            if speed > 6:
                scale = 6 / speed
                obb.vx *= scale
                obb.vy *= scale
            if abs(obb.omega) > 0.6:
                obb.omega *= 0.95

    def sat_collision_response(self, verts1, verts2):
        axes1 = get_axes(verts1)
        axes2 = get_axes(verts2)
        smallest_overlap = float("inf")
        best_axis = (0, 0)
        contact_point = verts2[0]

        for axis in axes1 + axes2:
            min1, max1 = project(verts1, axis)
            min2, max2 = project(verts2, axis)
            is_ol, ol_amt = overlap(min1, max1, min2, max2)
            if not is_ol:
                return False, 0, (0, 0), (0, 0)
            if ol_amt < smallest_overlap:
                smallest_overlap = ol_amt
                best_axis = axis

        best_distance = float("inf")
        for px, py in verts2:
            for i in range(4):
                x1, y1 = verts1[i]
                x2, y2 = verts1[(i + 1) % 4]
                dist, _, _ = point_to_segment_distance(px, py, x1, y1, x2, y2)
                if dist < best_distance:
                    best_distance = dist
                    contact_point = (px, py)

        return True, smallest_overlap, best_axis, contact_point

    def draw(self):
        pyxel.cls(0)
        for obb, color in zip([self.obb1, self.obb2], [11, 10]):
            verts = obb.get_vertices()
            for i in range(4):
                x1, y1 = verts[i]
                x2, y2 = verts[(i + 1) % 4]
                pyxel.line(int(x1), int(y1), int(x2), int(y2), color)

App()
