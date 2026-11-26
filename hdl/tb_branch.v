// Self-checking testbench for taken/not-taken JZ and an unconditional JMP.
`timescale 1ns/1ps

module tb_branch;
    reg  clk = 1'b0;
    reg  reset = 1'b1;
    wire [3:0] acc, pc;
    wire halted, zero, carry;
    integer cycle;

    cpu #(.PROGRAM_FILE("program_branch.hex")) dut (
        .clk(clk), .reset(reset), .acc(acc), .pc(pc),
        .halted(halted), .zero(zero), .carry(carry)
    );

    always #5 clk = ~clk;

    initial begin
        repeat (3) @(posedge clk);
        #1 reset = 1'b0;
        repeat (40) @(posedge clk);
        #1;
        if (acc !== 4'h3 || pc !== 4'hA || halted !== 1'b1) begin
            $display("FAIL tb_branch: acc=%h pc=%h halted=%b", acc, pc, halted);
        end else begin
            $display("PASS tb_branch: acc=%h pc=%h halted=%b", acc, pc, halted);
        end
        $finish;
    end
endmodule
