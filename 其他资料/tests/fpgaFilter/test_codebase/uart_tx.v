// UART发送模块
// 对应问题：5.1.4.2 建议准则A-4-2 - 模块端口顺序不规范

module uart_tx (
    output reg tx,              // 第6行 - 端口顺序不规范
    output reg busy,            // 输出端口应该放在输入端口之后
    input wire clk,
    input wire rst_n,
    input wire [7:0] data,
    input wire start,
    inout wire test_pin         // 双向端口应该放在最后
);

parameter BAUD_DIV = 16;

reg [3:0] bit_cnt;
reg [7:0] shift_reg;
reg [3:0] baud_cnt;

// 第156行附近 - 端口顺序应为：输入、输出、双向
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        tx <= 1'b1;
        busy <= 1'b0;
        bit_cnt <= 4'h0;
        shift_reg <= 8'h00;
        baud_cnt <= 4'h0;
    end else if (start && !busy) begin
        busy <= 1'b1;
        shift_reg <= data;
        bit_cnt <= 4'h0;
    end else if (busy) begin
        if (baud_cnt == BAUD_DIV - 1) begin
            baud_cnt <= 4'h0;
            if (bit_cnt == 4'd9) begin
                busy <= 1'b0;
                tx <= 1'b1;
            end else begin
                tx <= shift_reg[0];
                shift_reg <= {1'b1, shift_reg[7:1]};
                bit_cnt <= bit_cnt + 1;
            end
        end else begin
            baud_cnt <= baud_cnt + 1;
        end
    end
end

endmodule

module uart_tx_probe (
    input wire tx,
    output wire seen_high
);
    assign seen_high = tx;
endmodule
