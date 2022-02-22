import secrets


bit_size = 250
bits = secrets.randbits(bit_size)

print(bits)
bin_ascii = bin(bits)[2:].zfill(bit_size)
print("Binary String: ", bin_ascii)
print("Binary lenght: ", len(bin_ascii))
num_ones_array = bin_ascii.count('1')
print("Number of 'ones': ", num_ones_array)
