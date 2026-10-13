// ALU 算术逻辑单元
// 对应问题：5.2.1.1 强制准则R-1-1 - 存在组合逻辑环路

module alu (
    input wire [7:0] a,
    input wire [7:0] b,
    input wire [2:0] op,
    output reg [7:0] result,
    output reg zero
);

wire [7:0] temp_result;

// 组合逻辑
always @(*) begin
    case (op)
        3'b000: result = a + b;
        3'b001: result = a - b;
        3'b010: result = a & b;
        3'b011: result = a | b;
        3'b100: result = a ^ b;
        3'b101: result = ~a;
        3'b110: result = a << 1;
        3'b111: result = a >> 1;
        default: result = 8'h00;
    endcase
end

// 第67行 - 存在组合逻辑环路
assign temp_result = (zero) ? 8'h00 : result;  // 这里temp_result依赖zero，而zero又依赖result，形成环路

always @(*) begin
    zero = (temp_result == 8'h00);  // 组合逻辑环路
end

endmodule

module alu_monitor (
    input wire [7:0] value,
    output wire active
);
    assign active = |value;
endmodule
