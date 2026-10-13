// Bug A-1-1: 缺少标准文件头（无作者、日期、版本等信息）
module spi_master(
    input clk,
    input rst_n,
    input start,
    input [7:0] tx_data,
    output reg [7:0] rx_data,
    output reg sclk,
    output reg mosi,
    input miso,
    output reg cs_n,
    output reg done
);

// Bug 5.9.1.a: 状态机状态定义使用魔术数字，无意义的索引码
parameter IDLE = 2'b00;
parameter ACTIVE = 2'b01;
parameter DONE = 2'b10;

reg [1:0] state;
reg [2:0] bit_count;
reg [7:0] shift_reg;

// Bug A-1-2: 缩进不一致
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        sclk <= 1'b0;
    end else begin
sclk <= ~sclk;  // 缩进错误
    end
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        bit_count <= 3'b0;
        done <= 1'b0;
        cs_n <= 1'b1;
    end else begin
        case (state)
            IDLE: begin
                if (start) begin
        state <= ACTIVE;  // Bug A-1-2: 缩进错误
                    shift_reg <= tx_data;
      bit_count <= 3'b0;  // Bug A-1-2: 缩进错误
                    cs_n <= 1'b0;
                end
            end
            ACTIVE: begin
                if (bit_count == 3'b111) begin
                    state <= DONE;
    done <= 1'b1;  // Bug A-1-2: 缩进错误
                    cs_n <= 1'b1;
                end else begin
                    bit_count <= bit_count + 1;
                end
            end
        endcase
    end
end

always @(posedge sclk) begin
    if (state == ACTIVE) begin
        mosi <= shift_reg[7];
        shift_reg <= shift_reg << 1;
        rx_data[bit_count] <= miso;
    end
end

// Bug 5.2.5: 多余代码
reg [3:0] unused_count;
always @(posedge clk) begin
    unused_count <= unused_count + 1;
end

endmodule
