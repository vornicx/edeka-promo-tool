from PIL import Image, ImageDraw
from app.templates.base import BaseTemplate


class PosterA4Template(BaseTemplate):
    def __init__(self):
        super().__init__(2480, 3508)

    def create_layout(self, background: Image.Image) -> Image.Image:
        bg = background.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self.canvas = bg.copy()
        self.draw = ImageDraw.Draw(self.canvas)
        return self.canvas


class PosterA5Template(BaseTemplate):
    def __init__(self):
        super().__init__(1748, 2480)

    def create_layout(self, background: Image.Image) -> Image.Image:
        bg = background.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self.canvas = bg.copy()
        self.draw = ImageDraw.Draw(self.canvas)
        return self.canvas
