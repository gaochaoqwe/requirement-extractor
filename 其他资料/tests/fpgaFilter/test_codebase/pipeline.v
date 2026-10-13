// 流水线模块
// 对应问题：5.2.1.3 强制准则R-1-3 - 存在锁存器推断

module pipeline (
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    input wire [2:0] op_code,
    output reg [7:0] data_out
);

reg [7:0] stage1_data;
reg [7:0] stage2_data;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        stage1_data <= 8'h00;
    end else begin
        stage1_data <= data_in;
    end
end

// 第223行 - 组合逻辑中存在锁存器推断
// case语句没有覆盖所有情况，会推断出锁存器
always @(*) begin
    case (op_code)
        3'b000: stage2_data = stage1_data;
        3'b001: stage2_data = stage1_data + 1;
        3'b010: stage2_data = stage1_data - 1;
        // 缺少其他case分支，没有default，会推断锁存器
    endcase
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_out <= 8'h00;
    end else begin
        data_out <= stage2_data;
    end
end

endmodule
