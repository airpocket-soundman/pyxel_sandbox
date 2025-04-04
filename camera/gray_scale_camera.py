import pyxel
import cv2
import numpy as np
from PIL import Image
import tempfile
import os

class ResolutionEffectCameraApp:
    def __init__(self):
        pyxel.init(256, 256, title="Virtual Resolution Toggle (Clean Sizes)")

        # Pyxelの16階調グレースケールパレット（白→黒）
        for i, gray in enumerate(reversed([int(j * 255 / 15) for j in range(16)])):
            pyxel.colors[i] = (gray << 16) | (gray << 8) | gray

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # 解像度候補：きれいな16の倍数
        self.res_list = [24, 36, 48, 64, 72, 80, 96, 128, 160, 196, 224, 256]
        self.res_index = len(self.res_list) - 1  # 初期：256x256

        pyxel.run(self.update, self.draw)

    def update(self):
        # 解像度切り替え（↑：上げる、↓：下げる）
        if pyxel.btnp(pyxel.KEY_UP):
            self.res_index = min(self.res_index + 1, len(self.res_list) - 1)
            print(f"⬆ 解像度: {self.res_list[self.res_index]}x{self.res_list[self.res_index]}")
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.res_index = max(self.res_index - 1, 0)
            print(f"⬇ 解像度: {self.res_list[self.res_index]}x{self.res_list[self.res_index]}")

        ret, frame = self.cap.read()
        if not ret:
            return

        # グレースケール化 + 明るさ補正
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

        # ↓ここがポイント：選んだ解像度に縮小してから256×256に拡大
        target_res = self.res_list[self.res_index]
        img_pil = Image.fromarray(square).resize((target_res, target_res), resample=Image.BILINEAR)
        img_pil = img_pil.resize((256, 256), resample=Image.NEAREST)  # 粗さを維持

        # 減色（16色）＋ Pyxel用パレットに変換
        img_p = img_pil.convert("P", palette=Image.ADAPTIVE, colors=16)
        palette = [(int(i * 255 / 15),) * 3 for i in reversed(range(16))]
        flat_palette = sum(palette, ()) + (0,) * (768 - 48)
        img_p.putpalette(flat_palette)

        # 一時ファイル保存 → Pyxelに読み込み
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

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()

ResolutionEffectCameraApp()
