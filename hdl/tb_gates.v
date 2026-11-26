// Self-checking testbench for the structural gate library.
`timescale 1ns/1ps

module tb_gates;
    reg  a, b;
    wire y_not, y_and, y_nand, y_or, y_nor, y_xor;
    integer errors = 0;
    integer i;

    cmos_not  u_not  (.a(a),       .y(y_not));
    cmos_and  u_and  (.a(a), .b(b), .y(y_and));
    cmos_nand u_nand (.a(a), .b(b), .y(y_nand));
    cmos_or   u_or   (.a(a), .b(b), .y(y_or));
    cmos_nor  u_nor  (.a(a), .b(b), .y(y_nor));
    cmos_xor  u_xor  (.a(a), .b(b), .y(y_xor));

    task check;
        input expected_not, expected_and, expected_nand;
        input expected_or,  expected_nor,  expected_xor;
        begin
            #1;
            if (y_not  !== expected_not)  begin $display("FAIL not  a=%b got %b", a, y_not);  errors = errors + 1; end
            if (y_and  !== expected_and)  begin $display("FAIL and  a=%b b=%b got %b", a, b, y_and);  errors = errors + 1; end
            if (y_nand !== expected_nand) begin $display("FAIL nand a=%b b=%b got %b", a, b, y_nand); errors = errors + 1; end
            if (y_or   !== expected_or)   begin $display("FAIL or   a=%b b=%b got %b", a, b, y_or);   errors = errors + 1; end
            if (y_nor  !== expected_nor)  begin $display("FAIL nor  a=%b b=%b got %b", a, b, y_nor);  errors = errors + 1; end
            if (y_xor  !== expected_xor)  begin $display("FAIL xor  a=%b b=%b got %b", a, b, y_xor);  errors = errors + 1; end
        end
    endtask

    initial begin
        for (i = 0; i < 4; i = i + 1) begin
            a = i[1]; b = i[0];
            check(~a, a & b, ~(a & b), a | b, ~(a | b), a ^ b);
        end
        if (errors == 0)
            $display("PASS tb_gates (6 gates x 4 input vectors)");
        else
            $display("FAIL tb_gates (%0d errors)", errors);
        $finish;
    end
endmodule
