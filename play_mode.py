import random

from pico2d import *
import game_world
import game_framework
from boy import Boy
from grass import Grass
from bird import Bird, FRAME_COUNT

boy = None


def handle_events():


    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        else:
            boy.handle_event(event)


def init():
    global boy

    boy = Boy()
    game_world.add_oject(boy)

    grass = Grass()
    game_world.add_oject(grass, 0)

    # 새 10마리를 하나씩 따로 만들어 game_world에 추가한다 (위치, 방향, 크기, 속도가 모두 제각각)
    for _ in range(10):
        bird = Bird(random.randint(150, 1450), random.randint(340, 560),
                    random.choice((-1, 1)),
                    random.uniform(0.4, 0.6),
                    random.uniform(28.0, 44.0),
                    random.uniform(0, FRAME_COUNT))
        game_world.add_oject(bird)


def pause():
    boy.pause()


def resume():
    pass


def finish():
    global boy
    game_world.clear()
    boy = None


def update():
    game_world.update()

def render():
    clear_canvas()
    game_world.render()
    update_canvas()









