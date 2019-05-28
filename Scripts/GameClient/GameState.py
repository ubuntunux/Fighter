from enum import Enum

from PyEngine3D.Utilities import StateMachine, StateItem


class KEY_FLAG:
    NONE = 0
    MOVE = 1 << 0
    JUMP = 1 << 1
    PUNCH = 1 << 2
    KICK = 1 << 3


class STATES:
    NONE = 0
    IDLE = 1
    MOVE = 2
    JUMP = 3
    JUMP_KICK = 4
    PUNCH = 5
    KICK = 6


class StateInfo:
    def __init__(self):
        self.player = None
        self.animation_meshes = None
        self.on_ground = None
        self.key_flag = None

    def set_info(self, player, animation_meshes, on_ground, key_flag):
        self.player = player
        self.animation_meshes = animation_meshes
        self.on_ground = on_ground
        self.key_flag = key_flag


class StateBase(StateItem):
    enable_rotation = False
    enable_jump = False
    enable_move = False
    enable_punch = False
    enable_kick = False


class StateNone(StateBase):
    def on_update(self, state_info=None):
        self.state_manager.set_state(STATES.IDLE, state_info)


class StateIdle(StateBase):
    enable_rotation = True
    enable_jump = True
    enable_move = True
    enable_punch = True
    enable_kick = True

    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['idle'], loop=True, speed=0.3, blend_time=0.1)

    def on_update(self, state_info=None):
        if not state_info.on_ground:
            self.state_manager.set_state(STATES.JUMP, state_info)
        elif state_info.key_flag & KEY_FLAG.MOVE:
            self.state_manager.set_state(STATES.MOVE, state_info)
        elif state_info.key_flag & KEY_FLAG.PUNCH:
            self.state_manager.set_state(STATES.PUNCH, state_info)
        elif state_info.key_flag & KEY_FLAG.KICK:
            self.state_manager.set_state(STATES.KICK, state_info)


class StateMove(StateBase):
    enable_rotation = True
    enable_jump = True
    enable_move = True
    enable_punch = True
    enable_kick = True

    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['walk'], loop=True, blend_time=0.1)

    def on_update(self, state_info=None):
        if not state_info.on_ground:
            self.state_manager.set_state(STATES.JUMP, state_info)
        elif not (state_info.key_flag & KEY_FLAG.MOVE):
            self.state_manager.set_state(STATES.IDLE, state_info)
        elif state_info.key_flag & KEY_FLAG.PUNCH:
            self.state_manager.set_state(STATES.PUNCH, state_info)
        elif state_info.key_flag & KEY_FLAG.KICK:
            self.state_manager.set_state(STATES.KICK, state_info)


class StateJump(StateBase):
    enable_rotation = True
    enable_move = True
    enable_punch = True
    enable_kick = True

    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['jump'], loop=False, speed=1.0, blend_time=0.1)

    def on_update(self, state_info=None):
        if state_info.on_ground:
            self.state_manager.set_state(STATES.IDLE, state_info)
        elif state_info.key_flag & KEY_FLAG.PUNCH or state_info.key_flag & KEY_FLAG.KICK:
            self.state_manager.set_state(STATES.JUMP_KICK, state_info)


class StateJumpKick(StateBase):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['jump_kick'], loop=False, speed=1.0, blend_time=0.1)

    def on_update(self, state_info=None):
        if state_info.on_ground:
            self.state_manager.set_state(STATES.IDLE, state_info)


class StatePunch(StateBase):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['punch'], start_time=0.5, end_time=1.0, loop=False, speed=1.0, blend_time=0.1)

    def on_update(self, state_info=None):
        if state_info.player.is_animation_end:
            self.state_manager.set_state(STATES.IDLE, state_info)


class StateKick(StateBase):
    def on_enter(self, state_info=None):
        if state_info is not None:
            state_info.player.set_animation(state_info.animation_meshes['kick'], loop=False, speed=1.0, blend_time=0.1)

    def on_update(self, state_info=None):
        if state_info.player.is_animation_end:
            self.state_manager.set_state(STATES.IDLE, state_info)


class GameStateManager(StateMachine):
    def __init__(self, *args, **kargs):
        StateMachine.__init__(self, *args, **kargs)
        self.state_info = StateInfo()
        self.add_state(StateNone, STATES.NONE)
        self.add_state(StateIdle, STATES.IDLE)
        self.add_state(StateMove, STATES.MOVE)
        self.add_state(StateJump, STATES.JUMP)
        self.add_state(StateJumpKick, STATES.JUMP_KICK)
        self.add_state(StatePunch, STATES.PUNCH)
        self.add_state(StateKick, STATES.KICK)

        self.set_state(STATES.NONE)

    def update_state(self, player, animation_meshes, on_ground, key_flag):
        self.state_info.set_info(player, animation_meshes, on_ground, key_flag)
        StateMachine.update_state(self, self.state_info)
