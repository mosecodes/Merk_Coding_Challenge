"""
Script for parsing sixtysix files
"""
import numpy as np
import os
import pandas as pd
import math
import struct
import matplotlib.pyplot as plt
from rainbow.datafile import DataFile


def read_file_a(file_path):
    """
    Read the file at file_path and return the xlabels, active columns, and data as numpy arrays.

    :param file_path: Path to the file

    :return:
        xlabels: ndarray, dtype = (float, prec=4),
        active columns: ndarray, dtype = (uint16 tuples with shape (value, length)),
        data: numpy array of uint8 values
    """
    name = os.path.relpath(file_path)
    print(f'\nParsing file \\{name}')
    with open(file_path, 'rb') as f:
        raw_bytes = f.read()

    # GET XLABELS FROM COLUMNS [4:8] OF THE FILE
    width = 10
    # calculate the total number of rows, ensuring integer division
    length = len(raw_bytes) // width

    # create a ndarray from raw_bytes with the shape of (length, width)
    # keeping the default dtype of uint8
    try:
        full_array = np.frombuffer(raw_bytes, dtype='uint8').reshape(length, width)
    except ValueError as e:
        print(f'Error creating full array in file {name}: {e}')
        raise ValueError(e)

    # extract the xlabels from the full array, converting to rounded floats
    # and put the first 4 columns of the full array in a data variable
    try:
        # create an array of the [4:8] split of each row of the full array
        offsets, xlabels_data, num_cols = np.hsplit(full_array, [4, 8])

        # create a byte buffer from the xlabels_data
        xlabels_buffer = xlabels_data.tobytes()

        # create a 1D array from the xlabels_buffer
        xlabels_array = np.frombuffer(xlabels_buffer, dtype='>I').astype('float32') / 60000
        # print(f'\tShape of xlabels array: {xlabels_array.shape}')

        # round the xlabels_array to 4 decimal places
        xlabels = np.round(xlabels_array, 4)

    except ValueError as e:
        print(f'Error creating xlabels array in file {name}: {e}')
        raise ValueError(e)


    # GET DATA FROM DATA ARRAY
    data_bytes = offsets.tobytes()
    offsets_arr = np.frombuffer(data_bytes, dtype='>I')

    return xlabels, offsets_arr


def read_file_b(file_path):
    """
    Reads a .B file, puts the data through a parsing function, and returns the transformed data.

    :param file_path: Path to the file
    :return: DataFrame of the transformed data
    """
    name = os.path.relpath(file_path)
    print(f'Parsing file \\{name}')
    with open(file_path, 'rb') as f:
        raw_bytes = f.read()
        ylabels = []
        for i in range(len(raw_bytes) // 6):
            f.seek(i * 6)
            value = struct.unpack('<H', f.read(2))[0]
            if value not in ylabels:
                ylabels.append(value)

        ylabels = np.sort(ylabels)

    # print(f'\tByte-length of {name}: {len(raw_bytes)}')

    return ylabels


def read_file_c(file_path):
    """
    Read the file at file_path and return the data transformation key as an uint8
    :param file_path: Path to the file
    :return: np.uint8 (should be Unicode character 'C' or 'B')
    """
    name = os.path.relpath(file_path)
    print(f'Parsing file \\{name}')
    with open(file_path, 'rb') as f:
        f.seek(4)
        file_format = f.read(1)
    # print the file format as a utf-8 string
    # print(f'\tFile format string: {file_format.decode("utf-8")}')
    # print(f'\tFile format as uint8: {np.frombuffer(file_format, dtype="uint8")[0]}\n')
    # return the file format as an uint8
    return np.frombuffer(file_format, dtype='uint8')[0]


def parse_sixtysix(folder_path):
    """
    Parse the sixtysix files in the folder at folder_path. Return the xlabels, ylabels, and data as numpy arrays. \
    Also return the key from the file C as a uint8.
    :param folder_path: Path to the folder
    :return: xlabels, ylabels, data, key
    """
    # parse files A, B, and C
    file_a_path = os.path.join(os.getcwd(), folder_path, 'sixtysix.A')
    xlabels, offsets = read_file_a(file_a_path)

    file_b_path = os.path.join(os.getcwd(), folder_path, 'sixtysix.B')
    ylabels = read_file_b(file_b_path)

    file_c_path = os.path.join(os.getcwd(), folder_path, 'sixtysix.C')
    c_key = (read_file_c(file_c_path))

    """
    Create the data array from the xlabels, ylabels, and offsets
    File A holds offsets to read file B data from for every xlabel, \
    the offset is the first 4 bytes of the row in file A, and corresponds \
    to the row in file B where the data for that xlabel is stored. \
    
    The last two bytes of each 10 byte sequence in file A are the number \
    of active columns for that xlabel. 
    """
    a = open(file_a_path, 'rb')
    b = open(file_b_path, 'rb')

    data_rows = []

    # read data for each xlabel
    for i in range(xlabels.size):
        # get the B offset from file A
        b_offset = struct.unpack('>I', a.read(4))[0]
        # get the xlabel from file A
        xlabel = np.round(((struct.unpack('>I', a.read(4))[0]) / 60000), 4)
        # get the number of active columns from file A
        num_cols = struct.unpack('>H', a.read(2))[0]

        # make empty row
        row_data = [0] * len(ylabels)

        # move to the B offset in file B
        b.seek(b_offset)
        # read number of active columns from file B
        for _ in range(num_cols):
            # get the column number from file B
            ylabel = struct.unpack('<H', b.read(2))[0]
            # get the data from file B
            value = struct.unpack('<I', b.read(4))[0]
            # get index of ylabel in ylabels
            index = np.where(ylabels == ylabel)[0][0]
            # print(f'Index of {ylabel} in ylabels: {index}\n'
            #       f'number of ylabels: {len(ylabels)}')
            # add value to row_data at index
            row_data[index] = value

        data_rows.append(row_data)
        # print(f'Row {xlabel} done')

    # make data from second column of data_rows
    data = np.array(data_rows)

    a.close()
    b.close()

    return xlabels, ylabels, data, c_key


def main():
    """
    Main function for parsing the sixtysix files
    :return: None
    """
    # create directory of folder paths
    cwd = os.getcwd()
    datadir_path = os.path.join(cwd, 'datadir')
    folder_paths = [os.path.join(datadir_path, folder) for folder in os.listdir(datadir_path)]

    # create list of DataFiles
    solution_list = []
    for path in folder_paths:
        xlabels, ylabels, data, key = parse_sixtysix(path)
        dfile = DataFile(path, 'MS', xlabels, ylabels, data, {'format': key})
        solution_list.append(dfile)

    # create directory with csv files for evaluation
    solution_path = os.path.join(cwd, 'csv_files')
    try:
        os.mkdir(solution_path)
        print(f'\nmade solution folder at ./{os.path.basename(solution_path)}')
    except FileExistsError:
        print(f'\nfolder already exists at ./{os.path.basename(solution_path)}\n'
              f'\tdelete the folder to create a new one.')

    # add solution files to directory
    for df in solution_list:
        file_name = df.name + '_solution'
        path = os.path.join(solution_path, file_name)
        if not os.path.exists(path):
            df.export_csv(path)
            print(f'wrote {file_name} to {os.path.basename(solution_path)}')
        else:
            print(f'{file_name} already exists in {os.path.basename(solution_path)}\n'
                  f'\tdelete the file to write a new one.')


if __name__ == '__main__':
    main()
