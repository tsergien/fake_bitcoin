def to_bbits(num):
    exponent = 0
    mantisa = num
    while(mantisa > 2**24):
            exponent += 1
            mantisa = mantisa // 256    
    return f'0x{exponent:0x}{mantisa:06x}'

print(to_bbits(0x168fd00000000000000000000000000000000000000000000000000000000))

