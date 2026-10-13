// 简单FIFO模块 - 包含故意的bug用于测试
module fifo #(
    parameter DEPTH = 16,
    parameter WIDTH = 8
)(
    input clk,
    input rst_n,
    input wr_en,
    input rd_en,
    input [WIDTH-1:0] data_in,
    output reg [WIDTH-1:0] data_out,
    output full,
    output empty
);

// Bug 1: 参数使用错误的位宽
reg [3:0] wr_ptr;  // 应该是 [4:0] 才能表示0-16
reg [3:0] rd_ptr;  // 应该是 [4:0] 才能表示0-16
reg [WIDTH-1:0] mem [0:DEPTH-1];

// Bug 2: 复位逻辑不完整
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        wr_ptr <= 4'b0;
        rd_ptr <= 4'b0;
        // Bug 3: 没有复位data_out
    end else begin
        if (wr_en && !full) begin
            mem[wr_ptr] <= data_in;
            wr_ptr <= wr_ptr + 1;
        end
        if (rd_en && !empty) begin
            data_out <= mem[rd_ptr];
            rd_ptr <= rd_ptr + 1;
        end
    end
end

// Bug 4: 状态标志逻辑错误
assign full = (wr_ptr == rd_ptr);  // 错误的full逻辑
assign empty = (wr_ptr == rd_ptr); // 错误的empty逻辑

endmodule 