-- 简单ALU实体 - 包含故意的bug用于测试
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity alu is
    Port ( 
        a : in STD_LOGIC_VECTOR (7 downto 0);
        b : in STD_LOGIC_VECTOR (7 downto 0);
        op : in STD_LOGIC_VECTOR (2 downto 0);
        result : out STD_LOGIC_VECTOR (7 downto 0);
        zero_flag : out STD_LOGIC
    );
end alu;

architecture Behavioral of alu is
    signal temp_result : STD_LOGIC_VECTOR (7 downto 0);
    -- Bug 1: 位宽不匹配
    signal carry : STD_LOGIC_VECTOR (8 downto 0);
begin
    -- Bug 2: case语句没有others分支
    process(a, b, op)
    begin
        case op is
            when "000" => temp_result <= STD_LOGIC_VECTOR(unsigned(a) + unsigned(b));
            when "001" => temp_result <= STD_LOGIC_VECTOR(unsigned(a) - unsigned(b));
            when "010" => temp_result <= a and b;
            when "011" => temp_result <= a or b;
            when "100" => temp_result <= a xor b;
            when "101" => temp_result <= not a;
            when "110" => temp_result <= a(6 downto 0) & '0';
            -- Bug 3: 缺少others分支
        end case;
    end process;
    
    -- Bug 4: 信号驱动冲突
    result <= temp_result;
    result <= (others => '0');  -- 多重驱动
    
    -- Bug 5: 类型转换问题
    process(temp_result)
    begin
        if unsigned(temp_result) = 0 then  -- Bug: 类型不匹配
            zero_flag <= '1';
        else
            zero_flag <= '0';
        end if;
    end process;
    
    -- Bug 6: 未使用的信号赋值
    carry <= STD_LOGIC_VECTOR(unsigned('0' & a) + unsigned('0' & b));
    
end Behavioral; 