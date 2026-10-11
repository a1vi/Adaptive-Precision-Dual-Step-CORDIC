`timescale 1ns/1ps
module tb_cordic_power;
    reg clk = 0, rst_n = 0, start = 0, op = 0;
    reg [1:0] prec_sel = 0;
    reg signed [31:0] theta_in, x0_in, y0_in;
    wire signed [31:0] cos_out, sin_out, angle_out;
    wire valid;
    wire [7:0] cycle_count;

    cordic_top uut (
        .clk(clk), .rst_n(rst_n), .start(start), .op(op), .prec_sel(prec_sel),
        .theta_in(theta_in), .x0_in(x0_in), .y0_in(y0_in),
        .cos_out(cos_out), .sin_out(sin_out), .angle_out(angle_out),
        .valid(valid), .cycle_count(cycle_count)
    );

    always #5 clk = ~clk;

    integer NSTIM = 6;
    reg signed [31:0] ang_mem [0:4999];
    reg signed [31:0] x_mem   [0:4999];
    reg signed [31:0] y_mem   [0:4999];
    integer i, p;

    task run_one;
        begin
            @(negedge clk); start = 1;
            @(negedge clk); start = 0;
            @(posedge valid);
            @(negedge clk);
        end
    endtask

    initial begin
        $readmemh("eval_angles_h.hex", ang_mem);
        $readmemh("eval_xy_x_h.hex", x_mem);
        $readmemh("eval_xy_y_h.hex", y_mem);

        $dumpfile("power.vcd");
        $dumpvars(0, uut);

        rst_n = 0; #12; rst_n = 1;

        // Exercise all three precision modes with real rotation (sin/cos)
        // and vectoring (atan2) stimuli drawn from the same evaluation
        // angle/coordinate set used for the paper's accuracy sweep --
        // representative switching activity, not a synthetic toggle pattern.
        for (p = 0; p < 3; p = p + 1) begin
            prec_sel = p[1:0];

            op = 0; // rotation: sin/cos
            for (i = 0; i < NSTIM; i = i + 1) begin
                theta_in = ang_mem[i];
                run_one;
            end

            op = 1; // vectoring: atan2
            for (i = 0; i < NSTIM; i = i + 1) begin
                x0_in = x_mem[i]; y0_in = y_mem[i];
                run_one;
            end
        end

        $display("DONE power stimulus");
        $finish;
    end
endmodule
