// 编码器模块
// 对应问题：5.1.7.2 建议准则A-7-2 - 参数定义未使用parameter关键字

module encoder (
    input wire [7:0] in,
    output reg [2:0] out,
    output reg valid
);

// 第289行 - 应使用parameter或localparam定义常量
`define BUS_WIDTH 8  // 不推荐使用宏定义，应使用parameter

always @(*) begin
    valid = 1'b0;
    out = 3'b000;
    
    if (in[0]) begin
        out = 3'b000;
        valid = 1'b1;
    end else if (in[1]) begin
        out = 3'b001;
        valid = 1'b1;
    end else if (in[2]) begin
        out = 3'b010;
        valid = 1'b1;
    end else if (in[3]) begin
        out = 3'b011;
        valid = 1'b1;
    end else if (in[4]) begin
        out = 3'b100;
        valid = 1'b1;
    end else if (in[5]) begin
        out = 3'b101;
        valid = 1'b1;
    end else if (in[6]) begin
        out = 3'b110;
        valid = 1'b1;
    end else if (in[7]) begin
        out = 3'b111;
        valid = 1'b1;
    end
end

endmodule
