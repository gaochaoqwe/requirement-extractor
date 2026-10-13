// 简单ALU模块 - 包含故意的bug用于测试
module alu(
    input [7:0] a,
    input [7:0] b,
    input [2:0] op,
    output reg [7:0] result,
    output zero_flag
);

// Bug 1: case语句没有default分支
always @(*) begin
    case (op)
        3'b000: result = a + b;
        3'b001: result = a - b;
        3'b010: result = a & b;
        3'b011: result = a | b;
        3'b100: result = a ^ b;
        3'b101: result = ~a;
        3'b110: result = a << 1;
        // Bug 2: 缺少default分支
    endcase
end

// Bug 3: 组合逻辑使用了阻塞赋值
always @(*) begin
    if (result == 8'b0)
        zero_flag = 1'b1;  // 应该使用非阻塞赋值
    else
        zero_flag = 1'b0;
end

// Bug 4: 位宽不匹配
wire [7:0] temp_result;
assign temp_result = a + b + 1'b1;  // 可能溢出

endmodule 