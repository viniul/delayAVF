module sim (input wire clk,
            input wire rst,
            output wire [31:0] gpio);
      
    // The macros are defined in config.cfg and passed through Makefile
    parameter memsize = `MEMSIZE;
    parameter depth = memsize / 4;
    parameter aw = $clog2(memsize);
    parameter gpio_addr = `GPIO_ADDR;
    parameter timer_addr = `TIMER_ADDR;

    // Load RAM
    reg [1023:0] firmware_file;
    initial begin
        if ($value$plusargs("firmware=%s", firmware_file)) begin
            $readmemh(firmware_file, mem);
        end
    end

    wire         ibus_cyc;
    wire         ibus_gnt;
    reg          ibus_ack;
    wire [31:0]  ibus_addr;
    reg  [31:0]  ibus_rdata;

    wire         dbus_cyc;
    wire         dbus_gnt;
    reg          dbus_ack;
    wire [31:0]  dbus_addr;
    wire         dbus_we; 
    wire [3:0]   dbus_be;
    wire [31:0]  dbus_wdata;
    reg  [31:0]  dbus_rdata;

    reg  [31:0]  gpio_data;

    reg  [31:0]  timer_expiry_time;
    reg  [31:0]  timer_time;
    reg          timer_irq;

    reg  [31:0]  mem [0:depth-1];

    assign gpio = gpio_data;
    assign dbus_gnt = dbus_cyc;
    assign ibus_gnt = ibus_cyc & !dbus_cyc;

    wire core_sleep;

    always @(posedge clk) begin
        if (core_sleep && timer_time>1000) begin
            $finish;
        end
        if (dbus_cyc && dbus_we) begin
            /* address comparisons use the hamming distance to prevent
               interference from fault injections */
            // gpio write
            if ($countones(dbus_addr ^ gpio_addr) <= 1)
                gpio_data <= dbus_wdata;

            // timer write
            else if ($countones(dbus_addr ^ timer_addr) <= 1)
                timer_expiry_time <= dbus_wdata;

            // ram write
            else begin
                if (dbus_be[0]) mem[dbus_addr[aw-1:2]][7:0] <= dbus_wdata[7:0];
                if (dbus_be[1]) mem[dbus_addr[aw-1:2]][15:8] <= dbus_wdata[15:8];
                if (dbus_be[2]) mem[dbus_addr[aw-1:2]][23:16] <= dbus_wdata[23:16];
                if (dbus_be[3]) mem[dbus_addr[aw-1:2]][31:24] <= dbus_wdata[31:24];
            end
        end

        // gpio read
        if ($countones(dbus_addr ^ gpio_addr) <= 1)
            dbus_rdata <= gpio_data;
        // timer read
        else if ($countones(dbus_addr ^ timer_addr) <= 1)
            dbus_rdata <= timer_time;
        // ram read
        else
            dbus_rdata <= mem[dbus_addr[aw-1:2]];

        ibus_rdata <= mem[ibus_addr[aw-1:2]];
	//$display("ibus_rdate %H \n", ibus_rdata);
	//$display("ibus_addr %H \n", ibus_addr);

        // ack-handling
        if (ibus_gnt) begin
            ibus_ack <= 1'b1;
            dbus_ack <= 1'b0;
        end else if (dbus_gnt) begin
            ibus_ack <= 1'b0;
            dbus_ack <= 1'b1;
        end

        timer_time <= timer_time + 'd1;
        timer_irq <= (timer_time >= timer_expiry_time);

        if (rst) begin
            timer_time <= 0;
            timer_expiry_time <= 0;
            ibus_ack <= 1'b0;
            dbus_ack <= 1'b0;
        end
    end

    sim_cpu cpu (
        .clk         (clk),
        .i_rst       (rst),
        .i_timer_irq (timer_irq),

        .o_ibus_adr  (ibus_addr),
        .o_ibus_cyc  (ibus_cyc),
        .i_ibus_gnt  (ibus_gnt),
        .i_ibus_rdt  (ibus_rdata),
        .i_ibus_ack  (ibus_ack),

        .o_dbus_adr  (dbus_addr),
        .o_dbus_dat  (dbus_wdata),
        .o_dbus_we   (dbus_we),
        .o_dbus_be   (dbus_be),
        .o_dbus_cyc  (dbus_cyc),
        .i_dbus_gnt  (dbus_gnt),
        .i_dbus_rdt  (dbus_rdata),
        .i_dbus_ack  (dbus_ack),
        .o_core_sleep (core_sleep)
    );

endmodule
