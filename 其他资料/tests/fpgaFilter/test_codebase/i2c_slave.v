// I2C从机模块
// 对应问题：5.2.5.4 强制准则R-5-4 - 敏感列表不完整

module i2c_slave (
    input wire scl,
    inout wire sda,
    input wire rst_n,
    output reg [7:0] rx_data,
    output reg data_valid
);

reg [7:0] shift_reg;
reg [2:0] bit_cnt;
reg sda_out;
reg sda_oe;

assign sda = sda_oe ? sda_out : 1'bz;

// 第201行 - 敏感列表不完整
// always块中使用了scl, rst_n, sda等信号，但敏感列表不完整
always @(posedge scl) begin  // 缺少rst_n和sda
    if (!rst_n) begin
        shift_reg <= 8'h00;
        bit_cnt <= 3'b0;
        data_valid <= 1'b0;
    end else begin
        shift_reg <= {shift_reg[6:0], sda};
        bit_cnt <= bit_cnt + 1;
        if (bit_cnt == 3'd7) begin
            rx_data <= {shift_reg[6:0], sda};
            data_valid <= 1'b1;
        end else begin
            data_valid <= 1'b0;
        end
    end
end

endmodule
