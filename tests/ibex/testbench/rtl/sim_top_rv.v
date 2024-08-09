module sim_top
   (input wire clk,
    input wire rst, // active high reset
    output wire [31:0] gpio);

    sim dut(clk, rst, gpio);

endmodule