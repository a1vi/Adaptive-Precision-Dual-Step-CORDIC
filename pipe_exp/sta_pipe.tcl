read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog pipe_exp/netlist_pipe.v
link_design cordic_top_pipe
create_clock -name clk -period 10 [get_ports clk]
set_input_delay -clock clk 0 [all_inputs]
set_output_delay -clock clk 0 [all_outputs]
report_checks -path_delay max -digits 4
report_tns
report_wns
