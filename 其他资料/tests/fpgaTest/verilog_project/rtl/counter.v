// 8位计数器模块 - 包含故意的bug用于测试
module counter(
    input clk,
    input reset,
    input enable,
    output reg [7:0] count,
    output overflow
);

// Bug 1: 缺少always块的敏感列表
always @(posedge clk) begin
    if (reset) begin
        count <= 8'b0;
    end else if (enable) begin
        count <= count + 1;
    end
end

// Bug 2: 组合逻辑没有使用always_comb
assign overflow = (count == 8'hFF) ? 1'b1 : 1'b0;

// Bug 3: 未使用的信号
wire unused_signal;
reg [3:0] unused_reg;

endmodule 