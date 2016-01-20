from myhdl import *

# definition of constants / configuration parameters
c_not_reached = 0
c_reached = 1
c_direction_pos1 = 0
c_direction_pos2 = 1
c_position_pos1 = 0
c_position_pos2 = 1
c_speed_slow = 0
c_speed_fast = 1
c_home_seeking_slow_counter_maxvalue = 10
c_pos1_seeking_fast_counter_maxvalue = 10
c_pos1_seeking_slow_counter_maxvalue = 10
c_pos2_seeking_fast_counter_maxvalue = 10
c_pos2_seeking_slow_counter_maxvalue = 10
c_clock_freq = 10000000
c_microsteps_per_seconds_fast = 10000
c_microsteps_per_seconds_slow = 1000
c_prescaler_slow = c_clock_freq / c_microsteps_per_seconds_slow
c_prescaler_fast = c_clock_freq / c_microsteps_per_seconds_fast

m_state = enum('undefined',
               'init',
               'seek_home',
               'seek_home_timeout',
               'pos1_resting',
               'pos1_resting_error',
               'pos2_seeking_fast',
               'pos2_seeking_slow',
               'pos2_seeking_timeout',
               'pos2_resting',
               'pos2_resting_error',
               'pos1_seeking_fast',
               'pos1_seeking_slow',
               'pos1_seeking_timeout')


def mirror_box_controller(
        clk,                # input, main clock
        reset,              # input, main reset, active low
        state_reset,        # input, synchronous reset for the FSM state, active low
        state,              # output, state of the FSM for debugging purposes
        hall1_not,          # input, raw signal of the hallsensor on position 1, active low
        hall2_not,          # input, raw signal of the hallsensor on position 2, active low
        drive2pos1_manual,  # input, driving this signal high sets the target_position to pos1, manual operation
        drive2pos2_manual,  # input, driving this signal high sets the target_position to pos2, manual operation
        drive2pos1_PIO,     # input, driving this signal high sets the target_position to pos1, PIO interface
        drive2pos2_PIO,     # input, driving this signal high sets the target_position to pos2, PIO interface
        lock_manual_input,  # input, driving this signal high disables the manual operation
        stepper_direction,  # output, direction signal for the stepper driver, 1==CW, 0==CCW
        stepper_steps       # output, step signal for the stepper driver, each cycle equals one microstep
):

    # definition of internal registers
    target_position =  Signal(bool(c_position_pos1))  # 0==Pos1, 1==Pos2
    reg_home_seeking_slow_counter = Signal(0)
    reg_pos1_seeking_fast_counter = Signal(0)
    reg_pos1_seeking_slow_counter = Signal(0)
    reg_pos2_seeking_fast_counter = Signal(0)
    reg_pos2_seeking_slow_counter = Signal(0)
    reg_step_generator_slow_counter = Signal(0)
    reg_step_generator_fast_counter = Signal(0)

    # definition of internal flags
    flag_stepper_direction = Signal(bool(0))
    flag_stepper_enable = Signal(bool(0))   # enables the generation of the stepping signal for the stepper driver
    flag_stepper_speed = Signal(bool(0))     # 0==slow stepping speed, 1==fast stepping speed
    flag_seek_home_slow_enable = Signal(bool(0))
    flag_seek_pos1_slow_enable = Signal(bool(0))
    flag_seek_pos1_fast_enable = Signal(bool(0))
    flag_seek_pos2_slow_enable = Signal(bool(0))
    flag_seek_pos2_fast_enable = Signal(bool(0))
    flag_seek_home_slow_counter_top = Signal(bool(0))
    flag_seek_pos1_slow_counter_top = Signal(bool(0))    # 1 when seeking position 1 goes into timeout
    flag_seek_pos1_fast_counter_top = Signal(bool(0))    # 1 when time for fast seeking is up
    flag_seek_pos2_slow_counter_top = Signal(bool(0))    # 1 when seeking position 2 goes into timeout
    flag_seek_pos2_fast_counter_top = Signal(bool(0))    # 1 when time for fast seeking is up

    # definition of internal signals
    hall1 = Signal(bool(0))     # 1 when the magnet has reached hallsensor 1, active high
    hall2 = Signal(bool(0))     # 1 when the magnet has reached hallsensor 2, active high
    step_clock_slow = Signal(bool(0))    # clock for the stepper driver when seeking slowly
    step_clock_fast = Signal(bool(0))    # clock for the stepper driver when seeking fast

    @always_seq(clk.posedge, reset=reset)
    def step_generator_slow():
        if reg_step_generator_slow_counter <= Signal((c_prescaler_slow -2) / 2):
            reg_step_generator_slow_counter.next = reg_step_generator_slow_counter + 1
        else:
            reg_step_generator_slow_counter.next = Signal(0)
            step_clock_slow.next = not step_clock_slow

    @always_seq(clk.posedge, reset=reset)
    def step_generator_fast():
        if reg_step_generator_fast_counter <= Signal((c_prescaler_fast -2) / 2):
            reg_step_generator_fast_counter.next = reg_step_generator_fast_counter + 1
        else:
            reg_step_generator_fast_counter.next = Signal(0)
            step_clock_fast.next = not step_clock_fast

    @always_comb
    def step_output():
        if flag_stepper_enable == Signal(bool(1)):
            if flag_stepper_speed == Signal(bool(c_speed_fast)):
                stepper_steps.next = step_clock_fast
            else:
                stepper_steps.next = step_clock_slow
        else:
            stepper_steps.next = Signal(bool(0))

    @always_comb
    def generate_stepper_direction():
        stepper_direction.next = flag_stepper_direction

    @always_comb
    def inverter_hall1():
        hall1.next = not hall1_not

    @always_comb
    def inverter_hall2():
        hall2.next = not hall2_not

    @always_seq(clk.posedge, reset=reset)
    def update_target_position():
        if drive2pos1_manual == Signal(bool(1)):
            target_position.next = Signal(bool(c_position_pos1))
        elif drive2pos1_PIO == Signal(bool(1)):
            target_position.next = Signal(bool(c_position_pos1))
        elif drive2pos2_manual == Signal(bool(1)):
            target_position.next = Signal(bool(c_position_pos2))
        elif drive2pos2_PIO == Signal(bool(1)):
            target_position.next = Signal(bool(c_position_pos2))

    @always_seq(clk.posedge, reset=reset)
    def home_seeking_slow_counter():
        if flag_seek_home_slow_enable == Signal(bool(1)):
            if reg_home_seeking_slow_counter > c_home_seeking_slow_counter_maxvalue:
                flag_seek_home_slow_counter_top.next = Signal(bool(1))
            else:
                flag_seek_home_slow_counter_top.next = Signal(bool(0))
                reg_home_seeking_slow_counter.next = reg_home_seeking_slow_counter + 1

    @always_seq(clk.posedge, reset=reset)
    def pos1_seeking_slow_counter():
        if flag_seek_pos1_slow_enable == Signal(bool(1)):
            if reg_pos1_seeking_slow_counter > c_pos1_seeking_slow_counter_maxvalue:
                flag_seek_pos1_slow_counter_top.next = Signal(bool(1))
            else:
                flag_seek_pos1_slow_counter_top.next = Signal(bool(0))
                reg_pos1_seeking_slow_counter.next = reg_pos1_seeking_slow_counter + 1

    @always_seq(clk.posedge, reset=reset)
    def pos1_seeking_fast_counter():
        if flag_seek_pos1_fast_enable == Signal(bool(1)):
            if reg_pos1_seeking_fast_counter > c_pos1_seeking_fast_counter_maxvalue:
                flag_seek_pos1_fast_counter_top.next = Signal(bool(1))
            else:
                flag_seek_pos1_fast_counter_top.next = Signal(bool(0))
                reg_pos1_seeking_fast_counter.next = reg_pos1_seeking_fast_counter + 1

    @always_seq(clk.posedge, reset=reset)
    def pos2_seeking_slow_counter():
        if flag_seek_pos2_slow_enable == Signal(bool(1)):
            if reg_pos2_seeking_slow_counter > c_pos2_seeking_slow_counter_maxvalue:
                flag_seek_pos2_slow_counter_top.next = Signal(bool(1))
            else:
                flag_seek_pos2_slow_counter_top.next = Signal(bool(0))
                reg_pos2_seeking_slow_counter.next = reg_pos2_seeking_slow_counter + 1

    @always_seq(clk.posedge, reset=reset)
    def pos2_seeking_fast_counter():
        if flag_seek_pos2_fast_enable == Signal(bool(1)):
            if reg_pos2_seeking_fast_counter > c_pos2_seeking_fast_counter_maxvalue:
                flag_seek_pos2_fast_counter_top.next = Signal(bool(1))
            else:
                flag_seek_pos2_fast_counter_top.next = Signal(bool(0))
                reg_pos2_seeking_fast_counter.next = reg_pos2_seeking_fast_counter + 1

    @always_seq(clk.posedge, reset=reset)
    def fsm():
        if state == m_state.init:
            state.next = m_state.seek_home
            flag_stepper_direction.next = Signal(bool(c_direction_pos1))
            flag_stepper_speed.next = Signal(bool(c_speed_slow))
            flag_stepper_enable.next = Signal(bool(0))
            flag_seek_home_slow_counter_top.next = Signal(bool(0))
            flag_seek_pos1_slow_counter_top.next = Signal(bool(0))
            flag_seek_pos1_fast_counter_top.next = Signal(bool(0))
            flag_seek_pos2_slow_counter_top.next = Signal(bool(0))
            flag_seek_pos2_fast_counter_top.next = Signal(bool(0))
            target_position.next = Signal(bool(c_position_pos1))
            reg_home_seeking_slow_counter.next = Signal(0)
            reg_pos1_seeking_fast_counter.next = Signal(0)
            reg_pos1_seeking_slow_counter.next = Signal(0)
            reg_pos2_seeking_fast_counter.next = Signal(0)
            reg_pos2_seeking_slow_counter.next = Signal(0)

        elif state == m_state.seek_home:
            flag_seek_home_slow_enable.next = Signal(bool(1))
            flag_stepper_enable.next = Signal(bool(1))
            if flag_seek_home_slow_counter_top == Signal(bool(c_reached)):
                state.next = m_state.seek_home_timeout
            else:
                if hall1 == Signal(bool(c_reached)) and hall2 == Signal(bool(c_not_reached)):
                    state.next = m_state.pos1_resting
                else:
                    state.next = m_state.seek_home

        elif state == m_state.seek_home_timeout:
            flag_seek_home_slow_enable.next = Signal(bool(0))
            flag_stepper_enable.next = Signal(bool(0))
            if state_reset == Signal(bool(1)):
                state.next = m_state.init
            else:
                state.next = m_state.seek_home_timeout

        elif state == m_state.pos1_resting:
            reg_home_seeking_slow_counter.next = Signal(0)
            reg_pos1_seeking_slow_counter.next = Signal(0)
            flag_seek_home_slow_enable.next = Signal(bool(0))
            flag_seek_pos1_slow_enable.next = Signal(bool(0))
            flag_stepper_enable.next = Signal(bool(0))
            if target_position == Signal(bool(c_position_pos2)):
                state.next = m_state.pos2_seeking_fast
                reg_pos2_seeking_fast_counter.next = Signal(0)
                flag_stepper_direction.next = Signal(bool(c_direction_pos2))
                flag_stepper_speed.next = Signal(bool(c_speed_fast))
                flag_stepper_enable.next = Signal(bool(0))
            else:
                if hall1 == Signal(bool(c_reached)):
                    state.next = m_state.pos1_resting
                else:
                    state.next = m_state.pos1_resting_error

        elif state == m_state.pos2_resting:
            reg_pos2_seeking_slow_counter.next = Signal(0)
            flag_seek_pos2_slow_enable.next = Signal(bool(0))
            flag_stepper_enable.next = Signal(bool(0))
            if target_position == Signal(bool(c_position_pos1)):
                state.next = m_state.pos1_seeking_fast
                reg_pos1_seeking_fast_counter.next = Signal(0)
                flag_stepper_direction.next = Signal(bool(c_direction_pos1))
                flag_stepper_speed.next = Signal(bool(c_speed_fast))
                flag_stepper_enable.next = Signal(bool(0))
            else:
                if hall2 == Signal(bool(c_reached)):
                    state.next = m_state.pos2_resting
                else:
                    state.next = m_state.pos2_resting_error

        elif state == m_state.pos1_resting_error:
            flag_stepper_enable.next = Signal(bool(0))
            if state_reset == Signal(bool(1)):
                state.next = m_state.init
            else:
                state.next = m_state.pos1_resting_error

        elif state == m_state.pos2_resting_error:
            flag_stepper_enable.next = Signal(bool(0))
            if state_reset == Signal(bool(1)):
                state.next = m_state.init
            else:
                state.next = m_state.pos2_resting_error

        elif state == m_state.pos1_seeking_slow:
            flag_seek_pos1_fast_enable.next = Signal(bool(0))
            flag_seek_pos1_slow_enable.next = Signal(bool(1))
            reg_pos1_seeking_fast_counter.next = Signal(0)
            flag_stepper_direction.next = Signal(bool(c_direction_pos1))
            flag_stepper_speed.next = Signal(bool(c_speed_slow))
            flag_stepper_enable.next = Signal(bool(1))
            if hall1 == Signal(bool(c_reached)):
                state.next = m_state.pos1_resting
            else:
                if flag_seek_pos1_slow_counter_top == Signal(bool(c_reached)):
                    state.next = m_state.pos1_seeking_timeout
                else:
                    state.next = m_state.pos1_seeking_slow

        elif state == m_state.pos2_seeking_slow:
            flag_stepper_enable.next = Signal(bool(1))
            reg_pos2_seeking_fast_counter.next = Signal(0)
            flag_stepper_direction.next = Signal(bool(c_direction_pos2))
            flag_stepper_speed.next = Signal(bool(c_speed_slow))
            flag_seek_pos2_fast_enable.next = Signal(bool(0))
            flag_seek_pos2_slow_enable.next = Signal(bool(1))
            if hall2 == Signal(bool(c_reached)):
                state.next = m_state.pos2_resting
            else:
                if flag_seek_pos2_slow_counter_top == Signal(bool(1)):
                    state.next = m_state.pos2_seeking_timeout
                else:
                    state.next = m_state.pos2_seeking_slow

        elif state == m_state.pos1_seeking_fast:
            flag_stepper_enable.next = Signal(bool(1))
            flag_stepper_enable.next = Signal(bool(1))
            flag_stepper_direction.next = Signal(bool(c_direction_pos1))
            flag_stepper_speed.next = Signal(bool(c_speed_fast))
            flag_seek_pos1_fast_enable.next = Signal(bool(1))
            if flag_seek_pos1_fast_counter_top == Signal(bool(1)):
                reg_pos1_seeking_slow_counter.next = Signal(0)
                state.next = m_state.pos1_seeking_slow
                flag_stepper_enable.next = Signal(0)
                flag_stepper_speed.next = Signal(c_speed_slow)
                flag_stepper_direction.next = Signal(c_direction_pos1)
            else:
                state.next = m_state.pos1_seeking_fast

        elif state == m_state.pos2_seeking_fast:
            flag_stepper_enable.next = Signal(bool(1))
            flag_seek_pos2_fast_enable.next = Signal(bool(1))
            flag_seek_pos2_slow_enable.next = Signal(bool(0))
            if flag_seek_pos2_fast_counter_top == Signal(bool(1)):
                reg_pos2_seeking_slow_counter.next = Signal(0)
                state.next = m_state.pos2_seeking_slow
                flag_stepper_enable.next = Signal(0)
                flag_stepper_speed.next = Signal(c_speed_slow)
                flag_stepper_direction.next = Signal(c_direction_pos2)
            else:
                state.next = m_state.pos2_seeking_fast

        elif state == m_state.pos1_seeking_timeout:
            flag_stepper_enable.next = Signal(bool(0))
            if state_reset == Signal(bool(1)):
                state.next = m_state.init
            else:
                state.next = m_state.pos1_seeking_timeout

        elif state == m_state.pos2_seeking_timeout:
            flag_stepper_enable.next = Signal(bool(0))
            if state_reset == Signal(bool(1)):
                state.next = m_state.init
            else:
                state.next = m_state.pos2_seeking_timeout
        else:
            state.next = m_state.init

    # return fsm, inverter_hall1, inverter_hall2, pos1_seeking_fast_counter, pos2_seeking_fast_counter,\
    #        pos1_seeking_slow_counter. pos2_seeking_slow_counter, home_seeking_slow_counter, update_target_position
    return fsm, inverter_hall1, inverter_hall2, pos1_seeking_fast_counter, pos2_seeking_fast_counter,\
           pos1_seeking_slow_counter, home_seeking_slow_counter, update_target_position, pos2_seeking_slow_counter,\
            step_generator_slow, step_generator_fast, step_output, generate_stepper_direction




















