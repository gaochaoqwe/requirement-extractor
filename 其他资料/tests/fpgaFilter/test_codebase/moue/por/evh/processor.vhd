-- 处理器模块 (VHDL)
-- 对应问题：5.2.5.2 强制准则R-5-2 - 进程敏感列表缺少信号

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity processor is
    Port (
        clk : in STD_LOGIC;
        rst_n : in STD_LOGIC;
        data_in : in STD_LOGIC_VECTOR(15 downto 0);
        addr : in STD_LOGIC_VECTOR(7 downto 0);
        wr_en : in STD_LOGIC;
        data_out : out STD_LOGIC_VECTOR(15 downto 0);
        status : out STD_LOGIC_VECTOR(3 downto 0)
    );
end processor;

architecture Behavioral of processor is
    signal internal_reg : STD_LOGIC_VECTOR(15 downto 0);
    signal addr_reg : STD_LOGIC_VECTOR(7 downto 0);
    signal status_reg : STD_LOGIC_VECTOR(3 downto 0);
    -- 为触发 5.3.1 规则，增加一个组合逻辑信号
    signal comb_sig : STD_LOGIC_VECTOR(3 downto 0);
begin
    -- 第78行 - 进程敏感列表缺少信号
    -- 进程中使用了data_in, addr, wr_en，但敏感列表中缺少这些信号
    process(clk)  -- 缺少rst_n, data_in, addr, wr_en
    begin
        if rising_edge(clk) then
            if rst_n = '0' then
                internal_reg <= (others => '0');
                addr_reg <= (others => '0');
                status_reg <= (others => '0');
            else
                if wr_en = '1' then
                    internal_reg <= data_in;
                    addr_reg <= addr;
                end if;
                status_reg <= addr(3 downto 0);
            end if;
        end if;
    end process;
    
    data_out <= internal_reg;
    status <= status_reg;

    -- 违规：5.3.1 进程中敏感列表信号应完整、正确
    -- 使用了 wr_en 和 addr，但敏感列表只包含 addr，缺少 wr_en
    process(addr)
    begin
        if wr_en = '1' then
            comb_sig <= addr(3 downto 0);
        else
            comb_sig <= (others => '0');
        end if;
    end process;
end Behavioral;
