-- 控制器模块 (VHDL)
-- 对应问题：5.1.8.1 建议准则A-8-1 - 实体名称与文件名不一致

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- 第45行 - 实体名称与文件名不一致
-- 文件名是controller.vhd，但实体名是ctrl_unit
entity ctrl_unit is
    Port (
        clk : in STD_LOGIC;
        rst : in STD_LOGIC;
        enable : in STD_LOGIC;
        status : out STD_LOGIC_VECTOR(3 downto 0);
        done : out STD_LOGIC
    );
end ctrl_unit;

architecture Behavioral of ctrl_unit is
    type state_type is (IDLE, RUN, WAIT_STATE, FINISH);
    signal current_state : state_type;
    signal counter : unsigned(7 downto 0);
begin
    process(clk, rst)
    begin
        if rst = '1' then
            current_state <= IDLE;
            counter <= (others => '0');
            done <= '0';
            status <= (others => '0');
        elsif rising_edge(clk) then
            case current_state is
                when IDLE =>
                    if enable = '1' then
                        current_state <= RUN;
                    end if;
                when RUN =>
                    counter <= counter + 1;
                    if counter = 255 then
                        current_state <= FINISH;
                    end if;
                when WAIT_STATE =>
                    current_state <= RUN;
                when FINISH =>
                    done <= '1';
                    current_state <= IDLE;
            end case;
        end if;
    end process;
end Behavioral;

entity extra_unit is
    Port (
        a : in STD_LOGIC;
        y : out STD_LOGIC
    );
end extra_unit;

architecture rtl of extra_unit is
begin
    y <= a;
end rtl;
