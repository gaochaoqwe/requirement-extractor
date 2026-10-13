-- 8位计数器实体 - 包含故意的bug用于测试
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity counter is
    Port ( 
        clk : in STD_LOGIC;
        reset : in STD_LOGIC;
        enable : in STD_LOGIC;
        count : out STD_LOGIC_VECTOR (7 downto 0);
        overflow : out STD_LOGIC
    );
end counter;

architecture Behavioral of counter is
    signal count_reg : unsigned(7 downto 0) := (others => '0');
    -- Bug 1: 未使用的信号
    signal unused_signal : STD_LOGIC;
    signal temp_count : unsigned(7 downto 0);
begin
    -- Bug 2: 敏感列表不完整
    process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then
                count_reg <= (others => '0');
            elsif enable = '1' then
                count_reg <= count_reg + 1;
            end if;
        end if;
    end process;
    
    -- Bug 3: 类型转换错误
    count <= STD_LOGIC_VECTOR(count_reg);
    
    -- Bug 4: 组合逻辑没有完整的敏感列表
    process(count_reg)
    begin
        if count_reg = "11111111" then
            overflow <= '1';
        else
            overflow <= '0';
        end if;
    end process;
    
    -- Bug 5: 信号赋值但未使用
    temp_count <= count_reg + 1;
    
end Behavioral; 