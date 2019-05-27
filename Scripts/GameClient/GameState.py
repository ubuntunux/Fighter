from enum import Enum

from PyEngine3D.Utilities import StateMachine, StateItem


class STATES(Enum):
    NONE = 0
    IDLE = 1
    MOVE = 2
    JUMP = 3
    PUNCH = 4
    KICK = 5


class StateInfo:
    def __init__(self):
        self.player = None
        self.animation_meshes = None
        self.on_ground = None
        self.move = None

    def set_info(self, player, animation_meshes, on_ground, move):
        self.player = player
        self.animation_meshes = animation_meshes
        self.on_ground = on_ground
        self.move = move


class StateItemNone(StateItem):
    def on_update(self, state_info=None):
        self.state_manager.set_state(STATES.IDLE, state_info)


class StateItemIdle(StateItem):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['idle'], loop=True, speed=0.3, blend_time=0.1)

    def on_update(self, state_info=None):
        if not state_info.on_ground:
            self.state_manager.set_state(STATES.JUMP, state_info)
        elif state_info.move:
            self.state_manager.set_state(STATES.MOVE, state_info)


class StateItemMove(StateItem):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['walk'], loop=True, blend_time=0.1)

    def on_update(self, state_info=None):
        if not state_info.on_ground:
            self.state_manager.set_state(STATES.JUMP, state_info)
        elif not state_info.move:
            self.state_manager.set_state(STATES.IDLE, state_info)


class StateItemJump(StateItem):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['jump'], loop=False, speed=1.0, blend_time=0.1)

    def on_update(self, state_info=None):
        if state_info.on_ground:
            self.state_manager.set_state(STATES.IDLE, state_info)


class GameStateManager(StateMachine):
    def __init__(self, *args, **kargs):
        StateMachine.__init__(self, *args, **kargs)
        self.state_info = StateInfo()
        self.add_state(StateItemNone, STATES.NONE)
        self.add_state(StateItemIdle, STATES.IDLE)
        self.add_state(StateItemMove, STATES.MOVE)
        self.add_state(StateItemJump, STATES.JUMP)

        self.set_state(STATES.NONE)

    def update_state(self, player, animation_meshes, on_ground, move):
        self.state_info.set_info(player, animation_meshes, on_ground, move)
        StateMachine.update_state(self, self.state_info)
