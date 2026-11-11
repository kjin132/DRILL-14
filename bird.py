from pico2d import load_image


class Bird:
    image = None  # 모든 새가 공유하는 스프라이트 시트 (한 번만 로딩)

    def __init__(self, x, y):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')
        self.x, self.y = x, y

    def update(self):
        pass

    def draw(self):
        # 시트 맨 위 줄의 첫 번째 새(182 x 180)를 그대로 그린다
        Bird.image.clip_draw(0, 326, 182, 180, self.x, self.y)
