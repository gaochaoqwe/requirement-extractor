"""
Number format conversion utilities for DOCX numbering.
"""

import re
from typing import Dict, List, Tuple


class NumberFormatConverter:
    """Utility class for converting integers to various numbering formats."""
    
    # Traditional Chinese characters for numbering
    IDEOGRAPH_TRADITIONAL = "甲乙丙丁戊己庚辛壬癸"
    IDEOGRAPH_ZODIAC = "子丑寅卯辰巳午未申酉戌亥"
    
    @staticmethod
    def int_to_upper_letter(num: int) -> str:
        """Convert integer to uppercase letters (A, B, C, ..., Z, AA, AB, ...)."""
        if num <= 0:
            raise ValueError("Number must be positive")
        
        result = []
        while num > 0:
            num -= 1
            remainder = num % 26
            result.append(chr(remainder + ord('A')))
            num //= 26
        return "".join(reversed(result))
    
    @staticmethod
    def int_to_upper_roman(num: int) -> str:
        """Convert integer to uppercase Roman numerals."""
        if num <= 0 or num > 3999:
            raise ValueError("Number must be between 1 and 3999 for Roman numerals")
        
        values = [
            (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
        ]
        
        roman_num = ''
        for value, symbol in values:
            count = num // value
            if count:
                roman_num += symbol * count
                num -= value * count
        
        return roman_num
    
    @staticmethod
    def int_to_cardinal_text(num: int) -> str:
        """Convert integer to cardinal text (One, Two, Three, ...)."""
        if not isinstance(num, int) or num < 0 or num > 999999999:
            raise ValueError("Number must be a positive integer within reasonable range")
        
        if num == 0:
            return "Zero"
        
        base = [
            "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"
        ]
        
        tens = [
            "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
        ]
        
        thousands = ["", "Thousand", "Million", "Billion"]
        
        def convert_hundreds(n):
            if n == 0:
                return ""
            elif n < 20:
                return base[n]
            elif n < 100:
                ten, unit = divmod(n, 10)
                return tens[ten] + ("-" + base[unit] if unit else "")
            else:
                hundred, rest = divmod(n, 100)
                result = base[hundred] + " Hundred"
                if rest:
                    result += " " + convert_hundreds(rest)
                return result
        
        if num < 100:
            return convert_hundreds(num)
        
        chunks = []
        while num > 0:
            num, remainder = divmod(num, 1000)
            chunks.append(remainder)
        
        words = []
        for i in range(len(chunks) - 1, -1, -1):
            if chunks[i] == 0:
                continue
            chunk_word = convert_hundreds(chunks[i])
            if thousands[i]:
                chunk_word += " " + thousands[i]
            words.append(chunk_word)
        
        return " ".join(words)
    
    @staticmethod
    def int_to_ordinal_text(num: int) -> str:
        """Convert integer to ordinal text (First, Second, Third, ...)."""
        if not isinstance(num, int) or num < 1 or num > 999999:
            raise ValueError("Number must be a positive integer within reasonable range")
        
        # Special cases for 1-20
        ordinals = [
            "", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth",
            "Tenth", "Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth",
            "Seventeenth", "Eighteenth", "Nineteenth", "Twentieth"
        ]
        
        if num <= 20:
            return ordinals[num]
        
        # For larger numbers, convert to cardinal and modify ending
        cardinal = NumberFormatConverter.int_to_cardinal_text(num)
        
        # Handle special cases for ordinal endings
        if cardinal.endswith("One"):
            return cardinal[:-3] + "First"
        elif cardinal.endswith("Two"):
            return cardinal[:-3] + "Second"
        elif cardinal.endswith("Three"):
            return cardinal[:-5] + "Third"
        elif cardinal.endswith("Five"):
            return cardinal[:-4] + "Fifth"
        elif cardinal.endswith("Eight"):
            return cardinal[:-5] + "Eighth"
        elif cardinal.endswith("Nine"):
            return cardinal[:-4] + "Ninth"
        elif cardinal.endswith("Twelve"):
            return cardinal[:-6] + "Twelfth"
        elif cardinal.endswith("Twenty"):
            return cardinal[:-6] + "Twentieth"
        elif cardinal.endswith("Thirty"):
            return cardinal[:-6] + "Thirtieth"
        elif cardinal.endswith("Forty"):
            return cardinal[:-5] + "Fortieth"
        elif cardinal.endswith("Fifty"):
            return cardinal[:-5] + "Fiftieth"
        elif cardinal.endswith("Sixty"):
            return cardinal[:-5] + "Sixtieth"
        elif cardinal.endswith("Seventy"):
            return cardinal[:-7] + "Seventieth"
        elif cardinal.endswith("Eighty"):
            return cardinal[:-6] + "Eightieth"
        elif cardinal.endswith("Ninety"):
            return cardinal[:-6] + "Ninetieth"
        else:
            return cardinal + "th"
    
    @staticmethod
    def int_to_chinese(num: int, ch_num: str, units: str) -> str:
        """Convert integer to Chinese numerals."""
        if not (0 <= num <= 99999999):
            raise ValueError("Number must be between 0 and 99,999,999")
        
        if num == 0:
            return ch_num[0]
        
        def convert_within_10000(n):
            if n == 0:
                return ch_num[0]
            
            digits = [int(d) for d in str(n).zfill(4)]
            result = ""
            
            for i, digit in enumerate(digits):
                if digit != 0:
                    result += ch_num[digit] + units[3-i]
            
            # Clean up zeros and units
            zero_char = ch_num[0]
            result = re.sub(f"(?:{zero_char}[{units}])+", zero_char, result)
            result = result.rstrip(units[0])
            
            if result != zero_char:
                result = result.rstrip(zero_char)
            
            # Handle special case for "十" (ten)
            if result.startswith(ch_num[1] + units[1]):
                result = result[1:]
            
            return result
        
        if num < 10000:
            return convert_within_10000(num)
        else:
            left = num // 10000
            right = num % 10000
            result = convert_within_10000(left) + "万"
            if right > 0:
                result += convert_within_10000(right)
            return result
    
    @staticmethod
    def int_to_chinese_counting(num: int) -> str:
        """Convert integer to Chinese counting numerals."""
        return NumberFormatConverter.int_to_chinese(num, "〇一二三四五六七八九", "个十百千")
    
    @staticmethod
    def int_to_chinese_legal_simplified(num: int) -> str:
        """Convert integer to Chinese legal simplified numerals."""
        return NumberFormatConverter.int_to_chinese(num, "零壹贰叁肆伍陆柒捌玖", "个拾佰仟")