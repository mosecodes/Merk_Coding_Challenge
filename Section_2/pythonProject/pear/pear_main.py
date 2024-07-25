"""
Methods for parsing pear file

"""
import os
import re
import numpy as np
import rainbow as rb
from rainbow.datafile import DataFile
from rainbow.datadirectory import DataDirectory
import pandas as pd

"""
BINARY PARSING METHODS

parsing for the pear problems
"""


def parse_pear_4(path):
    """
    Parses a pear file based on a 4 byte format.

    :param path: path to the file

    :return: 1D numpy array with ylabels. 2D numpy array with data values \
        where the rows correspond to the retention times and \
        the columns correspond to the ylabels.
    """

    # read most significant 4 bytes from each segment into 'raw_bytes'.
    with open(path, 'rb') as f:
        raw_bytes = f.read()

    # verify path and raw_bytes
    # print(path)
    # print(raw_bytes)

    # calculate the 'values' from each 4-byte segment. dtype must be little-endian int
    raw_values = np.frombuffer(raw_bytes, dtype='<i')

    # verify raw_values, should print 328 for sample file
    # print(raw_values[90])

    # find the start of the real data by skipping the header
    start_index = 0
    while raw_values[start_index] == 72:
        start_index += 1

    # find the end of the real data by skipping the footer
    end_index = len(raw_values)
    while raw_values[end_index - 1] == 70:
        end_index -= 1

    # start interpreting ints after header
    unshaped_values = raw_values[start_index:end_index]

    # reshape the useful data into a 2D array with time, intensity columns
    num_cols = 2
    num_rows = len(unshaped_values) // num_cols
    result_array = unshaped_values[:num_rows * num_cols].reshape((num_rows, num_cols))

    # verify result array
    # print(result_array[:15])

    # create ylabels
    ylabels = ['intensity']
    ylabels_arr = np.array(ylabels)

    # cleanup
    del raw_values, raw_bytes, unshaped_values, ylabels

    return ylabels_arr, result_array


def datafile_paths_from_dir(path):
    """
    Method for returning an array of data file paths from a directory path.

    :param path: Path of the directory
    :return: ndarray of all paths to files within the directory path
    """
    # Ensure the provided path is a directory
    if not os.path.isdir(path):
        raise ValueError(f'the path {path} is not a directory or does not exist.')

    # List all files in the directory (assuming no subdirectories)
    files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    # Convert the list to a ndarray
    files_arr = np.array(files)

    return files_arr


def make_pear_datafile(path, ylabels, data):
    xlabels, intensity_data = np.hsplit(data, 2)
    xlabels = xlabels.flatten()
    metadata = {'meta': 'None'}
    name = os.path.basename(path)
    # debugging errors
    if not isinstance(path, str):
        raise Exception(f'file path {path} is not a string')
    if not isinstance(xlabels, np.ndarray) or xlabels.ndim != 1:
        raise Exception(f'xlabels for {name} is not an ndarray or is not 1D'
                        f'\n    ndarray: {isinstance(xlabels, np.ndarray)}'
                        f'\n    ndim: {xlabels.ndim}'
                        f'\n    sample: {xlabels[:3]}')
    if not isinstance(ylabels, np.ndarray) or ylabels.ndim != 1:
        raise Exception(f'ylabels for {name} is not an ndarray or is not 1D')
    if not isinstance(intensity_data, np.ndarray) or intensity_data.ndim != 2:
        raise Exception(f'intensity_data for {name} is not an ndarray or is not 2D')
    if not isinstance(metadata, dict):
        raise Exception(f'metadata for {name} is not a dict (somehow?)')
    # create DataFile
    return DataFile(path, 'UV', xlabels, ylabels, intensity_data, metadata)


def main():
    """
    main script for reading pear binary data and outputting formatted csv data

    :return: None
    """
    # create directory and file paths
    cwd_path = os.getcwd()
    datadir_path = cwd_path + '\\datadir'
    file_paths = datafile_paths_from_dir(datadir_path)

    # create list of DataFiles
    data_files = []
    for file_path in file_paths:
        name = os.path.basename(file_path)
        print(f'\nparsing file: {name.upper()}')
        # create necessary arguments for make_datafile method from extracted data
        ylabels, data = parse_pear_4(file_path)
        print(f'making DataFile: {name}')
        data_files.append(make_pear_datafile(file_path, ylabels, data))

    data_files_array = np.array(data_files)

    # create directory with csv files for evaluation
    solution_path = os.path.join(cwd_path, 'csv_files')
    try:
        os.mkdir(solution_path)
        print(f'made solution folder at ./{os.path.basename(solution_path)}')
    except FileExistsError as err:
        print(f"The folder '{solution_path}' already exists")
        raise err
    for df in data_files_array:
        file_name = df.name + '_solution'
        path = os.path.join(solution_path, file_name)
        if not os.path.exists(path):
            df.export_csv(path)

    # TESTING WITH SAMPLE DATA
    # pear_path = os.getcwd() + '\\pear'
    # ylabels, data = parse_pear_4(pear_path)
    # pear_datafile = make_pear_datafile(pear_path, ylabels, data)
    #
    # pear_datafile.plot(None, linestyle='', marker='.', markersize=1.0)


if __name__ == '__main__':
    main()