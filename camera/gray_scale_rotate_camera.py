import pyxel
import cv2
import numpy as np
from PIL import Image
import tempfile
import os

class RotatingResolutionCameraApp:
    def __init__(self):
        pyxel.init(256, 256, title="Pyxel Cam: Rotation + Resolution")

        # グレースケールパレット（白→黒）
        for i, gray in enumerate(reversed([int(j * 255 / 15) for j in range(16)])):
            pyxel.colors[i] = (gray << 16) | (gray << 8) | gray

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # カスタム解像度リスト
        self.res_list = [24, 36, 48, 64, 72, 80, 96, 128, 160, 196, 224, 256]
        self.res_index = len(self.res_list) - 1  # 初期は最大（256）

        self.rotation_angle = 0.0  # 回転角度

        pyxel.run(self.update, self.draw)

    def update(self):
        # 解像度切替
        if pyxel.btnp(pyxel.KEY_UP):
            self.res_index = min(self.res_index + 1, len(self.res_list) - 1)
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.res_index = max(self.res_index - 1, 0)

        # 回転操作（押してる間だけ）
        if pyxel.btn(pyxel.KEY_LEFT):
            self.rotation_angle = (self.rotation_angle + 2) % 360
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.rotation_angle = (self.rotation_angle - 2) % 360

        # カメラ画像取得
        ret, frame = self.cap.read()
        if not ret:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.5)

        # 正方形にトリミング
        h, w = gray.shape
        if w > h:
            margin = (w - h) // 2
            square = gray[:, margin:margin + h]
        else:
            margin = (h - w) // 2
            square = gray[margin:margin + w, :]

        # PIL変換 → 解像度に縮小 → 回転 → 256×256に再拡大
        target_res = self.res_list[self.res_index]
        img_pil = Image.fromarray(square).resize((target_res, target_res), resample=Image.BILINEAR)
        img_pil = img_pil.rotate(self.rotation_angle, expand=False).resize((256, 256), resample=Image.NEAREST)

        # 減色 + パレット適用
        img_p = img_pil.convert("P", palette=Image.ADAPTIVE, colors=16)
        palette = [(int(i * 255 / 15),) * 3 for i in reversed(range(16))]
        flat_palette = sum(palette, ()) + (0,) * (768 - 48)
        img_p.putpalette(flat_palette)

        # 一時ファイル経由でPyxelにロード
        temp_path = os.path.join(tempfile.gettempdir(), "debug_palette_image.png")
        img_p.save(temp_path)
        pyxel.image(0).load(0, 0, temp_path)

        # Qで終了
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
            cv2.destroyAllWindows()

    def draw(self):
        pyxel.cls(0)
        pyxel.blt(0, 0, 0, 0, 0, 256, 256)

        # 情報表示
        res = self.res_list[self.res_index]
        pyxel.text(4, 4, f"RES: {res}x{res}", 7)
        pyxel.text(4, 14, f"ROT: {int(self.rotation_angle)} deg", 7)
        pyxel.text(4, 24, "↑↓ RES  ←→ ROT  Q QUIT", 6)

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()

RotatingResolutionCameraApp()
