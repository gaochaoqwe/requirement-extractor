-- Bug A-1-1: 缺少标准文件头
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity debouncer is
    Generic (
        COUNTER_SIZE : integer := 19
    );
    Port ( 
        clk : in STD_LOGIC;
        rst_n : in STD_LOGIC;
        button_in : in STD_LOGIC;
        button_out : out STD_LOGIC;
        unused_port : out STD_LOGIC  -- Bug 5.1.3: 未使用的输出端口
    );
end debouncer;

architecture Behavioral of debouncer is
    signal counter : unsigned(COUNTER_SIZE-1 downto 0) := (others => '0');
    signal button_sync : STD_LOGIC_VECTOR(1 downto 0) := (others => '0');
    
    -- Bug 5.2.5: 未使用的信号
    signal unused_counter : integer := 0;
    signal extra_unused : STD_LOGIC_VECTOR(7 downto 0);
    
    -- Bug 5.9.1.b: 过度嵌套的信号定义
    signal nested_sig1 : STD_LOGIC;
    signal nested_sig2 : STD_LOGIC;
    signal nested_sig3 : STD_LOGIC;
    
begin
    -- Bug A-1-2: 缩进不一致
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            button_sync <= (others => '0');
        elsif rising_edge(clk) then
button_sync(0) <= button_in;  -- 缩进错误
            button_sync(1) <= button_sync(0);
        end if;
    end process;
    
    -- Bug 5.9.1.b: 过度嵌套的逻辑
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            counter <= (others => '0');
            button_out <= '0';
        elsif rising_edge(clk) then
            if button_sync(1) = '1' then
                if counter < 2**COUNTER_SIZE-1 then
                    if counter > 100 then
                        if counter < 500 then
                            counter <= counter + 1;
                        else
                            counter <= counter + 1;
                        end if;
                    else
                        counter <= counter + 1;
                    end if;
                else
                    button_out <= '1';
                end if;
            else
                counter <= (others => '0');
                button_out <= '0';
            end if;
        end if;
    end process;
    
    -- Bug 5.2.5: 多余代码
    unused_counter <= to_integer(counter);
    extra_unused <= (others => '0');
    
    -- Bug 5.9.1.b: 不必要的复杂层次
    nested_sig1 <= button_in;
    nested_sig2 <= nested_sig1;
    nested_sig3 <= nested_sig2;
    
    -- Bug 5.1.3: 未使用的输出端口赋值
    unused_port <= '0';
    
end Behavioral;
