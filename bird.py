from pico2d import load_image

# --- 스프라이트 시트(bird_animation.png, 918 x 506) 구조 ---
SHEET_HEIGHT = 506
CELL_WIDTH = 182    # 한 칸의 너비 (칸 시작 위치가 182px 간격으로 일정)
SHEET_COLUMNS = 5   # 한 줄에 5마리
FRAME_COUNT = 14    # 5 + 5 + 4 = 날갯짓 한 바퀴가 14장
# 줄마다 (위쪽 경계, 아래쪽 경계). 그림 좌표계(위가 0)이고 줄 사이는 빈 공간이다.
ROW_BOUNDS = [(0, 180), (180, 360), (360, 506)]


def frame_rect(index):
    """index번 프레임을 잘라낼 사각형 (left, bottom, width, height). pico2d 좌표(아래가 0)."""
    row, col = divmod(index, SHEET_COLUMNS)
    top, bottom_edge = ROW_BOUNDS[row]
    return col * CELL_WIDTH, SHEET_HEIGHT - bottom_edge, CELL_WIDTH, bottom_edge - top


class Bird:
    image = None  # 모든 새가 공유하는 스프라이트 시트 (한 번만 로딩)

    def __init__(self, x, y):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')
        self.x, self.y = x, y
        self.frame = 0

    def update(self):
        pass

    def draw(self):
        left, bottom, w, h = frame_rect(int(self.frame))
        Bird.image.clip_draw(left, bottom, w, h, self.x, self.y)
