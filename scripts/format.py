#
# Copyright(c) 2018 Intel Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import argparse
import difflib
import glob
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    logging.info('Processing a command line')
    args = process_command_line()

    logging.info('Finding source files')
    files = find_source_files(args.root_directory)

    if args.check:
        return check_formatting(files, args.clang_format)
    else:
        return format_files(files, args.clang_format)


def check_formatting(files, clang_format):
    logging.info('Checking formatting')
    with ThreadPoolExecutor() as executor:
        logging.info('Reading expected values')
        expected = executor.map(run_clang_format_star,
                                zip(files,
                                    repeat(clang_format)))

        logging.info('Reading actual values')
        actual = executor.map(read_file, files)

        logging.info('Comparing')
        diff_results = executor.map(diff_star, zip(actual, expected))

    diffs = []
    for f, d in zip(files, diff_results):
        diff_str = '\n'.join(d)
        if diff_str:
            logging.warning('Diff in {}:\n{}'.format(f, diff_str))
            diffs.append(f)
        else:
            logging.debug('No diff in {}'.format(f))

    logging.info('Formatting checked')
    logging.info('Diff count: {}'.format(len(diffs)))
    return len(diffs)


def format_files(files, clang_format):
    logging.info('Running clang-format')
    with ThreadPoolExecutor() as executor:
        executor.map(run_clang_format_star,
                     zip(files, repeat(clang_format),
                         repeat('-i')))
    logging.info('Formatting is done')
    return 0


def find_source_files(root_path):
    types = ('.cpp', '.hpp', '.cl')
    files = []
    for t in types:
        pattern = '{}/**/*{}'.format(root_path, t)
        for f in glob.iglob(pattern, recursive=True):
            files.append(os.path.normpath(f))
    return files


def run_clang_format_star(args):
    return run_clang_format(*args)


def run_clang_format(f, command='clang-format', arguments=''):
    cmd = '{} {} {}'.format(command, arguments, f)
    return subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode()


def read_file(f):
    with open(f) as f_content:
        return f_content.read()


def diff_star(args):
    return diff(*args)


def diff(actual, expected):
    return difflib.unified_diff(actual.splitlines(), expected.splitlines())


def process_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-directory', default='../compute_samples',
                        help='Root directory of compute-samples source')
    parser.add_argument('--clang-format', default='clang-format',
                        help='clang-format command')
    parser.add_argument('--check', action='store_true',
                        help='Check formatting')
    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main())
