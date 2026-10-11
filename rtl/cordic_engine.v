// -----------------------------------------------------------------------
// cordic_engine.v
// Adaptive-precision circular-mode CORDIC engine (rotation + vectoring).
// Supports:
//   - MODE_ROTATE : (x0=K, y0=0, z0=theta) -> (cos(theta), sin(theta))
//   - MODE_VECTOR : (x0, y0)               -> (angle = atan2(y0,x0), mag*K)
//   - Residual-based early termination, stage/mode-dependent thresholds
//   - Optional dual-step-per-cycle (DSPC) scheduling: two micro-iterations
//     committed to the state registers per clock edge.
//
// Fixed-point format: PW-bit signed, Q(PW-FRAC).FRAC  (FRAC=20 fractional
// bits). Internal registers are wider than the nominal 24-bit operand
// range to avoid overflow during intermediate accumulation, matching the
// bit-accurate Python reference model (fixedmodel.py) used to tune the
// precision-mode parameters.
// -----------------------------------------------------------------------
`timescale 1ns/1ps

module cordic_engine #(
    parameter PW        = 32,   // register width
    parameter FRAC       = 20,   // fractional bits
    parameter ITMAX      = 18,   // max micro-iteration index (exclusive)
    parameter DUAL_STEP  = 0,    // 0 = single micro-iteration/cycle, 1 = two/cycle
    parameter EARLY_STOP = 1     // 0 = always run to target depth, 1 = residual check enabled
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 start,
    input  wire                 mode,        // 0 = ROTATE, 1 = VECTOR
    input  wire [1:0]           prec_sel,    // 00=High 01=Medium 10=Low
    input  wire signed [PW-1:0] x_in,
    input  wire signed [PW-1:0] y_in,
    input  wire signed [PW-1:0] z_in,
    output reg  signed [PW-1:0] x_out,
    output reg  signed [PW-1:0] y_out,
    output reg  signed [PW-1:0] z_out,
    output reg                  valid,
    output reg  [7:0]           cycle_count
);

    // ---- precomputed atan(2^-i) table, Q(PW-FRAC).FRAC, i = 0..ITMAX-1 ----
    // Values generated offline by fixedmodel.py (tofx(atan(2**-i))).
    function signed [PW-1:0] atan_lut;
        input [4:0] idx;
        begin
            case (idx)
                0 : atan_lut = 32'sd823550;
                1 : atan_lut = 32'sd486170;
                2 : atan_lut = 32'sd256879;
                3 : atan_lut = 32'sd130396;
                4 : atan_lut = 32'sd65451;
                5 : atan_lut = 32'sd32757;
                6 : atan_lut = 32'sd16383;
                7 : atan_lut = 32'sd8193;
                8 : atan_lut = 32'sd4096;
                9 : atan_lut = 32'sd2048;
                10: atan_lut = 32'sd1024;
                11: atan_lut = 32'sd512;
                12: atan_lut = 32'sd256;
                13: atan_lut = 32'sd128;
                14: atan_lut = 32'sd64;
                15: atan_lut = 32'sd32;
                16: atan_lut = 32'sd16;
                17: atan_lut = 32'sd8;
                default: atan_lut = 32'sd0;
            endcase
        end
    endfunction

    // ---- mode-dependent scheduling parameters (target depth / floor / threshold) ----
    // Values selected via the sweep in fixedmodel.py (see Table-II-equivalent).
    function [4:0] target_depth;
        input        m;   // 0 rotate 1 vector
        input [1:0]  p;
        begin
            case (p)
                2'b00: target_depth = 18; // High (same nominal cap both stages)
                2'b01: target_depth = 14; // Medium
                default: target_depth = 11; // Low
            endcase
        end
    endfunction

    function [4:0] floor_depth;
        input        m;
        input [1:0]  p;
        begin
            case (p)
                2'b00: floor_depth = 12; // High
                2'b01: floor_depth = 10; // Medium
                default: floor_depth = 8; // Low
            endcase
        end
    endfunction

    function signed [PW-1:0] thresh_val;
        input        m;
        input [1:0]  p;
        begin
            case (p)
                2'b00: thresh_val = 32'sd16;   // 2^-16
                2'b01: thresh_val = 32'sd64;   // 2^-14
                default: thresh_val = 32'sd256; // 2^-12
            endcase
        end
    endfunction

    localparam S_IDLE = 2'd0, S_RUN = 2'd1, S_DONE = 2'd2;
    reg [1:0] state;
    reg signed [PW-1:0] x_r, y_r, z_r;
    reg [4:0] iter;
    reg [1:0] prec_r;
    reg mode_r;

    // ---- single micro-iteration combinational function ----
    function [3*PW-1:0] micro_step;
        input signed [PW-1:0] x, y, z;
        input [4:0] i;
        input m; // 0 rotate, 1 vector
        reg   d_pos;
        reg signed [PW-1:0] xn, yn, zn;
        begin
            d_pos = m ? (y < 0) : (z >= 0); // sigma = +1 when d_pos
            if (d_pos) begin
                xn = x - (y >>> i);
                yn = y + (x >>> i);
                zn = z - atan_lut(i);
            end else begin
                xn = x + (y >>> i);
                yn = y - (x >>> i);
                zn = z + atan_lut(i);
            end
            micro_step = {xn, yn, zn};
        end
    endfunction

    wire signed [PW-1:0] x1, y1, z1;
    wire [3*PW-1:0] step1 = micro_step(x_r, y_r, z_r, iter, mode_r);
    assign {x1, y1, z1} = step1;

    wire [4:0] iter2 = iter + 5'd1;
    wire [3*PW-1:0] step2 = micro_step(x1, y1, z1, iter2, mode_r);
    wire signed [PW-1:0] x2, y2, z2;
    assign {x2, y2, z2} = step2;

    wire signed [PW-1:0] resid1 = mode_r ? y1 : z1;
    wire signed [PW-1:0] resid2 = mode_r ? y2 : z2;
    wire signed [PW-1:0] absresid1 = resid1[PW-1] ? -resid1 : resid1;
    wire signed [PW-1:0] absresid2 = resid2[PW-1] ? -resid2 : resid2;

    wire [4:0] tgt = target_depth(mode_r, prec_r);
    wire [4:0] flr = floor_depth(mode_r, prec_r);
    wire signed [PW-1:0] th = thresh_val(mode_r, prec_r);

    wire stop_after1 = ((iter+1) >= flr) && EARLY_STOP && (absresid1 < th);
    wire cap_after1  = ((iter+1) >= tgt);
    wire stop_after2 = ((iter+2) >= flr) && EARLY_STOP && (absresid2 < th);
    wire cap_after2  = ((iter+2) >= tgt);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; valid <= 1'b0; cycle_count <= 8'd0;
            x_r<=0; y_r<=0; z_r<=0; iter<=0; prec_r<=0; mode_r<=0;
        end else begin
            case (state)
                S_IDLE: begin
                    valid <= 1'b0;
                    if (start) begin
                        x_r <= x_in; y_r <= y_in; z_r <= z_in;
                        iter <= 5'd0; prec_r <= prec_sel; mode_r <= mode;
                        cycle_count <= 8'd0;
                        state <= S_RUN;
                    end
                end
                S_RUN: begin
                    cycle_count <= cycle_count + 8'd1;
                    if (DUAL_STEP) begin
                        if (stop_after1 || cap_after1) begin
                            x_r <= x1; y_r <= y1; z_r <= z1; iter <= iter+5'd1;
                            state <= S_DONE;
                        end else if (stop_after2 || cap_after2) begin
                            x_r <= x2; y_r <= y2; z_r <= z2; iter <= iter+5'd2;
                            state <= S_DONE;
                        end else begin
                            x_r <= x2; y_r <= y2; z_r <= z2; iter <= iter+5'd2;
                        end
                    end else begin
                        if (stop_after1 || cap_after1) begin
                            x_r <= x1; y_r <= y1; z_r <= z1; iter <= iter+5'd1;
                            state <= S_DONE;
                        end else begin
                            x_r <= x1; y_r <= y1; z_r <= z1; iter <= iter+5'd1;
                        end
                    end
                end
                S_DONE: begin
                    valid <= 1'b1;
                    state <= S_IDLE;
                end
                default: state <= S_IDLE;
            endcase
        end
    end

    always @(*) begin
        x_out = x_r; y_out = y_r; z_out = z_r;
    end

endmodule
