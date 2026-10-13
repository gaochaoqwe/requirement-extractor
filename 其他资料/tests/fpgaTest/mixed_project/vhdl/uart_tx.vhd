-- Bug A-1-1: 缺少标准文件头（无作者、日期、版本信息）
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity uart_tx is
    Generic (
        CLKS_PER_BIT : integer := 87
    );
    Port ( 
        clk : in STD_LOGIC;
        rst_n : in STD_LOGIC;
        tx_start : in STD_LOGIC;
        tx_data : in STD_LOGIC_VECTOR (7 downto 0);
        tx_serial : out STD_LOGIC;
        tx_done : out STD_LOGIC
    );
end uart_tx;

architecture Behavioral of uart_tx is
    type state_type is (IDLE, START_BIT, DATA_BITS, STOP_BIT);
    signal state : state_type := IDLE;
    
    signal clk_count : integer range 0 to CLKS_PER_BIT-1 := 0;
    signal bit_index : integer range 0 to 7 := 0;
    signal tx_data_reg : STD_LOGIC_VECTOR (7 downto 0) := (others => '0');
    
    -- Bug 5.2.5: 多余未使用的信号
    signal unused_signal : STD_LOGIC;
    signal another_unused : STD_LOGIC_VECTOR(3 downto 0);
    signal more_unused : integer := 0;
    
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst_n = '0' then
                state <= IDLE;
                clk_count <= 0;
                bit_index <= 0;
                tx_serial <= '1';
                tx_done <= '0';
            else
                case state is
                    when IDLE =>
                        tx_serial <= '1';
                        tx_done <= '0';
                        if tx_start = '1' then
        state <= START_BIT;  -- Bug A-1-2: 缩进错误
                            tx_data_reg <= tx_data;
    clk_count <= 0;  -- Bug A-1-2: 缩进错误
                        end if;
                    
                    when START_BIT =>
                        tx_serial <= '0';
                        if clk_count < CLKS_PER_BIT-1 then
                            clk_count <= clk_count + 1;
                        else
                            clk_count <= 0;
                            state <= DATA_BITS;
                            bit_index <= 0;
                        end if;
                    
                    when DATA_BITS =>
                        tx_serial <= tx_data_reg(bit_index);
                        if clk_count < CLKS_PER_BIT-1 then
                            clk_count <= clk_count + 1;
                        else
                            clk_count <= 0;
                            if bit_index < 7 then
                                bit_index <= bit_index + 1;
                            else
                                state <= STOP_BIT;
                            end if;
                        end if;
                    
                    when STOP_BIT =>
                        tx_serial <= '1';
                        if clk_count < CLKS_PER_BIT-1 then
                            clk_count <= clk_count + 1;
                        else
                            clk_count <= 0;
                            state <= IDLE;
                            tx_done <= '1';
                        end if;
                end case;
            end if;
        end if;
    end process;
    
    -- Bug 5.2.5: 多余代码
    unused_signal <= tx_start;
    another_unused <= "0000";
    more_unused <= 42;
    
end Behavioral;

-- Bug 5.2.10: 在同一文件中定义多个entity
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity dummy_entity is
    Port ( 
        clk : in STD_LOGIC;
        data_out : out STD_LOGIC
    );
end dummy_entity;

architecture Behavioral of dummy_entity is
begin
    data_out <= '0';
end Behavioral;
