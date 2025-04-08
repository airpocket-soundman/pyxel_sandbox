import pyxel
import cv2
from PIL import Image
import tempfile
import os

class CameraApp:
    def __init__(self):
        pyxel.init(256, 256, title="USB Camera Cropped View")

        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        # カメラ解像度取得と表示
        width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"🎥 カメラ解像度: {width} x {height}")

        pyxel.run(self.update, self.draw)

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # BGR → RGB
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #img = frame
        h, w, _ = img.shape

        # 正方形に中央クロップ
        if w > h:
            margin = (w - h) // 2
            img_cropped = img[:, margin:margin + h]  # 横をカット
        else:
            margin = (h - w) // 2
            img_cropped = img[margin:margin + w, :]  # 縦をカット

        # Pillow Image に変換してリサイズ
        img_pil = Image.fromarray(img_cropped).resize((256, 256))

        # 一時ファイル保存
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img_pil.save(tmp.name)
            temp_path = tmp.name

        pyxel.image(0).load(0, 0, temp_path)
        os.remove(temp_path)

    def draw(self):
        pyxel.cls(0)
        pyxel.blt(0, 0, 0, 0, 0, 256, 256)

    def __del__(self):
        self.cap.release()

CameraApp()
