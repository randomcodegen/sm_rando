
# i is the int from which to get bits (one byte)
# n is the number of bits to get
# p is where to start getting them from (indexed from 0 is the high bit of i)
def get_n_bits(i, n, p):
    end = (8 - n - p)
    assert end >= 0
    mask = (2**n - 1) << end
    return (i & mask) >> end

def decompress(src, debug=False):
    dst = b""
    index = 0
    while True:
        #print(index)
        next_cmd = src[index]
        if next_cmd == 0xff:
            break
        # The command code is the top 3 bits
        cmd_code = get_n_bits(next_cmd, 3, 0)
        if cmd_code == 7:
            # An extended command uses the next 3 bits for the actual command
            cmd_code = get_n_bits(next_cmd, 3, 3)
            # Get the integer which is the last 10 bits of the 2-byte command
            n_bytes = [next_cmd & 0b11, src[index+1]]
            n = int.from_bytes(n_bytes, byteorder='big')
            # Set the index higher - the argument bytes will be collected from after
            # the 2-byte code
            index += 2
        else:
            n = get_n_bits(next_cmd, 5, 3)
            index += 1
        # Arg is adjusted by 1 since ex. direct_copy 0 copies 1 byte
        adj_n = n + 1
        # Find the alg to use
        if cmd_code == 0:
            cmd = direct_copy
        elif cmd_code == 1:
            cmd = bytefill
        elif cmd_code == 2:
            cmd = wordfill
        elif cmd_code == 3:
            cmd = sigmafill
        elif cmd_code == 4:
            cmd = addr_copy
        elif cmd_code == 5:
            cmd = addr_xor_copy
        elif cmd_code == 6:
            cmd = rel_addr_copy
        else:
            assert False, "Bad cmd_code: " + str(cmd_code)
        # Use the cmd to compute the new bytes of dst
        # and the new index into src (the index of the next command)
        new, index = cmd(adj_n, index, src, dst, debug)
        # Add the decoded bytes to the dst
        dst += new
    return dst

def direct_copy(n, index, src, dst, debug):
    arg = src[index:index+n]
    if debug:
        print("DIRECTCOPY", len(dst), len(dst) + n)
    return arg, index + n

def bytefill(n, index, src, dst, debug):
    arg = src[index:index+1]
    if debug:
        print("BYTEFILL", len(dst), len(dst) + n)
    return (n * arg), index+1

def n_bytes_of_word(n, word):
    whole = n // 2
    half = n % 2
    out = whole * word + half * word[0:1]
    return out

def wordfill(n, index, src, dst, debug):
    arg = src[index:index+2]
    if debug:
        print("WORDFILL", len(dst), len(dst) + n)
    return n_bytes_of_word(n, arg), index+2

def sigmafill(n, index, src, dst, debug):
    arg = src[index]
    out = b""
    for i in range(n):
        argi = arg + i % 255
        out += argi.to_bytes(1, byteorder='big')
    if debug:
        print("SIGMAFILL", len(dst), len(dst) + n)
    return out, index+1

def addr_copy(n, index, src, dst, debug):
    arg_bytes = src[index:index+2]
    arg = int.from_bytes(arg_bytes, byteorder='big')
    to_copy = dst[arg:arg+n]
    if debug:
        print("ADDRCPY", arg, len(dst), len(dst) + n)
        print(to_copy)
    return to_copy, index+2

def map_bytes(op, byte):
    out = b""
    for b in byte:
        b_int = int.from_bytes(b, byteorder='big')
        out += op(b_int).to_bytes(1, byteorder='big')
    return out

def addr_xor_copy(n, index, src, dst, debug):
    arg_bytes = src[index:index+2]
    arg = int.from_bytes(arg_bytes, byteorder='big')
    to_copy = dst[arg:arg+n]
    to_copy = map_bytes(lambda x: x^0xff, to_copy)
    if debug:
        print("ADDRXORCPY", arg, len(dst), len(dst) + n)
        print(to_copy)
    return to_copy, index+2

def rel_addr_copy(n, index, src, dst, debug):
    # One byte
    arg = src[index]
    # Can't used negative indexing because n-arg can be zero
    to_copy = dst[len(dst)-arg:len(dst) + n-arg]
    if debug:
        print("ADDRRELCPY", arg, len(dst), len(dst) + n)
        print(to_copy)
    return to_copy, index+1
