// 内存控制器模块
// 对应问题：5.2.3.2 强制准则R-3-2 - 复位信号未正确连接

module memory_ctrl (
    input wire clk,
    input wire rst_n,
    input wire [7:0] addr,
    input wire [7:0] data_in,
    input wire wr_en,
    output reg [7:0] data_out
);

reg [7:0] memory [0:255];
reg [7:0] addr_reg;
reg wr_en_reg;

// 第102行 - 复位信号未正确连接
// 这些寄存器没有连接复位信号，存在隐患
always @(posedge clk) begin  // 缺少 or negedge rst_n
    addr_reg <= addr;
    wr_en_reg <= wr_en;
end

always @(posedge clk) begin  // 缺少复位
    if (wr_en_reg) begin
        memory[addr_reg] <= data_in;
    end
    data_out <= memory[addr_reg];
end

endmodule
