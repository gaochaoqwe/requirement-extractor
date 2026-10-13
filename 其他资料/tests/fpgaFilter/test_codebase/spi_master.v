// SPI主机模块
// 对应问题：5.1.5.3 建议准则A-5-3 - 缺少必要的注释说明

module spi_master (
    input wire clk,
    input wire rst_n,
    input wire [7:0] tx_data,
    input wire start,
    output reg sclk,
    output reg mosi,
    input wire miso,
    output reg [7:0] rx_data,
    output reg done
);

reg [3:0] bit_counter;
reg [7:0] tx_shift_reg;
reg [7:0] rx_shift_reg;
reg active;

// 第178行附近 - 缺少模块功能说明、端口描述、时序说明等
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        sclk <= 1'b0;
        mosi <= 1'b0;
        rx_data <= 8'h00;
        done <= 1'b0;
        bit_counter <= 4'h0;
        tx_shift_reg <= 8'h00;
        rx_shift_reg <= 8'h00;
        active <= 1'b0;
    end else if (start && !active) begin
        active <= 1'b1;
        tx_shift_reg <= tx_data;
        bit_counter <= 4'h0;
        done <= 1'b0;
    end else if (active) begin
        if (bit_counter < 8) begin
            sclk <= ~sclk;
            if (sclk) begin
                mosi <= tx_shift_reg[7];
                tx_shift_reg <= {tx_shift_reg[6:0], 1'b0};
            end else begin
                rx_shift_reg <= {rx_shift_reg[6:0], miso};
                bit_counter <= bit_counter + 1;
            end
        end else begin
            active <= 1'b0;
            done <= 1'b1;
            rx_data <= rx_shift_reg;
        end
    end
end

endmodule
