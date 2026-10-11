`timescale 1ns/1ps
module tb_pipe_check;
    reg clk=0, rst_n=0, start=0, op=0;
    reg [1:0] prec_sel=0;
    reg signed [31:0] theta_in, x0_in, y0_in;
    wire signed [31:0] cos_out, sin_out, angle_out;
    wire valid;
    wire [7:0] cycle_count;

    cordic_top_pipe uut (
        .clk(clk), .rst_n(rst_n), .start(start), .op(op), .prec_sel(prec_sel),
        .theta_in(theta_in), .x0_in(x0_in), .y0_in(y0_in),
        .cos_out(cos_out), .sin_out(sin_out), .angle_out(angle_out),
        .valid(valid), .cycle_count(cycle_count)
    );
    defparam uut.DUAL_STEP = 2;
    defparam uut.EARLY_STOP = 0;

    always #5 clk=~clk;

    integer i;
    task run_one;
        begin
            @(negedge clk); start=1;
            @(negedge clk); start=0;
            @(posedge valid);
            @(negedge clk);
        end
    endtask

    initial begin
        rst_n=0; #12; rst_n=1;
        op=0; prec_sel=0; theta_in=32'sd500000;
        run_one;
        $display("High rot cycle_count=%0d (expect 18)", cycle_count);
        prec_sel=1; run_one;
        $display("Medium rot cycle_count=%0d (expect 14)", cycle_count);
        prec_sel=2; run_one;
        $display("Low rot cycle_count=%0d (expect 11)", cycle_count);
        $finish;
    end
endmodule
