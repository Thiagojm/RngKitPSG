from bitstring import BitArray, BitStream
import secrets
import numpy


bit_size = 15
my_byte = secrets.token_bytes(int(bit_size/8))

# com bitstring
print("Bitstring")

a = BitArray(my_byte)

print(a.bin, a.bin.count("1"))

# Python
print("Pure Python")
int_val = int.from_bytes(my_byte, "big")
int_ascii = bin(int_val)[2:].zfill(bit_size)
print(int_ascii)
