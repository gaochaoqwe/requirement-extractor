// 状态机模块
// 对应问题：5.1.3.1 建议准则A-3-1 - 状态机状态命名不清晰

module state_machine (
    input wire clk,
    input wire rst_n,
    input wire start,
    output reg done
);

// 状态定义
parameter S0 = 3'b000;  // 第15行开始
parameter S1 = 3'b001;
parameter S2 = 3'b010;
parameter S3 = 3'b011;

reg [2:0] state, next_state;

// 状态寄存器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        state <= S0;
    else
        state <= next_state;
end

// 状态转移逻辑
always @(*) begin
    case (state)
        S0: begin           // 第35行 - 状态命名S0, S1不清晰，应使用IDLE, ACTIVE等
            done = 1'b0;
            if (start)
                next_state = S1;
            else
                next_state = S0;
        end
        S1: begin          // 第45行 - 状态命名不清晰
            done = 1'b0;
            next_state = S2;
        end
        S2: begin
            done = 1'b0;
            next_state = S3;
        end
        S3: begin
            done = 1'b1;
            next_state = S0;
        end
        default: next_state = S0;
    endcase
end

endmodule
