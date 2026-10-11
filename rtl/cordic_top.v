// -----------------------------------------------------------------------
// cordic_top.v
// Full-range wrapper around cordic_engine: quadrant folding extends the
// native +/-pi/2 (rotation) / first-fourth-quadrant (vectoring)
// convergence range to the full +/-pi domain, matching the standard
// CORDIC range-extension technique. theta_in is assumed pre-wrapped to
// [-pi, pi); the mod-2pi reduction itself is a separate, well-known
// preprocessing step and is not part of the contribution measured here.
// -----------------------------------------------------------------------
`timescale 1ns/1ps

module cordic_top #(
    parameter PW        = 32,
    parameter FRAC       = 20,
    parameter ITMAX      = 18,
    parameter DUAL_STEP  = 0,
    parameter EARLY_STOP = 1,
    parameter signed [PW-1:0] K_FX = 32'sd636751 // 1/A precomputed, ITMAX=18
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 start,
    input  wire                 op,          // 0 = SINCOS (rotate), 1 = ATAN2 (vector)
    input  wire [1:0]           prec_sel,
    input  wire signed [PW-1:0] theta_in,    // used when op=0, range [-pi,pi)
    input  wire signed [PW-1:0] x0_in,       // used when op=1
    input  wire signed [PW-1:0] y0_in,       // used when op=1
    output reg  signed [PW-1:0] cos_out,
    output reg  signed [PW-1:0] sin_out,
    output reg  signed [PW-1:0] angle_out,
    output wire                 valid,
    output wire [7:0]           cycle_count
);
    localparam signed [PW-1:0] PI     = 32'sd3294199; // pi   * 2^20
    localparam signed [PW-1:0] HALFPI = 32'sd1647100; // pi/2 * 2^20

    reg quad_neg_cos, quad_neg_sin, atan_flip;
    reg signed [PW-1:0] x_in_r, y_in_r, z_in_r, mode_r_hold;
    reg mode_hold;

    wire signed [PW-1:0] x_eng, y_eng, z_eng;
    reg  signed [PW-1:0] x_in_e, y_in_e, z_in_e;
    reg                  mode_e;

    always @(*) begin
        // default combinational fold (evaluated continuously; latched on start)
        x_in_e = {PW{1'b0}};
        y_in_e = {PW{1'b0}};
        z_in_e = {PW{1'b0}};
        mode_e = op;
        quad_neg_cos = 1'b0; quad_neg_sin = 1'b0; atan_flip = 1'b0;
        if (op == 1'b0) begin
            x_in_e = K_FX; y_in_e = {PW{1'b0}};
            if (theta_in > HALFPI) begin
                z_in_e = PI - theta_in; quad_neg_cos = 1'b1; quad_neg_sin = 1'b0;
            end else if (theta_in < -HALFPI) begin
                z_in_e = theta_in + PI; quad_neg_cos = 1'b1; quad_neg_sin = 1'b1;
            end else begin
                z_in_e = theta_in;
            end
        end else begin
            if (x0_in < 0) begin
                x_in_e = -x0_in; y_in_e = -y0_in; atan_flip = 1'b1;
            end else begin
                x_in_e = x0_in; y_in_e = y0_in;
            end
            z_in_e = {PW{1'b0}};
        end
    end

    reg quad_neg_cos_r, quad_neg_sin_r, atan_flip_r, mode_r, y0_nonneg_r;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            quad_neg_cos_r <= 0; quad_neg_sin_r <= 0; atan_flip_r <= 0; mode_r <= 0;
            y0_nonneg_r <= 0;
        end else if (start) begin
            quad_neg_cos_r <= quad_neg_cos; quad_neg_sin_r <= quad_neg_sin;
            atan_flip_r <= atan_flip; mode_r <= op;
            y0_nonneg_r <= (y0_in >= 0);
        end
    end

    cordic_engine #(
        .PW(PW), .FRAC(FRAC), .ITMAX(ITMAX), .DUAL_STEP(DUAL_STEP), .EARLY_STOP(EARLY_STOP)
    ) u_engine (
        .clk(clk), .rst_n(rst_n), .start(start), .mode(op), .prec_sel(prec_sel),
        .x_in(x_in_e), .y_in(y_in_e), .z_in(z_in_e),
        .x_out(x_eng), .y_out(y_eng), .z_out(z_eng),
        .valid(valid), .cycle_count(cycle_count)
    );

    always @(*) begin
        if (mode_r == 1'b0) begin
            cos_out   = quad_neg_cos_r ? -x_eng : x_eng;
            sin_out   = quad_neg_sin_r ? -y_eng : y_eng;
            angle_out = {PW{1'b0}};
        end else begin
            cos_out   = {PW{1'b0}};
            sin_out   = {PW{1'b0}};
            if (atan_flip_r)
                angle_out = y0_nonneg_r ? (z_eng + PI) : (z_eng - PI);
            else
                angle_out = z_eng;
        end
    end
endmodule
