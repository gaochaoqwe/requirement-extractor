// 数据通路模块
// 对应问题：5.2.4.1 强制准则R-4-1 - 使用了阻塞赋值在时序逻辑中

module data_path (
    input wire clk,
    input wire rst_n,
    input wire [15:0] data_in,
    input wire valid_in,
    output reg [15:0] data_out,
    output reg valid_out
);

reg [15:0] stage1_data;
reg [15:0] stage2_data;
reg stage1_valid;
reg stage2_valid;

// 第134行 - 时序逻辑中使用了阻塞赋值
// 应该使用非阻塞赋值 (<=) 而不是阻塞赋值 (=)
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        stage1_data = 16'h0000;   // 错误：时序逻辑应使用 <=
        stage1_valid = 1'b0;      // 错误：时序逻辑应使用 <=
        stage2_data = 16'h0000;   // 错误：时序逻辑应使用 <=
        stage2_valid = 1'b0;      // 错误：时序逻辑应使用 <=
        data_out = 16'h0000;      // 错误：时序逻辑应使用 <=
        valid_out = 1'b0;         // 错误：时序逻辑应使用 <=
    end else begin
        stage1_data = data_in;    // 错误：应使用 <=
        stage1_valid = valid_in;
        stage2_data = stage1_data;
        stage2_valid = stage1_valid;
        data_out = stage2_data;
        valid_out = stage2_valid;
    end
end

endmodule
