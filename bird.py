"""새떼 비행 애니메이션.

bird_animation.png(918 x 506)에는 날갯짓 한 바퀴를 이루는 14장이 5 + 5 + 4칸으로 들어 있다.
새가 '정확하게' 날도록 아래 네 가지 원칙으로 만들었다.

1. 그림은 눈을 기준점으로 맞춘다.
   프레임마다 날개 모양이 달라 잘라낸 사각형의 중심이 흔들린다. 눈은 몸통에 붙어 있으므로
   프레임별 눈 좌표를 재 두고 (self.x, self.y)가 항상 눈 위치가 되게 그린다.
   그러면 몸통은 제자리에 있고 날개만 움직인다. 왼쪽을 볼 때(좌우반전)는 눈에서 사각형
   중심까지의 x 거리도 반대로 뒤집는다.

2. 모든 움직임을 frame_time(경과 시간)으로 계산한다. 틱마다 고정값을 더하지 않는다.
   이동 거리   = 속도(pixel/s)   x frame_time
   프레임 증가 = 초당 프레임 수  x frame_time
   그래서 컴퓨터가 빠르든 느리든 새가 같은 속도로 날고 같은 속도로 날개를 젓는다.

3. 날갯짓 속도는 비행 속도에서 계산한다 (속도와 날갯짓이 어긋나지 않게).
   36km/h = 10m/s 이고 날갯짓 한 바퀴에 5m를 날아가므로 1초에 2바퀴, 즉 28프레임/초다.
   게임이 30프레임/초 안팎이면 한 틱에 약 0.93장씩 넘어가 프레임을 건너뛰지 않는다.

4. 좌우 반복 비행은 화면 경계에서의 반사로 만든다.
   경계를 넘은 만큼 안쪽으로 되돌리고 방향을 바꾼다. 경계는 눈에서 꼬리/날개 끝까지의 거리
   (BIRD_BACK_EXTENT x scale)만큼 안쪽으로 잡아 새가 화면 밖에서 잘리지 않는다.
   새떼의 속도는 모두 같으므로 한 마리씩 차례로 반사되어도 V자 편대가 그대로 유지된다.
"""
import math
import random

from pico2d import load_image, get_canvas_width

import game_framework

# ---------------------------------------------------------------------------
# 1. 스프라이트 시트 구조 (bird_animation.png, 918 x 506)
# ---------------------------------------------------------------------------
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
# 눈에서 꼬리/날개 끝까지 가장 먼 거리: 이만큼은 화면 안에 남겨야 잘리지 않는다
BIRD_BACK_EXTENT = 125


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

# ---------------------------------------------------------------------------
# 2. 비행 속도 (단위 변환: km/h -> m/min -> m/s -> pixel/s)
# ---------------------------------------------------------------------------
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel = 30 cm
FLIGHT_SPEED_KMPH = 36.0        # 새떼의 순항 속도
FLIGHT_SPEED_MPM = FLIGHT_SPEED_KMPH * 1000.0 / 60.0
FLIGHT_SPEED_MPS = FLIGHT_SPEED_MPM / 60.0
FLIGHT_SPEED_PPS = FLIGHT_SPEED_MPS * PIXEL_PER_METER   # 약 333 pixel/s

# 창을 끌거나 잠깐 멈춘 뒤에 frame_time이 커져도 한 번에 튀지 않도록 상한을 둔다
MAX_FRAME_TIME = 0.1

# ---------------------------------------------------------------------------
# 3. 날갯짓 속도
# ---------------------------------------------------------------------------
# 날개를 한 바퀴(14프레임) 젓는 동안 새가 날아가는 거리를 정해 두면,
# 비행 속도로부터 1초당 몇 프레임을 넘겨야 하는지가 정해진다.
WINGBEAT_DISTANCE_M = 5.0
FLIGHT_FRAMES_PER_SECOND = FLIGHT_SPEED_MPS / WINGBEAT_DISTANCE_M * FRAME_COUNT  # 10 / 5 * 14 = 28

# 날갯짓에 맞춘 상하 움직임: 날개가 내려가는 구간(프레임 5~9 부근)에서 양력으로 몸이
# 위로 올라가고, 날개를 올리는 구간에서 조금 내려간다. 날갯짓과 같은 주기의 사인파다.
BOB_AMPLITUDE = 6.0     # 위아래로 움직이는 폭 (pixel)
BOB_PHASE_FRAME = 3.5   # 사인파가 0에서 올라가기 시작하는 프레임 -> 7번 프레임에서 가장 높다

# ---------------------------------------------------------------------------
# 4. V자 편대
# ---------------------------------------------------------------------------
FORMATION_PAIRS = 3          # 리더 뒤로 3줄 (줄마다 위/아래 한 마리씩)
FORMATION_SPACING_X = 90     # 한 줄 뒤로 물러나는 거리
FORMATION_SPACING_Y = 36     # 한 줄 뒤로 갈수록 위/아래로 벌어지는 거리
LEADER_SCALE = 0.55          # 리더의 크기
FORMATION_SCALE_STEP = 0.03  # 한 줄 뒤로 갈수록 작아지는 정도 (원근감)


class Bird:
    image = None  # 모든 새가 공유하는 스프라이트 시트 (한 번만 로딩)

    def __init__(self, x, y, scale=0.5, phase=0.0):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')
        self.x, self.y = x, y
        self.base_y = y  # 날아다니는 높이(상하 움직임의 중심)
        self.frame = phase % FRAME_COUNT  # 날갯짓이 시작되는 지점
        self.dir = 1  # 1: 오른쪽, -1: 왼쪽
        self.scale = scale

    def update(self):
        dt = min(game_framework.frame_time, MAX_FRAME_TIME)
        # 프레임 번호도 실수로 누적한다: 경과 시간 x 초당 프레임 수
        self.frame = (self.frame + FLIGHT_FRAMES_PER_SECOND * dt) % FRAME_COUNT
        self.y = self.base_y + BOB_AMPLITUDE * math.sin(
            2 * math.pi * (self.frame - BOB_PHASE_FRAME) / FRAME_COUNT)
        # 이동 거리 = 속도 x 경과 시간
        self.x += self.dir * FLIGHT_SPEED_PPS * dt
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
    birds = [Bird(leader_x, leader_y, LEADER_SCALE, random.uniform(0, FRAME_COUNT))]
    for k in range(1, FORMATION_PAIRS + 1):
        for side in (+1, -1):
            birds.append(Bird(leader_x - k * FORMATION_SPACING_X,
                              leader_y + side * k * FORMATION_SPACING_Y,
                              LEADER_SCALE - k * FORMATION_SCALE_STEP,
                              random.uniform(0, FRAME_COUNT)))
    return birds
