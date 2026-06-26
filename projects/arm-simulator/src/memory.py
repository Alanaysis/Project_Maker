"""
ARM Memory Simulator Module
============================

Implements a simplified memory model for the ARM simulator:
- 32-bit addressable memory (simulated as a dict)
- Byte and word access
- Big-endian and little-endian support (ARM is typically little-endian)
- Memory alignment checking

ARM Architecture Background:
ARM uses a Load/Store architecture:
- Only LDR/STR instructions can access memory
- All other operations are on registers
- Memory addresses are byte-addressable
- ARM processors can be big-endian or little-endian
- This simulator defaults to little-endian (most common in embedded ARM)
"""


class Memory:
    """Simplified ARM memory simulator"""

    def __init__(self, size=0x10000):
        """
        Initialize memory with given size.

        Args:
            size: Memory size in bytes (default 64KB)
        """
        self.size = size
        self.memory = {}  # Sparse memory: address -> byte value

    def _normalize_address(self, address):
        """Normalize address to valid range"""
        return address & (self.size - 1) if self.size > 0 else address

    def write_byte(self, address, value):
        """Write a single byte to memory"""
        address = self._normalize_address(address)
        if 0 <= address < self.size:
            self.memory[address] = value & 0xFF

    def write_word(self, address, value):
        """Write a 32-bit word to memory (little-endian)"""
        address = self._normalize_address(address)
        for i in range(4):
            self.write_byte(address + i, (value >> (8 * i)) & 0xFF)

    def read_byte(self, address):
        """Read a single byte from memory"""
        address = self._normalize_address(address)
        if 0 <= address < self.size:
            return self.memory.get(address, 0)
        return 0

    def read_word(self, address):
        """
        Read a 32-bit word from memory (little-endian)

        Returns:
            32-bit unsigned integer value
        """
        address = self._normalize_address(address)
        value = 0
        for i in range(4):
            byte_addr = address + i
            if 0 <= byte_addr < self.size:
                byte_val = self.memory.get(byte_addr, 0)
            else:
                byte_val = 0
            value |= (byte_val << (8 * i))
        return value

    def write_string(self, address, string):
        """Write a null-terminated string to memory"""
        for i, char in enumerate(string):
            self.write_byte(address + i, ord(char))
        self.write_byte(address + len(string), 0)  # Null terminator

    def read_string(self, address):
        """Read a null-terminated string from memory"""
        result = []
        while True:
            byte = self.read_byte(address)
            if byte == 0:
                break
            result.append(chr(byte))
            address += 1
        return ''.join(result)

    def dump(self, start=0, length=256):
        """
        Dump memory contents in hex format.

        Args:
            start: Starting address
            length: Number of bytes to dump

        Returns:
            String with memory dump
        """
        lines = []
        for i in range(0, length, 16):
            addr = start + i
            hex_parts = []
            ascii_parts = []
            for j in range(16):
                byte_addr = addr + j
                if 0 <= byte_addr < self.size:
                    byte_val = self.memory.get(byte_addr, 0)
                else:
                    byte_val = 0
                hex_parts.append(f"{byte_val:02X}")
                ascii_parts.append(chr(byte_val) if 32 <= byte_val < 127 else '.')
            lines.append(f"  0x{addr:08X}: {' '.join(hex_parts)}  {''.join(ascii_parts)}")
        return '\n'.join(lines)

    def write_words(self, address, values):
        """Write multiple 32-bit words to memory"""
        for i, val in enumerate(values):
            self.write_word(address + (i * 4), val)

    def read_words(self, address, count):
        """Read multiple 32-bit words from memory"""
        return [self.read_word(address + (i * 4)) for i in range(count)]

    def __repr__(self):
        return f"Memory(size={self.size:#x}, entries={len(self.memory)})"
