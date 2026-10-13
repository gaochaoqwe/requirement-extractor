// FIFO缓冲器模块
// 对应问题：5.2.2.5 强制准则R-2-5 - 时钟域交叉未做同步处理

module fifo (
    input wire wr_clk,
    input wire rd_clk,
    input wire rst_n,
    input wire wr_en,
    input wire rd_en,
    input wire [7:0] din,
    output reg [7:0] dout,
    output reg full,
    output reg empty
);

reg [3:0] wr_ptr, rd_ptr;
reg [7:0] mem [0:15];

// 写时钟域
always @(posedge wr_clk or negedge rst_n) begin
    if (!rst_n) begin
        wr_ptr <= 4'b0;
    end else if (wr_en && !full) begin
        mem[wr_ptr] <= din;
        wr_ptr <= wr_ptr + 1;
    end
end

// 读时钟域
always @(posedge rd_clk or negedge rst_n) begin
    if (!rst_n) begin
        rd_ptr <= 4'b0;
    end else if (rd_en && !empty) begin
        dout <= mem[rd_ptr];
        rd_ptr <= rd_ptr + 1;
    end
end

// 第89行 - 时钟域交叉未做同步处理
// 直接在不同时钟域之间比较指针，没有做CDC同步
always @(*) begin
    full = (wr_ptr == rd_ptr - 1);   // 跨时钟域比较，危险！
    empty = (wr_ptr == rd_ptr);       // 跨时钟域比较，危险！
end

endmodule
