from decimal import Decimal

class Format:
    def roundFrequency(frequency: Decimal) -> Decimal:
        freq = frequency * 100000
        return Decimal(5 * round(freq / 5)) / 100000
class Bit:
    def getBit(char, index) -> bool:
        return ((char >> index) & 1) == 1
    def setBit(char, index, val):
        char += (val << index)
        return char
    