-- 简单RAM实体 - 包含故意的bug用于测试
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity ram is
    Generic (
        ADDR_WIDTH : integer := 8;
        DATA_WIDTH : integer := 8
    );
    Port ( 
        clk : in STD_LOGIC;
        we : in STD_LOGIC;
        addr : in STD_LOGIC_VECTOR (ADDR_WIDTH-1 downto 0);
        data_in : in STD_LOGIC_VECTOR (DATA_WIDTH-1 downto 0);
        data_out : out STD_LOGIC_VECTOR (DATA_WIDTH-1 downto 0)
    );
end ram;

architecture Behavioral of ram is
    -- Bug 1: 数组大小错误
    type ram_type is array (0 to 2**ADDR_WIDTH-2) of STD_LOGIC_VECTOR(DATA_WIDTH-1 downto 0);
    signal ram_data : ram_type := (others => (others => '0'));
    -- Bug 2: 未使用的信号
    signal unused_addr : STD_LOGIC_VECTOR(ADDR_WIDTH-1 downto 0);
begin
    -- Bug 3: 读写逻辑混乱
    process(clk)
    begin
        if rising_edge(clk) then
            if we = '1' then
                ram_data(to_integer(unsigned(addr))) <= data_in;
                -- Bug 4: 在写操作中也进行读操作
                data_out <= ram_data(to_integer(unsigned(addr)));
            end if;
        end if;
    end process;
    
    -- Bug 5: 异步读操作可能导致竞争
    process(addr)
    begin
        data_out <= ram_data(to_integer(unsigned(addr)));
    end process;
    
    -- Bug 6: 信号赋值但未使用
    unused_addr <= addr;
    
end Behavioral; 