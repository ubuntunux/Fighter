import numpy as np

from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton


class GameClient(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.player = None
        self.jump = False
        self.vel = 0.0

        self.models = {}

    def initialize(self, core_manager):
        logger.info("GameClient::initialize")

        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager

        player_walk = self.resource_manager.get_model("player_walk")
        player_jump = self.resource_manager.get_model("player_jump")

        if player_walk is not None:
            main_camera = self.scene_manager.main_camera
            pos = main_camera.transform.pos - main_camera.transform.front * 5.0
            self.player = self.scene_manager.add_object(model=player_walk, pos=pos)
            self.player.transform.set_scale(0.5)

        self.models['walk'] = player_walk
        self.models['jump'] = player_jump

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

        move_speed = 10.0 * delta
        rotation_speed = 0.3141592 * delta
        move = False

        if keydown[Keyboard.W] or self.game_backend.wheel_up:
            self.player.transform.set_yaw(-1.57079)
            move = True
        elif keydown[Keyboard.S] or self.game_backend.wheel_down:
            self.player.transform.set_yaw(1.57079)
            move = True

        if keydown[Keyboard.A]:
            self.player.transform.set_yaw(0.0)
            move = True
        elif keydown[Keyboard.D]:
            self.player.transform.set_yaw(3.141592)
            move = True

        if move:
            self.player.transform.move_front(move_speed)

        # Jump
        player_pos = self.player.transform.get_pos()

        if not self.jump and keydown[Keyboard.SPACE]:
            self.jump = True
            self.vel = 0.5

        if self.jump or 0.0 < player_pos[1]:
            self.vel -= 1.0 * delta
            self.player.transform.move_y(self.vel)
            self.player.animation_model = self.models['jump']
        else:
            self.player.animation_model = self.models['walk']

        if player_pos[1] < 0.0:
            player_pos[1] = 0.0
            self.vel = 0.0
            self.jump = False

        camera.transform.set_pos(player_pos)
        camera.transform.move_up(5.0)
        camera.transform.move_front(10.0)

    def update(self, delta):
        self.update_player(delta)
