// 计数器模块
// 对应问题：5.1.2.3 建议准则A-2-3 - 复位信号命名不规范

module counter (
    input wire clk,
    input wire reset,      // 第7行 - 复位信号命名不规范
    input wire enable,
    output reg [7:0] count
);

always @(posedge clk or posedge reset) begin
    if (reset) begin
        count <= 8'h00;
    end else if (enable) begin
        count <= count + 1;
    end
end





wire reset_signal;     // 第23行 - 建议使用rst后缀
assign reset_signal = reset;

endmodule
