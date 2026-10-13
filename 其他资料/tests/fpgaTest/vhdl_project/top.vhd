-- 顶层实体 - 包含故意的bug用于测试
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity top is
    Port ( 
        clk : in STD_LOGIC;
        reset : in STD_LOGIC;
        data_in : in STD_LOGIC_VECTOR (7 downto 0);
        data_out : out STD_LOGIC_VECTOR (7 downto 0);
        count_out : out STD_LOGIC_VECTOR (7 downto 0)
    );
end top;

architecture Behavioral of top is
    -- 组件声明
    component counter
        Port ( 
            clk : in STD_LOGIC;
            reset : in STD_LOGIC;
            enable : in STD_LOGIC;
            count : out STD_LOGIC_VECTOR (7 downto 0);
            overflow : out STD_LOGIC
        );
    end component;
    
    component alu
        Port ( 
            a : in STD_LOGIC_VECTOR (7 downto 0);
            b : in STD_LOGIC_VECTOR (7 downto 0);
            op : in STD_LOGIC_VECTOR (2 downto 0);
            result : out STD_LOGIC_VECTOR (7 downto 0);
            zero_flag : out STD_LOGIC
        );
    end component;
    
    -- 信号声明
    signal alu_a, alu_b : STD_LOGIC_VECTOR (7 downto 0);
    signal alu_result : STD_LOGIC_VECTOR (7 downto 0);
    signal alu_op : STD_LOGIC_VECTOR (2 downto 0);
    signal alu_zero : STD_LOGIC;
    signal overflow_sig : STD_LOGIC;
    -- Bug 1: 未使用的信号
    signal unused_signal : STD_LOGIC;
    
begin
    -- Bug 2: 端口映射错误
    u_counter : counter
        port map (
            clk => clk,
            reset => reset,
            enable => '1',
            count => count_out,
            overflow => open  -- Bug: 应该连接到信号
        );
    
    -- Bug 3: 信号驱动冲突
    alu_a <= data_in;
    alu_b <= x"55";
    alu_op <= "000";
    
    u_alu : alu
        port map (
            a => alu_a,
            b => alu_b,
            op => alu_op,
            result => alu_result,
            zero_flag => alu_zero
        );
    
    -- Bug 4: 多重驱动
    data_out <= alu_result;
    data_out <= count_out;  -- 多重驱动
    
    -- Bug 5: 信号赋值但未使用
    unused_signal <= alu_zero;
    
end Behavioral; 