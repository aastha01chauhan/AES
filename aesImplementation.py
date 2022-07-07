from pyfinite import ffield
F = ffield.FField(4)

# 6 B 5 4 2 E 7 A 9 D F C 3 1 0 8
aesSubBox = [0x6, 0xB, 0x5, 0x4, 0x2, 0xE, 0x7, 0xA, 0x9, 0xD, 0xF, 0xC, 0x3, 0x1, 0x0, 0x8]
reverseAesSubBox = [0xE, 0xD, 0x4, 0xC, 0x3, 0x2, 0x0, 0x6, 0xF, 0x8, 0x7, 0x1, 0xB, 0x9, 0x5, 0xA]

def arrayToGrid(arr):
    whole = []
    for i in range(len(arr)//16):
        a = arr[i*16: i*16 + 16]
        newGrid = [[], [], [], []]
        for i in range(4):
            for j in range(4):
                newGrid[i].append(int(a[i + j*4], 16))
        whole.append(newGrid)
    return whole

def lookupTable(byte):
    return aesSubBox[byte]

def reverseLookupTable(byte):
    return reverseAesSubBox[byte]

def padding(data):
    
    pad = bytes(16 - len(data) % 16)
    if len(pad) != 16:
        data += pad
        
    return data

def subBytes(grid):
    
    subBytesResult = [[lookupTable(val) for val in row] for row in grid]
            
    return subBytesResult 

def rotateRowLeft(row, n=1):
    
    return row[n:] + row[:n]

def shiftRows(data):
    
    shiftRowsStep = [rotateRowLeft(
                subBytes[i], i) for i in range(4)]
      
    return shiftRowsStep

def multiply_by_2(v):
    # s = v << 1
    # s &= 0xff
    # if (v & 128) != 0:
    #     s = s ^ 0x1b
    return F.Multiply(v, 2)

def multiply_by_3(v):
    
    return F.Multiply(v, 3)

def mix_columns(grid):
    
    new_grid = [[], [], [], []]
    for i in range(4):
        col = [grid[j][i] for j in range(4)]
        col = mix_column(col)
        for i in range(4):
            new_grid[i].append(col[i])
    return new_grid

def mix_column(column):
    
    r = [
        multiply_by_2(column[0]) ^ multiply_by_3(
            column[1]) ^ column[2] ^ column[3],
        multiply_by_2(column[1]) ^ multiply_by_3(
            column[2]) ^ column[3] ^ column[0],
        multiply_by_2(column[2]) ^ multiply_by_3(
            column[3]) ^ column[0] ^ column[1],
        multiply_by_2(column[3]) ^ multiply_by_3(
            column[0]) ^ column[1] ^ column[2],
    ]
    return r

def expand_key(key, rounds):

    rcon = [[1, 0, 0, 0]]

    for _ in range(1, rounds):
        rcon.append([F.Multiply(rcon[-1][0], 2), 0, 0, 0])

    key_grid = arrayToGrid(key)[0]

    for round in range(rounds):
        last_column = [row[-1] for row in key_grid]
        last_column_rotate_step = rotateRowLeft(last_column)
        last_column_sbox_step = [lookupTable(b) for b in last_column_rotate_step]
        last_column_rcon_step = [last_column_sbox_step[i]
                                 ^ rcon[round][i] for i in range(len(last_column_rotate_step))]

        for r in range(4):
            key_grid[r] += bytes([last_column_rcon_step[r]
                                  ^ key_grid[r][round*4]])

        # Three more columns to go
        for i in range(len(key_grid)):
            for j in range(1, 4):
                key_grid[i] += bytes([key_grid[i][round*4+j]
                                      ^ key_grid[i][round*4+j+3]])

    return key_grid

def extract_key_for_round(expanded_key, round):
    return [row[round*4: round*4 + 4] for row in expanded_key]

def add_sub_key(block_grid, key_grid):
    r = []

    # 4 rows in the grid
    for i in range(4):
        r.append([])
        # 4 values on each row
        for j in range(4):
            r[-1].append(block_grid[i][j] ^ key_grid[i][j])
    return r

def enc(key, data):
    #applying padding
    data = padding(data)
    
    #changing to grids
    grids = arrayToGrid(data)
    expanded_key = expand_key(key, 11)
    temp_grids = []
    round_key = extract_key_for_round(expanded_key, 0)
    for round in range(1, 10):
        temp_grids = []
        
        for grid in grids:
            sub_bytes_step = subBytes(grid)
            shift_rows_step = [rotateRowLeft(
                sub_bytes_step[i], i) for i in range(4)]
            mix_column_step = mix_columns(shift_rows_step)
            round_key = extract_key_for_round(expanded_key, round)
            add_sub_key_step = add_sub_key(mix_column_step, round_key)
            temp_grids.append(add_sub_key_step)

        grids = temp_grids

    # A final round without the mix columns
    temp_grids = []
    round_key = extract_key_for_round(expanded_key, 10)

    for grid in grids:
        sub_bytes_step = subBytes(grid)
        shift_rows_step = [rotateRowLeft(
            sub_bytes_step[i], i) for i in range(4)]
        add_sub_key_step = add_sub_key(shift_rows_step, round_key)
        temp_grids.append(add_sub_key_step)

    grids = temp_grids

    int_stream = []
    
    for grid in grids:
        for column in range(4):
            for row in range(4):
                int_stream.append(grid[row][column])

    return int_stream

x = enc('10001011011110111', '898a842ba51ee2af')
for i in x:
  print(hex(i)[2:], sep="", end="")
    
            

    










        