from pico2d import load_image, get_canvas_width

import game_framework

# --- 스프라이트 시트(bird_animation.png, 918 x 506) 구조 ---
SHEET_HEIGHT = 506
CELL_WIDTH = 182    # 한 칸의 너비 (칸 시작 위치가 182px 간격으로 일정)
SHEET_COLUMNS = 5   # 한 줄에 5마리
FRAME_COUNT = 14    # 5 + 5 + 4 = 날갯짓 한 바퀴가 14장
# 줄마다 (위쪽 경계, 아래쪽 경계). 그림 좌표계(위가 0)이고 줄 사이는 빈 공간이다.
ROW_BOUNDS = [(0, 180), (180, 360), (360, 506)]
# --- 비행 속도 (단위 변환: km/h -> m/min -> m/s -> pixel/s) ---
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel = 30 cm
FLIGHT_SPEED_KMPH = 36.0        # 새떼의 순항 속도
FLIGHT_SPEED_MPM = FLIGHT_SPEED_KMPH * 1000.0 / 60.0
FLIGHT_SPEED_MPS = FLIGHT_SPEED_MPM / 60.0
FLIGHT_SPEED_PPS = FLIGHT_SPEED_MPS * PIXEL_PER_METER

# --- 날갯짓 속도 ---
# 날개를 한 바퀴(14프레임) 젓는 동안 새가 날아가는 거리를 정해 두면,
# 비행 속도로부터 1초당 몇 프레임을 넘겨야 하는지가 정해진다.
WINGBEAT_DISTANCE_M = 5.0
FLIGHT_FRAMES_PER_SECOND = FLIGHT_SPEED_MPS / WINGBEAT_DISTANCE_M * FRAME_COUNT  # 10 / 5 * 14 = 28

# 눈에서 꼬리/날개 끝까지 가장 먼 거리: 이만큼은 화면 안에 남겨야 잘리지 않는다
BIRD_BACK_EXTENT = 125


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


# --- V자 편대 ---
FORMATION_PAIRS = 3       # 리더 뒤로 3줄 (줄마다 위/아래 한 마리씩)
FORMATION_SPACING_X = 90  # 한 줄 뒤로 물러나는 거리
FORMATION_SPACING_Y = 36  # 한 줄 뒤로 갈수록 위/아래로 벌어지는 거리


class Bird:
    image = None  # 모든 새가 공유하는 스프라이트 시트 (한 번만 로딩)

    def __init__(self, x, y, scale=0.5):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')
        self.x, self.y = x, y
        self.frame = 0
        self.dir = 1  # 1: 오른쪽, -1: 왼쪽
        self.scale = scale

    def update(self):
        # 프레임 번호도 실수로 누적한다: 경과 시간 x 초당 프레임 수
        self.frame = (self.frame + FLIGHT_FRAMES_PER_SECOND * game_framework.frame_time) % FRAME_COUNT
        # 이동 거리 = 속도 x 경과 시간
        self.x += self.dir * FLIGHT_SPEED_PPS * game_framework.frame_time
        # 화면 양 끝에서는 넘어간 만큼 되돌아오며(반사) 방향을 바꾼다
        margin = BIRD_BACK_EXTENT * self.scale
        left_limit = margin
        right_limit = get_canvas_width() - margin
        if self.x > right_limit:
            self.x = 2 * right_limit - self.x
            self.dir = -1
        elif self.x < left_limit:
            self.x = 2 * left_limit - self.x
            self.dir = 1

    def draw(self):
        left, bottom, w, h, center_dx, center_dy = FRAMES[int(self.frame)]
        # (self.x, self.y)가 눈 위치가 되도록 사각형 중심을 옮겨서 그린다
        # 왼쪽을 볼 때는 좌우반전되므로 눈에서 중심까지의 x 거리도 반대가 된다
        x = self.x + center_dx * self.dir * self.scale
        y = self.y + center_dy * self.scale
        draw_w, draw_h = int(w * self.scale), int(h * self.scale)
        if self.dir == 1:
            Bird.image.clip_draw(left, bottom, w, h, x, y, draw_w, draw_h)
        else:
            Bird.image.clip_composite_draw(left, bottom, w, h, 0, 'h', x, y, draw_w, draw_h)


def make_v_formation(leader_x, leader_y):
    """오른쪽을 보고 나는 V자 편대(리더 1마리 + 뒤쪽 6마리)를 만들어 돌려준다."""
    birds = [Bird(leader_x, leader_y)]
    for k in range(1, FORMATION_PAIRS + 1):
        for side in (+1, -1):
            birds.append(Bird(leader_x - k * FORMATION_SPACING_X,
                              leader_y + side * k * FORMATION_SPACING_Y))
    return birds
