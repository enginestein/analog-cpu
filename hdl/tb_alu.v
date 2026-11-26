// Self-checking testbench for the 4-bit ALU.
`timescale 1ns/1ps

module tb_alu;
    localparam [3:0] PASS = 4'h0, ADD = 4'h1, SUB = 4'h2, AND = 4'h3,
                     OR = 4'h4, XOR = 4'h5, NOT = 4'h6;

    reg  [3:0] op, a, b;
    wire [3:0] y;
    wire zero, carry;
    reg  [3:0] expected;
    integer errors = 0;
    integer i, j;

    alu u_alu (.op(op), .a(a), .b(b), .y(y), .zero(zero), .carry(carry));

    task check_op;
        input expected_carry;
        input verify_carry;  // carry is only meaningful for ADD/SUB
        begin
            #1;
            if (y !== expected) begin
                $display("FAIL op=%h a=%h b=%h expected %h got %h", op, a, b, expected, y);
                errors = errors + 1;
            end
            if (zero !== (expected == 4'h0)) begin
                $display("FAIL zero flag op=%h a=%h b=%h", op, a, b);
                errors = errors + 1;
            end
            if (verify_carry && carry !== expected_carry) begin
                $display("FAIL carry op=%h a=%h b=%h expected %b got %b",
                         op, a, b, expected_carry, carry);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        // A few representative vectors per operation, including carry out.
        a = 4'h9; b = 4'h3;
        op = PASS; expected = 4'h9; check_op(1'b0, 1'b0);
        op = ADD;  expected = 4'hC; check_op(1'b0, 1'b1);
        op = SUB;  expected = 4'h6; check_op(1'b1, 1'b1);  // no borrow
        op = AND;  expected = 4'h1; check_op(1'b0, 1'b0);
        op = OR;   expected = 4'hB; check_op(1'b0, 1'b0);
        op = XOR;  expected = 4'hA; check_op(1'b0, 1'b0);
        op = NOT;  expected = 4'h6; check_op(1'b0, 1'b0);

        a = 4'hF; b = 4'h1;
        op = ADD;  expected = 4'h0; check_op(1'b1, 1'b1);  // wraps, carry out
        op = SUB;  expected = 4'hE; check_op(1'b1, 1'b1);  // no borrow
        op = AND;  expected = 4'h1; check_op(1'b0, 1'b0);
        op = XOR;  expected = 4'hE; check_op(1'b0, 1'b0);

        // Exhaustive check of the logic operations over all 256 vector pairs.
        for (i = 0; i < 16; i = i + 1) begin
            for (j = 0; j < 16; j = j + 1) begin
                a = i[3:0]; b = j[3:0];
                op = AND; expected = a & b; check_op(1'b0, 1'b0);
                op = OR;  expected = a | b; check_op(1'b0, 1'b0);
                op = XOR; expected = a ^ b; check_op(1'b0, 1'b0);
            end
        end

        if (errors == 0)
            $display("PASS tb_alu");
        else
            $display("FAIL tb_alu (%0d errors)", errors);
        $finish;
    end
endmodule
