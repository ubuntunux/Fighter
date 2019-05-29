import sys
import numpy as np

from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton, StateMachine, StateItem, Float3
from GameClient.GameState import *


GRAVITY = 20.0
JUMP_SPEED = 10.0
MOVE_SPEED = 6.0
BOUND_BOX_OFFSET = 0.1
EPSILON = sys.float_info.epsilon

KEY_FLAG_NONE = 0
KEY_FLAG_W = 1 << 0
KEY_FLAG_S = 1 << 1
KEY_FLAG_A = 1 << 2
KEY_FLAG_D = 1 << 3

key_map = dict()
key_map[KEY_FLAG_W] = -1.57079
key_map[KEY_FLAG_S] = 1.57079
key_map[KEY_FLAG_A] = 0.0
key_map[KEY_FLAG_D] = 3.141592
key_map[KEY_FLAG_W | KEY_FLAG_A] = -0.785395
key_map[KEY_FLAG_W | KEY_FLAG_D] = 3.926987
key_map[KEY_FLAG_S | KEY_FLAG_A] = 0.785395
key_map[KEY_FLAG_S | KEY_FLAG_D] = 2.356191


class GameClient(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.player = None
        self.enemy = None
        self.key_flag = KEY_FLAG.NONE
        self.on_ground = False
        self.velocity = Float3(0.0, 0.0, 0.0)
        self.animation_meshes = {}
        self.state_manager = GameStateManager()

    def initialize(self, core_manager):
        logger.info("GameClient::initialize")

        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager

        self.resource_manager.open_scene('stage')

        animation_list = ['avoid',
                          'elbow',
                          'falloff',
                          'grab_attack',
                          'grab_attack_hit',
                          'grab_attack_hit_loop',
                          'grab_attack_loop',
                          'heading',
                          'hit',
                          'idle',
                          'jump',
                          'jump_kick',
                          'kick',
                          'punch',
                          'standup',
                          'walk',
                          'lie_down']

        for key in animation_list:
            self.animation_meshes[key] = self.resource_manager.get_mesh("player_" + key)

        main_camera = self.scene_manager.main_camera
        pos = main_camera.transform.pos - main_camera.transform.front * 5.0
        player_model = self.resource_manager.get_model("player")
        self.player = self.scene_manager.add_object(model=player_model, pos=pos)
        # self.enemy = self.scene_manager.add_object(model=player_model, pos=pos)
        # self.player.transform.set_pos([0.0, -1.99, -11.0])
        self.player.transform.set_yaw(3.141592)
        self.player.transform.set_scale(0.45)
        self.velocity[...] = Float3(0.0, 0.0, 0.0)

        # self.enemy.transform.set_pos([0.0, -1.99, -11.0])
        # self.enemy.transform.set_yaw(3.141592)
        # self.enemy.transform.set_scale(0.45)

        # fix camera rotation
        main_camera.transform.set_rotation((0.0, 1.57079, 0.0))

    def exit(self):
        logger.info("GameClient::exit")
        self.scene_manager.delete_object(self.player.name)

    def update_player(self, delta):
        keydown = self.game_backend.get_keyboard_pressed()
        mouse_delta = self.game_backend.mouse_delta
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        camera = self.scene_manager.main_camera

        press_keys = 0

        if keydown[Keyboard.W]:
            press_keys |= KEY_FLAG_W
        elif keydown[Keyboard.S]:
            press_keys |= KEY_FLAG_S

        if keydown[Keyboard.A]:
            press_keys |= KEY_FLAG_A
        elif keydown[Keyboard.D]:
            press_keys |= KEY_FLAG_D

        self.key_flag = KEY_FLAG.NONE

        if press_keys in key_map:
            self.key_flag |= KEY_FLAG.MOVE

        if keydown[Keyboard.SPACE]:
            self.key_flag |= KEY_FLAG.JUMP

        if btn_left:
            self.key_flag |= KEY_FLAG.PUNCH

        if btn_right:
            self.key_flag |= KEY_FLAG.KICK

        state = self.state_manager.get_state()

        if (self.key_flag & KEY_FLAG.MOVE) and state.enable_rotation:
            self.player.transform.set_yaw(key_map[press_keys])

        if self.on_ground:
            if (self.key_flag & KEY_FLAG.JUMP) and state.enable_jump:
                self.on_ground = False
                self.velocity[1] = JUMP_SPEED

            if (self.key_flag & KEY_FLAG.MOVE) and state.enable_move:
                self.velocity[0] = self.player.transform.front[0] * MOVE_SPEED
                self.velocity[2] = self.player.transform.front[2] * MOVE_SPEED
            else:
                self.velocity[0] = 0.0
                self.velocity[2] = 0.0

        self.velocity[1] -= GRAVITY * delta

        old_player_pos = self.player.transform.get_pos().copy()
        move_vector = self.velocity * delta
        player_pos = old_player_pos + move_vector

        self.on_ground = False

        def compute_collide(i, old_position, position, move_vector, bound_box):
            j = (i + 1) % 3
            k = (i + 2) % 3

            def is_in_plane(index, ratio):
                if index == 1:
                    return bound_box.bound_min[index] < (old_position[index] + move_vector[index] * ratio + BOUND_BOX_OFFSET) < bound_box.bound_max[index]
                else:
                    return bound_box.bound_min[index] < (old_position[index] + move_vector[index] * ratio) < bound_box.bound_max[index]

            if move_vector[i] < 0.0 and position[i] <= bound_box.bound_max[i] <= old_position[i]:
                ratio = abs((bound_box.bound_max[i] - old_position[i]) / move_vector[i])
                if is_in_plane(j, ratio) and is_in_plane(k, ratio):
                    position[i] = bound_box.bound_max[i] + EPSILON
                    move_vector[i] = position[i] - old_position[i]
                    if 1 == i:
                        self.on_ground = True
            elif 0.0 < move_vector[i] and old_position[i] <= bound_box.bound_min[i] <= position[i]:
                ratio = abs((bound_box.bound_min[i] - old_position[i]) / move_vector[i])
                if is_in_plane(j, ratio) and is_in_plane(k, ratio):
                    position[i] = bound_box.bound_min[i] - EPSILON
                    move_vector[i] = position[i] - old_position[i]

        for collision_actor in self.scene_manager.collision_actors:
            for geometry_bound_box in collision_actor.get_geometry_bound_boxes():
                for i in range(3):
                    compute_collide(i, old_player_pos, player_pos, move_vector, geometry_bound_box)

        if self.on_ground:
            self.velocity[1] = 0.0

        self.state_manager.update_state(delta, self.player, self.animation_meshes, self.on_ground, self.key_flag)

        self.player.transform.set_pos(player_pos)
        camera.transform.set_pos(player_pos)
        camera.transform.move_up(5.0)
        camera.transform.move_front(10.0)

    def update(self, delta):
        self.update_player(delta)
