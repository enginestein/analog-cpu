// Structural digital equivalents of the CMOS gates in ../CMOS_*.sch.
//
// These are synthesisable behavioural descriptions of gate *logic*, not
// transistor-level models. The analogue behaviour lives in the Qucs-S
// schematics; this file is the digital reference the analogue gates should
// agree with (see `python -m analog_cpu`).

module cmos_not #(parameter WIDTH = 1) (
    input  wire [WIDTH-1:0] a,
    output wire [WIDTH-1:0] y
);
    assign y = ~a;
endmodule

module cmos_nand #(parameter WIDTH = 1) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] y
);
    assign y = ~(a & b);
endmodule

module cmos_nor #(parameter WIDTH = 1) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] y
);
    assign y = ~(a | b);
endmodule

// CMOS AND = NAND stage followed by an inverter (NODEN in CMOS_AND.sch).
module cmos_and #(parameter WIDTH = 1) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] y
);
    wire [WIDTH-1:0] noden;
    cmos_nand #(.WIDTH(WIDTH)) u_nand (.a(a), .b(b), .y(noden));
    cmos_not  #(.WIDTH(WIDTH)) u_inv  (.a(noden), .y(y));
endmodule

// CMOS OR = NOR stage followed by an inverter (N in CMOS_OR.sch).
module cmos_or #(parameter WIDTH = 1) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] y
);
    wire [WIDTH-1:0] n;
    cmos_nor #(.WIDTH(WIDTH)) u_nor (.a(a), .b(b), .y(n));
    cmos_not #(.WIDTH(WIDTH)) u_inv (.a(n), .y(y));
endmodule

module cmos_xor #(parameter WIDTH = 1) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] y
);
    wire [WIDTH-1:0] a_or_b, a_and_b, not_and;
    cmos_or  #(.WIDTH(WIDTH)) u_or    (.a(a), .b(b), .y(a_or_b));
    cmos_and #(.WIDTH(WIDTH)) u_and1  (.a(a), .b(b), .y(a_and_b));
    cmos_not #(.WIDTH(WIDTH)) u_inv   (.a(a_and_b), .y(not_and));
    cmos_and #(.WIDTH(WIDTH)) u_and2  (.a(a_or_b), .b(not_and), .y(y));
endmodule
