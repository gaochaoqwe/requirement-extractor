// 总线接口模块
// 对应问题：5.1.9.3 建议准则A-9-3 - 总线信号命名不规范

module bus_interface (
    input wire clk,
    input wire rst_n,
    // 第156行附近 - 总线信号命名不规范
    input wire [31:0] d,        // 不规范：应使用bus_data或类似命名
    input wire [15:0] a,        // 不规范：应使用bus_addr
    input wire w,               // 不规范：应使用bus_wr_en
    input wire r,               // 不规范：应使用bus_rd_en
    input wire v,               // 不规范：应使用bus_valid
    output reg [31:0] q,        // 不规范：应使用bus_data_out
    output reg rdy              // 不规范：应使用bus_ready
);

reg [31:0] data_reg;
reg [15:0] addr_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_reg <= 32'h00000000;
        addr_reg <= 16'h0000;
        q <= 32'h00000000;
        rdy <= 1'b0;
    end else begin
        if (w && v) begin
            data_reg <= d;
            addr_reg <= a;
            rdy <= 1'b1;
        end else if (r && v) begin
            q <= data_reg;
            rdy <= 1'b1;
        end else begin
            rdy <= 1'b0;
        end
    end
end

endmodule
