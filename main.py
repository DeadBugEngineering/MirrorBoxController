from myhdl import *

m_state = enum('undefined',
               'init',
               'seek_home',
               'seek_home_timeout',
               'pos1_resting',
               'pos1_resting_error',
               'pos2_seeking_fast',
               'pos2_seeking_slow',
               'pos2_seeing_timeout',
               'pos2_resting',
               'pos2_resting_error',
               'pos1_seeking_fast',
               'pos1_seeking_slow',
               'pos1_seeking_timeout')

def MirrorBoxController(
        clk,                # input, main clock
        reset,              # input, main reset, active low
        state_reset,        # input, synchronous reset for the FSM state, active low
        state,              # output, state of the FSM
        hall1_not,          # input, raw signal of the hallsensor on position 1, active low
        hall2_not,          # input, raw signal of the hallsensor on position 2, active low
        drive2pos1_manual,  # input, driving this signal high sets the target_position to pos1, manual operation
        drive2pos2_manual,  # input, driving this signal high sets the target_position to pos2, manual operation
        drive2pos1_PIO,     # input, driving this signal high sets the target_position to pos1, PIO interface
        drive2pos2_PIO,     # input, driving this signal high sets the target_position to pos2, PIO interface
        lock_manual_input,  # input, driving this signal high disables the manual operation
        stepper_direction,  # output, direction signal for the stepper driver, 1==CW, 0==CCW
        stepper_steps,      # output, step signal for the stepper driver, each cycle equals one microstep
        osidjoid
):

    # definition of configuration parameters
    seek_home_counter_maxvalue = Signal(555)
    pos1_seeking_fast_counter_maxvalue = Signal(555)
    pos1_seeking_slow_counter_maxvalue = Signal(555)
    pos2_seeking_fast_counter_maxvalue = Signal(555)
    pos2_seeking_slow_counter_maxvalue = Signal(555)
    steps_per_second_fast = Signal(555)
    steps_per_second_slow = Signal(555)
    cw_direction = Signal(1)




    # definition of internal registers
    target_position = Signal(bool(0))   # 0==Pos1, 1==Pos2
    reg_pos1_seeking_fast_counter = Signal(0)
    reg_pos1_seeking_slow_counter = Signal(0)
    reg_pos2_seeking_fast_counter = Signal(0)
    reg_pos2_seeking_slow_counter = Signal(0)

    # definition of internal flags
    flag_stepper_enable = Signal(bool(0))   # enables the generation of the stepping signal for the stepper driver
    flag_stepper_speed = Signal(bool(0)     # 0==slow stepping speed, 1==fast stepping speed
    flag_seek_home_counter_top = Signal(bool(0))
    flag_seek_pos1_slow_counter_top = Signal(bool(0))    # 1 when seeking position 1 goes into timeout
    flag_seek_pos1_fast_counter_top = Signal(bool(0))    # 1 when time for fast seeking is up
    flag_seek_pos2_slow_counter_top = Signal(bool(0))    # 1 when seeking position 2 goes into timeout
    flag_seek_pos2_fast_counter_top = Signal(bool(0))    # 1 when time for fast seeking is up





    @always_seq(clk.posedge, reset=reset)
    def FSM():
        if state == m_state.init:
            state.next = m_state.seek_home

        elif state == m_state.seek_home:
            if seek_home_counter_top == Signal(bool(1)):
                state.next = m_state.seek_home_timeout

            elif (hall1 == Signal(bool(1)) and hall2 == Signal(bool(0))):
                state.next = m_state.pos1_resting

            else:
                state.next = m_state.seek_home

        elif state == m_state.seek_home_timeout:
            state.next = m_state.seek_home_timeout

        elif state == m_state.pos1_resting:
            if target_position == Signal(bool(1)):
                state.next = m_state.pos2_seeking_fast
            else:
                if hall1 == Signal(bool(0)):
                    state.next = m_state.pos1_resting
                else:
                    state.next = pos1_resting_error

        elif state == m_state.pos2_resting:
            if target_position == Signal(bool(0)):
                state.next = m_state.pos1_seeking_fast
            else:
                if hall2 == Signal(bool(0)):
                    state.next = m_state.pos2_resting
                else:
                    state.next = pos2_resting_error

        elif state == m_state.pos1_resting_error:
            state.next = m_state.pos1_resting_error

        elif state == m_state.pos2_resting_error:
            state.next = m_state.pos2_resting_error

        elif state == m_state.pos1_seeking_slow:
            if flag_seek_pos1_slow_counter_top == Signal(bool(1)):
                state.next = m_state.pos1_seeking_timeout
            else:
                state.next = m_state.pos1_seeking_slow

        elif state == m_state.pos2_seeking_slow:
            if flag_seek_pos2_slow_counter_top == Signal(bool(1)):
                state.next = m_state.pos2_seeking_timeout
            else:
                state.next = m_state.pos2_seeking_slow

        elif state == m_state.pos1_seeking_fast:
            if flag_seek_pos1_fast_counter_top == Signal(bool(1)):
                state.next = m_state.pos1_seeking_slow
            else:
                state.next = m_state.pos1_seeking_fast

        elif state == m_state.pos2_seeking_fast:
            if flag_seek_pos2_fast_counter_top == Signal(bool(1)):
                state.next = m_state.pos2_seeking_slow
            else:
                state.next = m_state.pos2_seeking_fast

        elif state == m_state.pos1_seeking_timeout:

        elif state == m_state.pos2_seeking_timeout:












































