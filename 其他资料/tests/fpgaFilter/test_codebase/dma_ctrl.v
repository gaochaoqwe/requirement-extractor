// DMA控制器模块
// 对应问题：5.2.6.1 强制准则R-6-1 - 存在竞争冒险

module dma_ctrl (
    input wire clk,
    input wire rst_n,
    input wire [31:0] src_addr,
    input wire [31:0] dst_addr,
    input wire [15:0] length,
    input wire start,
    output reg [31:0] mem_addr,
    output reg mem_wr_en,
    output reg mem_rd_en,
    inout wire [31:0] mem_data,
    output reg done,
    output reg busy
);

reg [15:0] count;
reg [31:0] temp_data;
reg data_valid;

// 第189行 - 存在竞争冒险
// 多个always块可能同时修改busy信号
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        busy <= 1'b0;
        done <= 1'b0;
    end else if (start) begin
        busy <= 1'b1;  // 竞争点1
        done <= 1'b0;
    end
end

always @(posedge clk) begin
    if (count >= length) begin
        busy <= 1'b0;  // 竞争点2：与上面的always块可能产生竞争
        done <= 1'b1;
    end
end

// 读写控制也存在竞争
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 16'h0000;
        mem_rd_en <= 1'b0;
    end else if (busy) begin
        mem_addr <= src_addr + count;
        mem_rd_en <= 1'b1;
        count <= count + 1;
    end
end

always @(posedge clk) begin
    if (data_valid) begin
        mem_addr <= dst_addr + count;  // 竞争：mem_addr在多个always块中被赋值
        mem_wr_en <= 1'b1;
    end
end

endmodule
