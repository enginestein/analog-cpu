// One bit of the ripple-carry adder used by the ALU. Built from the same
// primitive gates that the CMOS gate library implements.

module full_adder (
    input  wire a,
    input  wire b,
    input  wire cin,
    output wire sum,
    output wire cout
);
    wire a_xor_b;
    wire ab;
    wire axb_cin;

    xor u_xor1 (a_xor_b, a, b);
    xor u_xor2 (sum, a_xor_b, cin);
    and u_and1 (ab, a, b);
    and u_and2 (axb_cin, a_xor_b, cin);
    or  u_or1  (cout, ab, axb_cin);
endmodule
