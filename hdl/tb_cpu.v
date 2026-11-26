// Self-checking testbench for the reference CPU running program.hex.
`timescale 1ns/1ps

module tb_cpu;
    reg  clk = 1'b0;
    reg  reset = 1'b1;
    wire [3:0] acc, pc;
    wire halted, zero, carry;
    integer cycle;

    cpu dut (
        .clk(clk), .reset(reset), .acc(acc), .pc(pc),
        .halted(halted), .zero(zero), .carry(carry)
    );

    always #5 clk = ~clk;

    initial begin
        repeat (3) @(posedge clk);
        #1 reset = 1'b0;
        repeat (40) @(posedge clk);
        #1;
        if (acc !== 4'h3 || pc !== 4'hA || halted !== 1'b1 || dut.mem[0] !== 4'hC) begin
            $display("FAIL tb_cpu: acc=%h pc=%h halted=%b mem[0]=%h",
                     acc, pc, halted, dut.mem[0]);
        end else begin
            $display("PASS tb_cpu: acc=%h pc=%h halted=%b mem[0]=%h",
                     acc, pc, halted, dut.mem[0]);
        end
        $finish;
    end
endmodule
