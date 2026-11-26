// 4-bit ALU for the reference CPU. Logic operations use the structural gate
// modules from gates.v; arithmetic uses a ripple-carry chain of full_adder.
// Opcode values are shared with the CPU instruction set in cpu.v.

module alu #(parameter WIDTH = 4) (
    input  wire [3:0]        op,
    input  wire [WIDTH-1:0]  a,
    input  wire [WIDTH-1:0]  b,
    output wire [WIDTH-1:0]  y,
    output wire              zero,
    output wire              carry
);
    localparam [3:0] ALU_PASS = 4'h0,
                     ALU_ADD  = 4'h1,
                     ALU_SUB  = 4'h2,
                     ALU_AND  = 4'h3,
                     ALU_OR   = 4'h4,
                     ALU_XOR  = 4'h5,
                     ALU_NOT  = 4'h6;

    wire is_sub = (op == ALU_SUB);
    wire [WIDTH-1:0] b_eff = is_sub ? ~b : b;
    wire [WIDTH:0] c;
    wire [WIDTH-1:0] sum;
    wire [WIDTH-1:0] and_y, or_y, xor_y, not_y;
    reg  [WIDTH-1:0] result;

    assign c[0] = is_sub;
    genvar i;
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin : adder_stage
            full_adder fa (
                .a(a[i]), .b(b_eff[i]), .cin(c[i]),
                .sum(sum[i]), .cout(c[i+1])
            );
        end
    endgenerate

    cmos_and #(.WIDTH(WIDTH)) u_and (.a(a), .b(b), .y(and_y));
    cmos_or  #(.WIDTH(WIDTH)) u_or  (.a(a), .b(b), .y(or_y));
    cmos_xor #(.WIDTH(WIDTH)) u_xor (.a(a), .b(b), .y(xor_y));
    cmos_not #(.WIDTH(WIDTH)) u_not (.a(a), .y(not_y));

    always @* begin
        case (op)
            ALU_ADD, ALU_SUB: result = sum;
            ALU_AND:  result = and_y;
            ALU_OR:   result = or_y;
            ALU_XOR:  result = xor_y;
            ALU_NOT:  result = not_y;
            default:  result = a;              // LDI / pass-through
        endcase
    end

    assign y = result;
    assign zero = ~|y;
    assign carry = c[WIDTH];
endmodule
