// 时钟分频器模块
// 对应问题：5.1.1.5 建议准则A-1-5 - 时钟信号命名不规范

module clock_divider (
    input wire sys_clk,
    input wire rst_n,
    output reg clk_out
);

parameter DIV_FACTOR = 4;

reg [3:0] counter;


wire clock_signal;  // 第15行 - 时钟信号命名不规范，应使用clk前缀

always @(posedge sys_clk or negedge rst_n) begin
    if (!rst_n) begin
        counter <= 4'b0;
        clk_out <= 1'b0;
    end else begin
        if (counter == DIV_FACTOR - 1) begin
            counter <= 4'b0;
            clk_out <= ~clk_out;
        end else begin
            counter <= counter + 1;
        end
    end
end

assign clock_signal = clk_out;

endmodule
