// -----------------------------------------------------------------------
// cordic_fpga_shell.v
// Pin-reduction TEST HARNESS for FPGA bring-up only. The 209-pin native
// interface of cordic_top exceeds the 207 user I/O available on the
// largest iCE40 package supported by the open-source toolchain
// (iCE40HX8K-CT256), so a direct placed-and-routed bitstream of
// cordic_top's native ports cannot be built on that device. This shell
// wraps the UNMODIFIED cordic_top/cordic_engine core with simple 8-bit
// serial shift-in / shift-out registers to fit the interface into a
// narrow pin budget. None of the CORDIC arithmetic is altered; the only
// added logic is plain shift registers and load/read sequencing, which
// is excluded from the reported critical-path discussion (verified via
// the nextpnr critical-path report to not be the timing-limiting path).
// -----------------------------------------------------------------------
`timescale 1ns/1ps

module cordic_fpga_shell #(
    parameter PW        = 32,
    parameter FRAC       = 20,
    parameter ITMAX      = 18,
    parameter DUAL_STEP  = 0,
    parameter EARLY_STOP = 1,
    parameter signed [PW-1:0] K_FX = 32'sd636751
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] din,        // serial byte-wide data in
    input  wire [2:0] ld_sel,     // which input register to shift into: 0=theta,1=x0,2=y0
    input  wire       ld_shift,   // pulse: shift din into selected input register (MSB-first, 4 bytes)
    input  wire       op,
    input  wire [1:0] prec_sel,
    input  wire       start,
    input  wire [2:0] rd_sel,     // which output register to shift out: 0=cos,1=sin,2=angle
    input  wire       rd_shift,   // pulse: shift selected output register out (MSB-first, 4 bytes)
    output wire [7:0] dout,
    output wire        valid,
    output wire [7:0]  cycle_count
);
    reg signed [PW-1:0] theta_sh, x0_sh, y0_sh;
    reg signed [PW-1:0] cos_cap, sin_cap, angle_cap;

    always @(posedge clk) begin
        if (ld_shift) begin
            case (ld_sel)
                3'd0: theta_sh <= {theta_sh[PW-9:0], din};
                3'd1: x0_sh    <= {x0_sh[PW-9:0],    din};
                3'd2: y0_sh    <= {y0_sh[PW-9:0],    din};
                default: ;
            endcase
        end
    end

    wire signed [PW-1:0] cos_eng, sin_eng, angle_eng;
    wire valid_eng;

    always @(posedge clk) begin
        if (valid_eng) begin
            cos_cap   <= cos_eng;
            sin_cap   <= sin_eng;
            angle_cap <= angle_eng;
        end
    end

    reg signed [PW-1:0] dout_sh;
    always @(posedge clk) begin
        if (rd_shift) begin
            case (rd_sel)
                3'd0: dout_sh <= {dout_sh[PW-9:0], 8'h00};
                3'd1: dout_sh <= {dout_sh[PW-9:0], 8'h00};
                3'd2: dout_sh <= {dout_sh[PW-9:0], 8'h00};
                default: ;
            endcase
        end else begin
            case (rd_sel)
                3'd0: dout_sh <= cos_cap;
                3'd1: dout_sh <= sin_cap;
                3'd2: dout_sh <= angle_cap;
                default: dout_sh <= {PW{1'b0}};
            endcase
        end
    end
    assign dout = dout_sh[PW-1:PW-8];

    assign valid = valid_eng;

    cordic_top #(
        .PW(PW), .FRAC(FRAC), .ITMAX(ITMAX),
        .DUAL_STEP(DUAL_STEP), .EARLY_STOP(EARLY_STOP), .K_FX(K_FX)
    ) u_engine (
        .clk(clk), .rst_n(rst_n), .start(start), .op(op), .prec_sel(prec_sel),
        .theta_in(theta_sh), .x0_in(x0_sh), .y0_in(y0_sh),
        .cos_out(cos_eng), .sin_out(sin_eng), .angle_out(angle_eng),
        .valid(valid_eng), .cycle_count(cycle_count)
    );

endmodule
