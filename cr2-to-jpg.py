#!/usr/bin/env python3

import argparse
import os
# import what we need
import shutil
from datetime import datetime

import numpy
from PIL import Image
from rawkit import raw  # You may need to rollback libraw (eg. to libraw16)


# converter function which iterates through list of files
def convert_cr2_to_jpg(in_path, out_path, path, verbose=True, overwrite=False):
    # file vars
    file_name = os.path.basename(in_path + path)
    file_without_ext = os.path.splitext(file_name)[0]
    file_timestamp = os.path.getmtime(in_path + path)
    parent = out_path + path[:path.rfind('/') + 1]
    jpg_image_location = parent + file_without_ext + '.jpg'

    # omit files that already exist in the destination
    if os.path.exists(jpg_image_location) and not overwrite:
        if verbose:
            print('...' + path + '\t\t => ignored (file exists)')
        return

    if verbose:
        print('...' + path + '\t\t => converting CR2-file')

    # parse CR2 image
    raw_image_process = raw.Raw(in_path + path)
    buffered_image = numpy.array(raw_image_process.to_buffer())

    # check orientation due to PIL image stretch issue
    if raw_image_process.metadata.orientation == 0:
        jpg_image_height = raw_image_process.metadata.height
        jpg_image_width = raw_image_process.metadata.width
    else:
        jpg_image_height = raw_image_process.metadata.width
        jpg_image_width = raw_image_process.metadata.height

    # prep JPG details
    jpg_image = Image.frombytes('RGB', (jpg_image_width, jpg_image_height), buffered_image)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    jpg_image.save(jpg_image_location, format="jpeg")

    # update JPG file timestamp to match CR2
    os.utime(jpg_image_location, (file_timestamp, file_timestamp))

    # close to prevent too many open files error
    jpg_image.close()
    raw_image_process.close()


def copy_other(in_path, out_path, path, verbose=True, overwrite=False, ):
    if os.path.exists(out_path + path) and not overwrite:
        if verbose:
            print('...' + path + '\t\t => ignored (file exists)')
        return

    if verbose:
        print('...' + path + '\t\t => copying file')

    shutil.copy2(in_path + path, out_path + path)


def process_folder(in_path, out_path, path, recursion=False, verbose=True, overwrite=False, smart_mode=False):
    if not str.endswith(path, '/') or path == '':
        path += '/'
    if verbose:
        print('...' + path + '\t\t => browsing folder')
    for sub_name in os.listdir(in_path + path):
        sub_path = path + sub_name
        if os.path.isdir(in_path + sub_path) and recursion:
            process_folder(in_path, out_path, sub_path, recursion=recursion, verbose=verbose, overwrite=overwrite)
        elif str.endswith(sub_path, '.CR2') or str.endswith(sub_path, '.cr2'):
            convert_cr2_to_jpg(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)
        elif smart_mode and os.path.isfile(in_path + sub_path):
            copy_other(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)



def parse_args():
    # params
    parser = argparse.ArgumentParser(description='Convert CR2 to JPG')
    parser.add_argument('source', help='source folder of CR2 files', type=str)
    parser.add_argument('destination', help='destination folder for converted JPG files', type=str)
    parser.add_argument('-r', help='convert files in subfolders recursively', action='store_true', dest='recursion')
    parser.add_argument('-q', help='do not show any output', action='store_false', dest='verbose')
    parser.add_argument('-f', help='force conversion and override existing files', action='store_true',
                        dest='overwrite')
    parser.add_argument('-s', help='turns on stupid mode - other files do not get copied automatically',
                        action='store_false',
                        dest='smart_mode')
    return parser.parse_args()


# call function
if __name__ == "__main__":
    args = parse_args()

    start_time = datetime.now()

    if str.endswith(args.source, '.CR2') or str.endswith(args.source, '.cr2'):
        if args.verbose:
            print('Converting ' + args.source)
            print('\tinto ' + args.destination)
            print()
        convert_cr2_to_jpg(args.source, args.destination, '', verbose=args.verbose, overwrite=args.overwrite)
    else:
        if args.verbose:
            print('Converting all files in ' + args.source)
            print('\tinto ' + args.destination)
            print()
        process_folder(args.source, args.destination, '', recursion=args.recursion,
                       verbose=args.verbose, overwrite=args.overwrite, smart_mode=args.smart_mode)

    if args.verbose:
        print()
        print('Finished in ' + str(datetime.now() - start_time))
        print('Done')