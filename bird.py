from pico2d import load_image

# --- 스프라이트 시트(bird_animation.png, 918 x 506) 구조 ---
SHEET_HEIGHT = 506
CELL_WIDTH = 182    # 한 칸의 너비 (칸 시작 위치가 182px 간격으로 일정)
SHEET_COLUMNS = 5   # 한 줄에 5마리
FRAME_COUNT = 14    # 5 + 5 + 4 = 날갯짓 한 바퀴가 14장
# 줄마다 (위쪽 경계, 아래쪽 경계). 그림 좌표계(위가 0)이고 줄 사이는 빈 공간이다.
ROW_BOUNDS = [(0, 180), (180, 360), (360, 506)]

# 몸통(눈)을 기준점으로 쓰기 위한 값. 칸 안에서 눈의 x는 모든 프레임이 같고,
# y는 프레임마다 조금씩 다르다 (시트 전체 기준 y, 위가 0).
EYE_X_IN_CELL = 123
EYE_Y_ON_SHEET = [93, 92, 91, 88, 85,
                  254, 253, 253, 254, 256,
                  429, 431, 432, 433]


def frame_rect(index):
    """index번 프레임을 잘라낼 사각형 (left, bottom, width, height)과
    '잘라낸 사각형의 중심'이 '눈'에서 얼마나 떨어져 있는지 (center_dx, center_dy).
    pico2d 좌표(아래가 0). 새가 오른쪽을 볼 때 기준이다."""
    row, col = divmod(index, SHEET_COLUMNS)
    top, bottom_edge = ROW_BOUNDS[row]
    height = bottom_edge - top
    center_dx = CELL_WIDTH / 2 - EYE_X_IN_CELL
    center_dy = EYE_Y_ON_SHEET[index] - (top + height / 2)
    return col * CELL_WIDTH, SHEET_HEIGHT - bottom_edge, CELL_WIDTH, height, center_dx, center_dy


# 매 프레임 계산하지 않도록 모듈을 불러올 때 14장을 한 번에 계산해 둔다
FRAMES = [frame_rect(i) for i in range(FRAME_COUNT)]


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
        left, bottom, w, h, center_dx, center_dy = FRAMES[int(self.frame)]
        # (self.x, self.y)가 눈 위치가 되도록 사각형 중심을 옮겨서 그린다
        Bird.image.clip_draw(left, bottom, w, h, self.x + center_dx, self.y + center_dy)
