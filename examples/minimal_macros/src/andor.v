// y = (a & b) | c
module andor (
  input clk,
  input nrst,

  input a,
  input b,
  input c,

  output reg y
);

  reg and_out;
  reg andor_out;

  bit_and and_macro (
    .clk(clk),
    .nrst(nrst),
    .a(a),
    .b(b),
    .y(and_out)
  );

  bit_or or_macro (
    .clk(clk),
    .nrst(nrst),
    .a(and_out),
    .b(c),
    .y(andor_out)
  );

  always @ (posedge clk or negedge nrst)
    if (!nrst)
      y <= 'b0;
    else
      y <= andor_out;

endmodule
