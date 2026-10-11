`timescale 1ns/1ps
module tb_cordic;
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
    defparam uut.DUAL_STEP = 0;
    defparam uut.EARLY_STOP = 1;

    always #5 clk = ~clk;

    integer NANG = 500, NXY = 500;
    reg signed [31:0] ang_mem [0:499];
    reg signed [31:0] x_mem   [0:499];
    reg signed [31:0] y_mem   [0:499];
    integer i, p;
    integer frot, fvec;
    reg [255:0] tag;
    reg [255:0] fname;

    task run_one;
        begin
            @(negedge clk); start = 1;
            @(negedge clk); start = 0;
            @(posedge valid);
            @(negedge clk);
        end
    endtask

    initial begin
        $readmemh("angles_h.hex", ang_mem);
        $readmemh("xy_x_h.hex", x_mem);
        $readmemh("xy_y_h.hex", y_mem);
        rst_n = 0; #12; rst_n = 1;

        if (uut.DUAL_STEP && uut.EARLY_STOP)      tag = "combined";
        else if (uut.DUAL_STEP)                   tag = "dualonly";
        else if (uut.EARLY_STOP)                  tag = "earlyonly";
        else                                       tag = "baseline";

        for (p = 0; p < 3; p = p + 1) begin
            prec_sel = p[1:0];
            $sformat(fname, "rot_%0s_p%0d.txt", tag, p);
            frot = $fopen(fname, "w");
            op = 0;
            for (i = 0; i < NANG; i = i + 1) begin
                theta_in = ang_mem[i];
                run_one;
                $fdisplay(frot, "%0d %0d %0d %0d", theta_in, cos_out, sin_out, cycle_count);
            end
            $fclose(frot);

            $sformat(fname, "vec_%0s_p%0d.txt", tag, p);
            fvec = $fopen(fname, "w");
            op = 1;
            for (i = 0; i < NXY; i = i + 1) begin
                x0_in = x_mem[i]; y0_in = y_mem[i];
                run_one;
                $fdisplay(fvec, "%0d %0d %0d %0d", x0_in, y0_in, angle_out, cycle_count);
            end
            $fclose(fvec);
        end

        $display("DONE %0s", tag);
        $finish;
    end
endmodule
