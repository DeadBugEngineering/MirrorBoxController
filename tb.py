from main import *

def testbench():
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

    dut = mirror_box_controller(clk, reset, state_reset, state, hall1_not, hall2_not, drive2pos1_manual,
                                drive2pos2_manual, drive2pos1_PIO, drive2pos2_PIO, lock_manual_input, stepper_direction,
                                stepper_steps)



    @always(delay(50))
    def clkgen():
        clk.next = not clk

    @instance
    def stimulus_clock():
        for i in range(5000):
            yield clk.posedge
        raise StopSimulation

    @instance
    def stim_hall1_not():
        yield delay(400)
        hall1_not.next = Signal(bool(0))
        yield delay(900)
        hall1_not.next = Signal(bool(1))
        yield delay(11700)
        hall1_not.next = Signal(bool(0))
        yield delay(1000)
        hall1_not.next = Signal(bool(1))
        yield delay(5500)
        hall1_not.next = Signal(bool(0))

    @instance
    def stim_hall2_not():
        yield delay(4000)
        hall2_not.next = Signal(bool(0))
        yield delay(2000)
        hall2_not.next = Signal(bool(1))
        yield delay(10000)
        hall2_not.next = Signal(bool(0))

    @instance
    def stim_state_reset():
        yield delay(9000)
        state_reset.next = Signal(bool(1))
        yield delay(1000)
        state_reset.next = Signal(bool(0))
        yield delay(2000)
        state_reset.next = Signal(bool(1))
        yield delay(1000)
        state_reset.next = Signal(bool(0))

    @instance
    def stim_drive2pos2_man():
        yield delay(1000)
        drive2pos2_manual.next = Signal(bool(1))
        yield delay(100)
        drive2pos2_manual.next = Signal(bool(0))

    @instance
    def stim_drive2pos2_PIO():
        yield delay(13500)
        drive2pos2_PIO.next = Signal(bool(1))
        yield delay(500)
        drive2pos2_PIO.next = Signal(bool(0))

    @instance
    def stim_drive2pos1_man():
        yield delay(17000)
        drive2pos1_manual.next = Signal(bool(1))
        yield delay(1000)
        drive2pos1_manual.next = Signal(bool(0))

    @always_seq(clk.posedge, reset=reset)
    def output_printer():
        print now(), state

    #return dut, clkgen, stimulus, output_printer
    return dut, clkgen, stimulus_clock, stim_hall1_not, stim_hall2_not, output_printer, stim_drive2pos2_man,\
        stim_state_reset, stim_drive2pos2_PIO, stim_drive2pos1_man


tb_fsm = traceSignals(testbench)
sim = Simulation(tb_fsm)
sim.run()


