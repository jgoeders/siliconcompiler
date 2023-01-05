module bit_or (
  input clk,
  input nrst,

  input a,
  input b,

  output reg y
);

  always @ (posedge clk or negedge nrst)
    if (!nrst)
      y <= 'b0;
    else
      y <= (a | b);

endmodule
