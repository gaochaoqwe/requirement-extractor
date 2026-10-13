// 乘法器模块
// 对应问题：5.2.3.5 强制准则R-3-5 - 未考虑溢出情况

module multiplier (
    input wire clk,
    input wire rst_n,
    input wire [7:0] a,
    input wire [7:0] b,
    input wire start,
    output reg [7:0] result,  // 注意：结果位宽不够
    output reg done,
    output reg overflow
);

reg [15:0] temp_result;
reg busy;

// 第312行 - 未考虑溢出情况
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        result <= 8'h00;
        done <= 1'b0;
        overflow <= 1'b0;
        busy <= 1'b0;
        temp_result <= 16'h0000;
    end else if (start && !busy) begin
        busy <= 1'b1;
        done <= 1'b0;
        temp_result <= a * b;  // 8位乘8位可能产生16位结果
    end else if (busy) begin
        // 错误：直接截断到8位，没有检测溢出
        result <= temp_result[7:0];  // 溢出未检测！
        done <= 1'b1;
        busy <= 1'b0;
        // 应该检查 temp_result[15:8] != 0 表示溢出
    end
end

endmodule
