import time

from nptdms import TdmsFile
import glob
import ntpath


def get_tdms_files_from_directory(directory_path):
    if directory_path[-1:] is not '/':
        directory_path = directory_path + '/'
    tdms_filenames = glob.glob(directory_path + '**/*.tdms', recursive=True)
    tdms_files = {}
    for name in tdms_filenames:
        tdms_files.update({name[(-1 * len(name) + len(directory_path)):]: TdmsFile(name)})
    return tdms_files


def generate_dropdown_inputs(directory_path, file_type):
    if directory_path[-1:] is not '/':
        directory_path = directory_path + '/'
    tdms_filenames = glob.glob(directory_path + '**/*.{}'.format(file_type), recursive=True)
    result = []
    for name in tdms_filenames:
        result.append({'label': ntpath.basename(name), 'value': name})
    return result


if __name__ == '__main__':
    start_time = time.time()
    print(generate_dropdown_inputs('/home/david/Documents/4dot_data/example_data/', 'tdms'))
    # tdms_filenames = glob.glob('/home/david/Documents/4dot_data/**/*.tdms', recursive=True)
    #
    # tdms_files = {}
    # # for i in range(1, 10):
    # # tdms_files.update({ntpath.basename(tdms_filenames[i]): TdmsFile(tdms_filenames[i]).as_dataframe()})
    #
    # print(len(tdms_filenames))
    print("--- %s seconds ---" % (time.time() - start_time))
