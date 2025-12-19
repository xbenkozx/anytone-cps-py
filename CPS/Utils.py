from decimal import Decimal

class Format:
    def roundFrequency(frequency: Decimal) -> Decimal:
        freq = frequency * 100000
        return Decimal(5 * round(freq / 5)) / 100000
class Bit:
    def getBit(char, index) -> bool:
        return ((char >> index) & 1) == 1
    
    def setBit(char, index, val):
        if val == 0 or val == False:
            mask = 1 << index
            inverted_mask = ~mask
            return char & inverted_mask
        else:
            return char | (1 << index)
        
    