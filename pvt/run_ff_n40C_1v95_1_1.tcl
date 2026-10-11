read_liberty sky130_fd_sc_hd__ff_n40C_1v95.lib
read_verilog netlist_1_1.v
link_design cordic_top
create_clock -name clk -period 1 [get_ports clk]
set_input_delay -clock clk 0 [all_inputs]
set_output_delay -clock clk 0 [all_outputs]
report_wns
report_tns
report_checks -path_delay max -digits 4 -format summary
