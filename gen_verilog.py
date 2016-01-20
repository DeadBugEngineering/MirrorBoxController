from main import *

clk = Signal(bool(0))
reset = ResetSignal(1, active=0, async=True)
state_reset = Signal(bool(0))
state = Signal(m_state.init)
hall1_not = Signal(bool(1))
hall2_not = Signal(bool(1))
drive2pos1_manual = Signal(bool(0))
drive2pos2_manual = Signal(bool(0))
drive2pos1_PIO = Signal(bool(0))
drive2pos2_PIO = Signal(bool(0))
lock_manual_input = Signal(bool(0))
stepper_direction = Signal(bool(c_direction_pos1))
stepper_steps = Signal(bool(0))

controller_inst = toVerilog(mirror_box_controller, clk, reset, state_reset, state, hall1_not, hall2_not, drive2pos1_manual,
                            drive2pos2_manual, drive2pos1_PIO, drive2pos2_PIO, lock_manual_input, stepper_direction,
                            stepper_steps)














