read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog netlist_0_1.v
link_design cordic_top
create_clock -name clk -period 10 [get_ports clk]
read_vcd -scope tb_cordic_power/uut power_0_1.vcd
report_activity_annotation
report_power
