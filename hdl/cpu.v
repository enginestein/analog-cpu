// A deliberately tiny accumulator CPU: 4-bit data, 16-word program ROM,
// 16-word data RAM, two cycles per instruction (FETCH, EXECUTE).
//
// Instruction word: {opcode[7:4], operand[3:0]}. The ALU opcode values are
// chosen to match the instruction opcodes so EXECUTE can use the ALU result
// directly. Load program.hex (or a file selected with PROGRAM_FILE) at reset.

module cpu #(
    parameter PROGRAM_FILE = "program.hex",
    parameter WORDS = 16
) (
    input  wire       clk,
    input  wire       reset,
    output reg  [3:0] acc,
    output reg  [3:0] pc,
    output reg        halted,
    output wire       zero,
    output wire       carry
);
    localparam [3:0] OP_LDI = 4'h0,
                     OP_ADD = 4'h1,
                     OP_SUB = 4'h2,
                     OP_AND = 4'h3,
                     OP_OR  = 4'h4,
                     OP_XOR = 4'h5,
                     OP_NOT = 4'h6,
                     OP_STA = 4'h7,
                     OP_LDA = 4'h8,
                     OP_JMP = 4'h9,
                     OP_JZ  = 4'hA,
                     OP_HLT = 4'hF;

    localparam [1:0] FETCH = 2'd0, EXECUTE = 2'd1;

    reg [7:0] prog [0:WORDS-1];
    reg [3:0] mem  [0:WORDS-1];
    reg [7:0] instr;
    reg [1:0] state;
    integer i;

    wire [3:0] opcode  = instr[7:4];
    wire [3:0] operand = instr[3:0];

    wire [3:0] alu_result;
    alu u_alu (
        .op(opcode), .a(acc), .b(operand),
        .y(alu_result), .zero(zero), .carry(carry)
    );

    initial begin
        $readmemh(PROGRAM_FILE, prog);
        for (i = 0; i < WORDS; i = i + 1)
            mem[i] = 4'h0;
    end

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            acc    <= 4'h0;
            pc     <= 4'h0;
            halted <= 1'b0;
            instr  <= 8'h00;
            state  <= FETCH;
        end else if (!halted) begin
            case (state)
                FETCH: begin
                    instr <= prog[pc];
                    pc    <= pc + 4'd1;
                    state <= EXECUTE;
                end
                EXECUTE: begin
                    case (opcode)
                        OP_LDI: acc <= operand;
                        OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR: acc <= alu_result;
                        OP_NOT: acc <= ~acc;
                        OP_STA: mem[operand] <= acc;
                        OP_LDA: acc <= mem[operand];
                        OP_JMP: pc <= operand;
                        OP_JZ:  if (zero) pc <= operand;
                        OP_HLT: halted <= 1'b1;
                        default: ; // NOP
                    endcase
                    state <= FETCH;
                end
                default: state <= FETCH;
            endcase
        end
    end
endmodule
