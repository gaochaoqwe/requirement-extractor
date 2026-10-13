// Bug A-1-1: 缺少标准文件头
module system_top(
    input clk,
    input rst_n,
    input button,
    input [7:0] spi_data_in,
    output [7:0] uart_data_out,
    output spi_sclk,
    output spi_mosi,
    input spi_miso,
    output spi_cs_n,
    output uart_tx
);

wire clk_div;
wire button_clean;
wire [7:0] spi_rx_data;
wire spi_done;
wire uart_tx_start;
wire uart_tx_done;

// Bug 5.2.5: 存在多余未使用的信号和代码
wire unused_signal;
reg [7:0] unused_reg;
wire extra_unused;
reg [15:0] more_unused;

// Bug 5.2.4: 顶层含有非连续赋值（组合逻辑）
reg [7:0] temp_data;
always @(*) begin
    temp_data = spi_data_in + 8'h01;
end

// Bug A-1-2: 缩进不一致
clock_divider #(
    .DIVIDE_RATIO(100)
) u_clk_div (
.clk_in(clk),  // 缩进错误
    .rst_n(rst_n),
        .clk_out(clk_div)  // 缩进错误
);

// Bug 5.1.3: 例化时未使用输出端口，应该使用open语法但没有
debouncer u_debouncer (
    .clk(clk),
    .rst_n(rst_n),
    .button_in(button),
    .button_out(button_clean)
    // .unused_port() 未连接的输出端口
);

// Bug 5.2.10: 多重驱动
assign uart_tx_start = button_clean;
assign uart_tx_start = spi_done;

spi_master u_spi (
    .clk(clk),
    .rst_n(rst_n),
    .start(button_clean),
    .tx_data(spi_data_in),
    .rx_data(spi_rx_data),
    .sclk(spi_sclk),
    .mosi(spi_mosi),
    .miso(spi_miso),
    .cs_n(spi_cs_n),
    .done(spi_done)
);

uart_tx u_uart (
    .clk(clk),
    .rst_n(rst_n),
    .tx_start(uart_tx_start),
    .tx_data(spi_rx_data),
    .tx_serial(uart_tx),
    .tx_done(uart_tx_done)
);

assign uart_data_out = spi_rx_data;

// Bug 5.2.5: 信号赋值但未使用
assign unused_signal = uart_tx_done;
assign extra_unused = button_clean & spi_done;

// Bug A-1-2: 缩进不一致
    always @(posedge clk) begin
        if (rst_n) begin
unused_reg <= 8'hAA;  // 缩进错误
        end
    end

endmodule

// Bug 5.2.10: 在同一个文件中定义多个模块
module dummy_module(
    input clk,
    output reg out
);
always @(posedge clk) begin
    out <= ~out;
end
endmodule
