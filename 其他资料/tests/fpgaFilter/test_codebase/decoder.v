// 译码器模块
// 对应问题：5.1.6.1 建议准则A-6-1 - case语句缺少default分支

module decoder (
    input wire [2:0] sel,
    input wire enable,
    output reg [7:0] out
);

// 第267行 - case语句缺少default分支
always @(*) begin
    if (enable) begin
        case (sel)
            3'b000: out = 8'b00000001;
            3'b001: out = 8'b00000010;
            3'b010: out = 8'b00000100;
            3'b011: out = 8'b00001000;
            3'b100: out = 8'b00010000;
            3'b101: out = 8'b00100000;
            3'b110: out = 8'b01000000;
            3'b111: out = 8'b10000000;
            // 缺少default分支，应该添加以提高代码健壮性
        endcase
    end else begin
        out = 8'b00000000;
    end
end

endmodule
