import pyxel
from PIL import Image
import tempfile
import os

class App:
    def __init__(self):
        pyxel.init(256, 256, title="Resized Image Display")

        # 画像をPillowで読み込んでリサイズ（最大256x256）
        img = Image.open("airpocket.png").resize((256, 256))

        # 一時ファイルに保存（自動削除される）
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name)
            temp_path = tmp.name

        # Pyxelに画像を読み込ませる
        pyxel.image(0).load(0, 0, temp_path)

        # 一時ファイルを削除
        os.remove(temp_path)

        pyxel.run(self.update, self.draw)

    def update(self):
        pass

    def draw(self):
        pyxel.cls(0)
        pyxel.blt(0, 0, 0, 0, 0, 256, 256)

App()
