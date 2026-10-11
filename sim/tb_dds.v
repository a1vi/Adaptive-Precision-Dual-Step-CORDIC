`timescale 1ns/1ps
// Application-level validation: drives cordic_top as a DDS/NCO sine-cosine
// generator over one full phase ramp (sim/dds_angles_h.hex, 4096 points,
// one cycle) at each of the three precision modes, for the Combined
// (DUAL_STEP=1, EARLY_STOP=1) configuration -- the fully-featured design
// as it would actually be deployed. Output is the real RTL-simulated
// cos_out/sin_out sequence, later FFT-analyzed in Python for SFDR/THD.
module tb_dds;
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
    defparam uut.DUAL_STEP = 1;
    defparam uut.EARLY_STOP = 1;

    always #5 clk = ~clk;

    parameter NANG = 4096;
    reg signed [31:0] ang_mem [0:4095];
    integer i, p;
    integer fout;
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
        $readmemh("dds_angles_h.hex", ang_mem);
        rst_n = 0; #12; rst_n = 1;
        x0_in = 0; y0_in = 0;
        op = 0;

        for (p = 0; p < 3; p = p + 1) begin
            prec_sel = p[1:0];
            $sformat(fname, "dds_out_combined_p%0d.txt", p);
            fout = $fopen(fname, "w");
            for (i = 0; i < NANG; i = i + 1) begin
                theta_in = ang_mem[i];
                run_one;
                $fdisplay(fout, "%0d %0d %0d", theta_in, cos_out, sin_out);
            end
            $fclose(fout);
        end

        $display("DONE dds");
        $finish;
    end
endmodule
