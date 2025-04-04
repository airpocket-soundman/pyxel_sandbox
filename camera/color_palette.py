import pyxel

class ShowColors:
    def __init__(self):
        pyxel.init(16 * 16, 40, title="Pyxel Color Palette (Visual)")
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def draw(self):
        pyxel.cls(0)
        for i in range(16):
            pyxel.rect(i * 16, 0, 16, 40, i)
            pyxel.text(i * 16 + 4, 16, "■", 7 if i != 7 else 0)  # 白の上には黒で描画

ShowColors()
