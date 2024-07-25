"""
Script for parsing scale file
"""
import os
import struct
import re
import numpy as np
import rainbow as rb
from rainbow.datafile import DataFile
from rainbow.datadirectory import DataDirectory
import pandas as pd

"""
BINARY PARSING METHODS

Scale file headers have a integer divisor by which to divide all data point integers, \
    an integer tuple of (start, end, interval) from which to create an array \
    of ylabels, and integer that holds the number of xlabels.
After the header, each row of data begins with two 0x48 bytes ('H' character in ASCII) \
    and is made up of 32-bit integers for the length of the row

"""


def datafile_paths_from_dir(path):
    """
    Method for returning an array of data file paths from a directory path.

    :param path: Path of the directory

    :return: ndarray of all paths to files within the directory path
    """
    # Ensure the provided path is a directory
    if not os.path.isdir(path):
        raise ValueError(f"the path '{path}' is not a directory or does not exist.")

    # List all files in the directory (assuming no subdirectories)
    files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    # Convert the list to a ndarray
    files_arr = np.array(files)

    return files_arr


def parse_xlabels_body(values):
    """
    Split real body values into xlabels (time) and absorbance data arrays.
    This function also converts the xlabels into floats, so they can \
        accurately represent the xlabels.

    :param values: real body values

    :return: 1D ndarray of xlabels. 2D array of absorbance data where \
        rows correspond to time (xlabels) and columns correspond \
        to wavelengths (ylabels).
    """
    # split values data column-wise into xlabels (column 0) and data (the rest)
    split = np.array([1])
    xlabels_data, body_data = np.hsplit(values, split)

    # convert xlabels integers into floats
    xlabels_bytes = xlabels_data.tobytes()
    xlabels = np.frombuffer(xlabels_bytes, dtype='>f')
    assert xlabels.size == body_data.shape[0], 'Problem when splitting xlabels and body data'

    return xlabels, body_data


def create_ylabels(info):
    """
    Create an ndarray of ylabels using parsed header information

    :param info: parsed ylabels_info from file header

    :return: ndarray of ylabels
    """
    start = info[0]
    end = info[1] + 1
    interval = info[2]

    return np.arange(start, end, interval)


def parse_body(data, num_cols):
    """
    Parses data body into an array of 32-bit integers.

    :param data: byte data to parse
    :param num_cols: number of ylabels to look for (+1 for xlabels column)

    :return: 2D array of [x, ...] rows and num_cols + 1 columns, where \
            x is the unconverted xlabel for the row and the rest of \
            the row is the absorbance data for the xlabel.
    """
    row_size = 2 + (num_cols+1)*4     # 2 bytes for 'HH', (num-cols+1)*4 bytes for the 32-bit integers
    pattern = b'HH'                   # Marker for beginning of a row
    row_format = f'>{num_cols+1}i'               # 19 big-endian, signed, 32-bit integers

    # List to hold extracted rows
    rows = []

    # Current position in data
    pos = 0
    while pos < len(data):
        # Look for 'HH' marker
        if data[pos:pos+2] == pattern:
            # Extract the 19 integers after the 'HH' marker
            row_data = data[pos+2:pos+row_size]
            if len(row_data) == (num_cols+1)*4:
                integers = struct.unpack(row_format, row_data)
                rows.append(integers)
            # Move to next row
            pos += row_size
        else:
            # If no marker found, raise error (there should always be a marker
            # immediately after the end of the data row
            raise ValueError(f'Error parsing data body at pos: {hex(pos)}')

    # convert list into ndarray
    result_arr = np.array(rows, dtype=np.int32)

    return result_arr


def parse_header(values):
    """
    Parses a ndarray of values from the header of a scale binary file into
        formatted int variables used for reading the rest of the file.
    These integers are 16-bit, unlike the rest of the file.

    :param values: file object to parse

    :return: divisor, ylabels_info, num_rows

    divisor = integer divisor to use when calculating real values for body data.
    ylabels_info = list of [start, end, interval] for creating a range of ylabels.
    num_rows = number of data rows in the body of the file.
    """
    # iterate through header to find necessary data
    results = []

    # store all non-zero numbers
    for value in values:
        if value != 0:
            results.append(value)

    if len(results) != 5:
        raise ValueError('Error with parsing header')

    # return formatted output variables
    return results[0], results[1:4], results[4]


def parse_scale_4(path):
    """
    Parses a scale file at the path

    :param path: Path to the scale file

    :return: 1D numpy array with ylabels. 1D numpy array with xlabels. \
        2D numpy array with data values where the rows correspond \
        to retention times and the columns to the ylabels. Dict of \
        metadata for the file
    """

    # read file
    with open(path, 'rb') as f:
        # read raw binary into bytes
        raw_bytes = f.read()

    # parse header info
    raw_values_head = np.frombuffer(raw_bytes[:512], '>H')
    divisor, ylabels_info, num_rows = parse_header(raw_values_head)

    # create ylabels
    ylabels = create_ylabels(ylabels_info)

    # parse body data
    raw_values_body = parse_body(raw_bytes[512:], ylabels.size)

    # verify parse body data
    assert raw_values_body.shape[0] == num_rows, (f'Error in parsing body of {os.path.basename(path)}\n\t'
                                                  f'Number of data rows parsed: {raw_values_body.shape[0]}\n\t'
                                                  f'Number of rows needed: {num_rows}')

    # create xlabels and body data
    xlabels, raw_body_data = parse_xlabels_body(raw_values_body)

    # map divisor over body data to convert to real data numbers
    real_body = np.divide(raw_body_data, divisor)

    # create metadata
    metadata = {
        'divisor': divisor,
        'ylabels_info': ylabels_info,
        'num_rows': num_rows
    }

    return ylabels, xlabels, real_body, metadata


def main():
    """
    main script for reading pear binary data and outputting formatted csv data

    :return: None
    """
    # create directory and file paths
    cwd_path = os.getcwd()
    datadir_path = cwd_path + '\\datadir'
    file_paths = datafile_paths_from_dir(datadir_path)

    # test methods using sample data
    # scale_path = os.path.join(cwd_path, 'scale')
    # parse_scale_4(scale_path)

    # parse problem files and save to DataFile list
    solution_list = []
    for path in file_paths:
        # parse file
        ylabels, xlabels, data, metadata = parse_scale_4(path)
        # make DataFile
        dfile = DataFile(path, 'UV', xlabels, ylabels, data, metadata)
        # append to list
        solution_list.append(dfile)

    # create directory with csv files for evaluation
    solution_path = os.path.join(cwd_path, 'csv_files')
    try:
        os.mkdir(solution_path)
        print(f'made solution folder at ./{os.path.basename(solution_path)}')
    except FileExistsError as err:
        print(f"The folder '{solution_path}' already exists")
        # raise err
    # add solution files to directory
    for df in solution_list:
        file_name = df.name + '_solution'
        path = os.path.join(solution_path, file_name)
        if not os.path.exists(path):
            df.export_csv(path)


if __name__ == '__main__':
    main()