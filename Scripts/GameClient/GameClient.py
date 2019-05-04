import numpy as np

from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton, StateMachine, StateItem


class GameClient(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.player = None
        self.jump = False
        self.punch = False
        self.kick = False
        self.vel = 0.0

        self.animation_meshes = {}

    def initialize(self, core_manager):
        logger.info("GameClient::initialize")

        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager

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
        self.player.transform.set_scale(0.5)

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

        if not self.jump and keydown[Keyboard.SPACE]:
            self.jump = True
            self.vel = 0.5

        if btn_left:
            self.punch = True

        if btn_right:
            self.kick = True

        # Jump
        player_pos = self.player.transform.get_pos()

        def check_collide(point, box):
            for i in range(3):
                if point[i] < box.bound_min[i] or box.bound_max[i] < point[i]:
                    return False
            return True

        collide = False
        bound_box = self.player.bound_box
        for collision_actor in self.scene_manager.collision_actors:
            if check_collide([bound_box.bound_center[0], bound_box.bound_min[1], bound_box.bound_center[2]], collision_actor.bound_box):
                collide = True
                break

        if self.jump or not collide:
            self.vel -= 1.0 * delta
            self.player.transform.move_y(self.vel)
            self.player.set_animation(self.animation_meshes['jump'], loop=False, speed=1.0)
        elif move:
            self.player.set_animation(self.animation_meshes['walk'], loop=True)
        else:
            self.player.set_animation(self.animation_meshes['idle'], loop=True, speed=0.3)

        # if keydown[Keyboard.Q]:
        #     self.player.transform.move_y(1.0)
        # elif keydown[Keyboard.E]:
        #     self.player.transform.move_y(-1.0)

        if collide:
            self.vel = 0.0
            self.jump = False

        camera.transform.set_pos(player_pos)
        camera.transform.move_up(5.0)
        camera.transform.move_front(10.0)

    def update(self, delta):
        self.update_player(delta)
