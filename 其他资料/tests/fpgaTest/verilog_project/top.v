// 顶层模块 - 包含故意的bug用于测试
module top(
    input clk,
    input reset,
    input [7:0] data_in,
    output [7:0] data_out,
    output [7:0] count_out
);

// Bug 1: 信号位宽不匹配
wire [7:0] alu_a, alu_b;
wire [7:0] alu_result;
wire [2:0] alu_op;
wire alu_zero;

// Bug 2: 实例化时端口连接错误
counter u_counter(
    .clk(clk),
    .reset(reset),
    .enable(1'b1),
    .count(count_out),
    .overflow()  // Bug: 悬空端口
);

// Bug 3: 信号驱动冲突
assign alu_a = data_in;
assign alu_b = 8'h55;
assign alu_op = 3'b000;

alu u_alu(
    .a(alu_a),
    .b(alu_b),
    .op(alu_op),
    .result(alu_result),
    .zero_flag(alu_zero)
);

// Bug 4: 多驱动问题
assign data_out = alu_result;
assign data_out = count_out;  // 多重驱动

// Bug 5: 未使用的信号
wire unused_wire;
reg unused_reg;

endmodule 