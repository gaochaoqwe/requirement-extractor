// Bug A-1-1: 缺少标准文件头
module clock_divider #(
    parameter DIVIDE_RATIO = 100
)(
    input clk_in,
    input rst_n,
    output reg clk_out
);

// Bug 5.9.1.a: 使用魔术数字而不是有意义的常量
reg [6:0] counter;

// Bug A-1-2: 缩进不一致
always @(posedge clk_in or negedge rst_n) begin
    if (!rst_n) begin
        counter <= 7'b0;
    end else begin
        if (counter >= DIVIDE_RATIO - 1) begin
        counter <= 7'b0;  // 缩进错误
            clk_out <= ~clk_out;
        end else begin
counter <= counter + 1;  // 缩进错误
        end
    end
end

// Bug 5.2.5: 多余的未使用代码
reg [3:0] unused_counter;
always @(posedge clk_in) begin
    unused_counter <= unused_counter + 1;
end

endmodule
