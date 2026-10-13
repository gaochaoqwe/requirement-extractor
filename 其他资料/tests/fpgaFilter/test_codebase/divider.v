// 除法器模块
// 对应问题：5.2.4.3 强制准则R-4-3 - 除零未做保护

module divider (
    input wire clk,
    input wire rst_n,
    input wire [15:0] dividend,
    input wire [7:0] divisor,
    input wire start,
    output reg [15:0] quotient,
    output reg [7:0] remainder,
    output reg done,
    output reg error
);

reg busy;
reg [4:0] cnt;
reg [15:0] temp_dividend;
reg [15:0] temp_divisor;

// 第334行 - 除零未做保护
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        quotient <= 16'h0000;
        remainder <= 8'h00;
        done <= 1'b0;
        error <= 1'b0;
        busy <= 1'b0;
        cnt <= 5'h00;
    end else if (start && !busy) begin
        busy <= 1'b1;
        done <= 1'b0;
        // 错误：没有检查除数是否为零
        temp_dividend <= dividend;
        temp_divisor <= {8'h00, divisor};  // 直接使用divisor，没有检查是否为0
        cnt <= 5'h00;
    end else if (busy) begin
        if (cnt < 16) begin
            temp_dividend <= {temp_dividend[14:0], 1'b0};
            if (temp_dividend >= temp_divisor) begin
                temp_dividend <= temp_dividend - temp_divisor;
                quotient[15-cnt] <= 1'b1;
            end else begin
                quotient[15-cnt] <= 1'b0;
            end
            cnt <= cnt + 1;
        end else begin
            remainder <= temp_dividend[7:0];
            done <= 1'b1;
            busy <= 1'b0;
        end
    end
end

endmodule
