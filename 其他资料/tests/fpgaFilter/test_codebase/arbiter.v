// 仲裁器模块
// 对应问题：5.2.2.1 强制准则R-2-1 - 信号位宽不匹配

module arbiter (
    input wire clk,
    input wire rst_n,
    input wire [3:0] request,
    output reg [1:0] grant,
    output reg grant_valid
);

reg [2:0] priority;  // 3位寄存器

// 第245行 - 信号位宽不匹配
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        grant <= 2'b00;
        grant_valid <= 1'b0;
        priority <= 3'b000;
    end else begin
        if (request[0]) begin
            grant <= 2'b00;
            grant_valid <= 1'b1;
            priority <= request;  // 错误：4位的request赋值给3位的priority
        end else if (request[1]) begin
            grant <= 2'b01;
            grant_valid <= 1'b1;
        end else if (request[2]) begin
            grant <= 2'b10;
            grant_valid <= 1'b1;
        end else if (request[3]) begin
            grant <= 2'b11;
            grant_valid <= 1'b1;
        end else begin
            grant_valid <= 1'b0;
        end
    end
end

endmodule
