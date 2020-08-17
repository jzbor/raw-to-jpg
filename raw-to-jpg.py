#!/usr/bin/env python3

import argparse
import numpy
import os
import rawpy
#import rawpy.enhance --- Only import is needed to avoid unnecessary dependencies
import shutil
import sys
from PIL import Image
from datetime import datetime

# This list/tuple may contain any raw file ending supported by libraw
# Unfortunately I was not able to find a list with all supported types
# Feel free to add some, open an issue or open a PR
RAW_FILE_ENDINGS = ( '.CR2', '.cr2', '.nef', '.NEF' )

errors = []


# converter function which iterates through list of files
def convert_raw_to_jpg(in_path, out_path, path, verbose=True, overwrite=False, auto_wb=False, enhance=False, tiff=False):
    # file vars
    file_name = os.path.basename(in_path + path)
    file_without_ext = os.path.splitext(file_name)[0]
    file_timestamp = os.path.getmtime(in_path + path)
    parent = out_path + path[:path.rfind('/') + 1]
    if tiff:
        jpg_image_location = parent + file_without_ext + '.tiff'
    else:
        jpg_image_location = parent + file_without_ext + '.jpg'

    # omit files that already exist in the destination
    if (os.path.exists(jpg_image_location) or os.path.exists(parent + file_without_ext + '.JPG')) and not overwrite:
        if verbose:
            print('...' + path + '\t\t => ignored (file exists)')
        return

    if verbose:
        print('...' + path + '\t\t => converting RAW-file')

    # read raw file
    raw = rawpy.imread(in_path + path)
    # enhance
    if enhance:
        if type(enhance) == bool:
            bad_pixels = rawpy.enhance.find_bad_pixels([in_path + path])
            rawpy.enhance.repair_bad_pixels(raw, bad_pixels)
        else:
            bad_pixels = rawpy.enhance.find_bad_pixels(enhance)
            rawpy.enhance.repair_bad_pixels(raw, bad_pixels)
    # post processing (with white balance of camera)
    if auto_wb:
        rgb = raw.postprocess(use_auto_wb=True)
    else:
        rgb = raw.postprocess(use_camera_wb=True)
    # create directory if not existent
    if not os.path.isdir(parent):
        os.makedirs(parent)
    # save image array
    Image.fromarray(rgb).save(jpg_image_location, quality=90, optimize=True)
    # update JPG file timestamp to match RAW
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


def process_folder(in_path, out_path, path, recursion=False, verbose=True, overwrite=False, smart_mode=False, auto_wb=False, enhance=False, tiff=False):
    if not str.endswith(path, '/') or path == '':
        path += '/'
    if verbose:
        print('...' + path + '\t\t => browsing folder')
    for sub_name in os.listdir(in_path + path):
        sub_path = path + sub_name
        if os.path.isdir(in_path + sub_path) and recursion:
            process_folder(in_path, out_path, sub_path, recursion=recursion, verbose=verbose, overwrite=overwrite,
                           smart_mode=smart_mode, auto_wb=auto_wb, enhance=enhance)
        elif sub_path.endswith(RAW_FILE_ENDINGS):
            convert_raw_to_jpg(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite, auto_wb=auto_wb, enhance=enhance, tiff=tiff)
        elif smart_mode and os.path.isfile(in_path + sub_path):
            copy_other(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)


def process_folder_ge(in_path, out_path, path, recursion=False, verbose=True, overwrite=False, smart_mode=False, auto_wb=False, tiff=False):
    if not str.endswith(path, '/') or path == '':
        path += '/'
    if verbose:
        print('...' + path + '\t\t => browsing folder')
    raw_files = []
    bad_pixel_paths = []
    for sub_name in os.listdir(in_path + path):
        sub_path = path + sub_name
        if os.path.isdir(in_path + sub_path) and recursion:
            process_folder(in_path, out_path, sub_path, recursion=recursion, verbose=verbose, overwrite=overwrite,
                           smart_mode=smart_mode, auto_wb=auto_wb, enhance=enhance)
        elif sub_path.endswith(RAW_FILE_ENDINGS):
            bad_pixel_paths.append(in_path + sub_path)
            raw_files.append((in_path, out_path, sub_path))
        elif smart_mode and os.path.isfile(in_path + sub_path):
            copy_other(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)

    # convert raws all at once
    for raw_file in raw_files:
        convert_raw_to_jpg(raw_file[0], raw_file[1], raw_file[2], verbose=verbose, overwrite=overwrite, auto_wb=auto_wb, enhance=bad_pixel_paths, tiff=tiff)

def copy_raw_folder(in_path, out_path, path, verbose=True, overwrite=False):
    if not str.endswith(path, '/') or path == '':
        path += '/'
    if verbose:
        print('...' + path + '\t\t => browsing folder')
    for sub_name in os.listdir(in_path + path):
        sub_path = path + sub_name
        if os.path.isdir(in_path + sub_path):
            copy_raw_folder(in_path, out_path, sub_path, verbose=verbose, overwrite=overwrite)
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
    parser = argparse.ArgumentParser(description='Convert RAW to JPG')
    parser.add_argument('source', help='source folder of RAW files', type=str)
    parser.add_argument('destination', help='destination folder for converted JPG files', type=str)
    parser.add_argument('-a', '--archive', help='archives/copies all RAW-files (recursive, maintains folder structure)',
                        action='store_true', dest='copy_mode')
    parser.add_argument('-e', '--enhance', help='remove bad pixels', action='store_true', dest='enhance')
    parser.add_argument('-f', '--force', help='force conversion and overwrite existing files', action='store_true',
                        dest='overwrite')
    parser.add_argument('-g', '--group-enhance', help='remove bad pixels by comparing different images with the same light setting (overwrites -e)',
                        action='store_true', dest='group_enhance')
    parser.add_argument('-q', '--quiet', help='do not show any output', action='store_false', dest='verbose')
    parser.add_argument('-r', '--recursive',
                        help='convert files in subfolders recursively', action='store_true', dest='recursion')
    parser.add_argument('-s', '--stupid', help='turns on stupid mode - other files do not get copied automatically',
                        action='store_false', dest='smart_mode')
    parser.add_argument('-t', '--tiff', help='converts into tiffs instead of jpgs',
                        action='store_true', dest='tiff')
    parser.add_argument('-w', '--auto-wb', help='uses automatic white balance instead of the cameras white balance',
                        action='store_true', dest='auto_wb')
    return parser.parse_args()


# call function
if __name__ == "__main__":
    args = parse_args()

    if args.enhance:
        import rawpy.enhance

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
                copy_raw_folder(args.source, args.destination, '', verbose=args.verbose, overwrite=args.overwrite)
        elif args.group_enhance:
            import rawpy.enhance
            if args.source.endswith(RAW_FILE_ENDINGS):
                print("Only folders are accepted as input in group enhance mode!")
                exit(1)
            else:
                if args.verbose:
                    print('Converting all files in ' + args.source)
                    print('\tinto ' + args.destination + ' \t(group enchancing enabled)')
                    print()
                process_folder_ge(args.source, args.destination, '', recursion=args.recursion,
                               verbose=args.verbose, overwrite=args.overwrite, smart_mode=args.smart_mode,
                               auto_wb=args.auto_wb, tiff=args.tiff)
        else:
            if args.source.endswith(RAW_FILE_ENDINGS):
                if args.verbose:
                    print('Converting ' + args.source)
                    print('\tinto ' + args.destination)
                    print()
                convert_raw_to_jpg(args.source, args.destination, '', verbose=args.verbose, overwrite=args.overwrite, auto_wb=args.auto_wb, enhance=args.enhance, tiff=args.tiff)
            else:
                if args.verbose:
                    print('Converting all files in ' + args.source)
                    print('\tinto ' + args.destination)
                    print()
                process_folder(args.source, args.destination, '', recursion=args.recursion,
                               verbose=args.verbose, overwrite=args.overwrite, smart_mode=args.smart_mode,
                               auto_wb=args.auto_wb, enhance=args.enhance, tiff=args.tiff)
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
