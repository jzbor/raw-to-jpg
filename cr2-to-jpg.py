#!/usr/bin/env python3

import argparse
import numpy
import os
import rawpy
import shutil
import sys
from PIL import Image
from datetime import datetime

# This list/tuple may contain any raw file ending supported by libraw
# Unfortunately I was not able to find a list with all supported types
# Feel free to add some, open an issue or open a PR
RAW_FILE_ENDINGS = ( '.CR2', '.cr2' )

errors = []


# converter function which iterates through list of files
def convert_cr2_to_jpg(in_path, out_path, path, verbose=True, overwrite=False):
    # file vars
    file_name = os.path.basename(in_path + path)
    file_without_ext = os.path.splitext(file_name)[0]
    file_timestamp = os.path.getmtime(in_path + path)
    parent = out_path + path[:path.rfind('/') + 1]
    jpg_image_location = parent + file_without_ext + '.jpg'

    # omit files that already exist in the destination
    if (os.path.exists(jpg_image_location) or os.path.exists(parent + file_without_ext + '.JPG')) and not overwrite:
        if verbose:
            print('...' + path + '\t\t => ignored (file exists)')
        return

    if verbose:
        print('...' + path + '\t\t => converting CR2-file')

    # read raw file
    raw = rawpy.imread(in_path + path)
    # post processing (with white balance of camera)
    rgb = raw.postprocess(use_camera_wb=True)
    # create directory if not existent
    if not os.path.isdir(parent):
        os.makedirs(parent)
    # save image array
    Image.fromarray(rgb).save(jpg_image_location, quality=90, optimize=True)
    # update JPG file timestamp to match CR2
    os.utime(jpg_image_location, (file_timestamp, file_timestamp))

    raw.close()

def copy_other(in_path, out_path, path, verbose=True, overwrite=False, ):
    if os.path.exists(out_path + path) and not overwrite:
        if verbose:
            print('...' + path + '\t\t => ignored (file exists)')
        return

    if verbose:
        print('...' + path + '\t\t => copying file')

    parent = out_path + path[:path.rfind('/') + 1]
    if not os.path.isdir(parent):
        os.makedirs(parent)

    shutil.copy2(os.path.abspath(in_path + path), os.path.abspath(out_path + path))


def process_folder(in_path, out_path, path, recursion=False, verbose=True, overwrite=False, smart_mode=False):
    if not str.endswith(path, '/') or path == '':
        path += '/'
    if verbose:
        print('...' + path + '\t\t => browsing folder')
    for sub_name in os.listdir(in_path + path):
        sub_path = path + sub_name
        if os.path.isdir(in_path + sub_path) and recursion:
            process_folder(in_path, out_path, sub_path, recursion=recursion, verbose=verbose, overwrite=overwrite,
                           smart_mode=smart_mode)
        elif sub_path.endswith(RAW_FILE_ENDINGS):
            convert_cr2_to_jpg(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)
        elif smart_mode and os.path.isfile(in_path + sub_path):
            copy_other(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)


def copy_cr2_folder(in_path, out_path, path, verbose=True, overwrite=False):
    if not str.endswith(path, '/') or path == '':
        path += '/'
    if verbose:
        print('...' + path + '\t\t => browsing folder')
    for sub_name in os.listdir(in_path + path):
        sub_path = path + sub_name
        if os.path.isdir(in_path + sub_path):
            copy_cr2_folder(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)
        elif sub_path.endswith(RAW_FILE_ENDINGS):
            if os.path.exists(out_path + sub_path) and not overwrite:
                if verbose:
                    print('...' + sub_path + '\t\t => ignored (file exists)')
                return
            else:
                if verbose:
                    print('...' + sub_path + '\t\t => copying file')
                parent = out_path + sub_path[:sub_path.rfind('/') + 1]
                if not os.path.isdir(parent):
                    os.makedirs(parent)
                shutil.copy2(os.path.abspath(in_path + sub_path), os.path.abspath(out_path + sub_path))


def parse_args():
    # params
    parser = argparse.ArgumentParser(description='Convert CR2 to JPG')
    parser.add_argument('source', help='source folder of CR2 files', type=str)
    parser.add_argument('destination', help='destination folder for converted JPG files', type=str)
    parser.add_argument('-r', help='convert files in subfolders recursively', action='store_true', dest='recursion')
    parser.add_argument('-q', help='do not show any output', action='store_false', dest='verbose')
    parser.add_argument('-f', help='force conversion and overwrite existing files', action='store_true',
                        dest='overwrite')
    parser.add_argument('-s', help='turns on stupid mode - other files do not get copied automatically',
                        action='store_false', dest='smart_mode')
    parser.add_argument('-a', help='archives/copies all CR2-files (recursive, maintains folder structure)',
                        action='store_true', dest='copy_mode')
    return parser.parse_args()


# call function
if __name__ == "__main__":
    args = parse_args()

    start_time = datetime.now()

    try:
        if args.copy_mode:
            if args.source.endswith(RAW_FILE_ENDINGS):
                print("Only folders are accepted as input in archive mode!")
                exit(1)
            else:
                if args.verbose:
                    print('Archiving all files in ' + args.source)
                    print('\tinto ' + args.destination)
                    print()
                copy_cr2_folder(args.source, args.destination, '', verbose=args.verbose, overwrite=args.overwrite)
        else:
            if args.source.endswith(RAW_FILE_ENDINGS):
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
    except KeyboardInterrupt:
        pass

    if args.verbose:
        print()
        if len(errors) > 0:
            print(str(len(errors)) + ' errors occured:')
            for e in errors:
                print('\t' + e[0] + e[2])
        else:
            print('No errors occured')
        print()
        print('Finished in ' + str(datetime.now() - start_time))
        print('Done')
