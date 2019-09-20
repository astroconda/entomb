#!/usr/bin/env python
import argparse
import os
import fnmatch
import requests
import shutil


def channel_dir(d):
    dname = os.path.dirname(d)
    channel = '/'.join(dname.split('/')[-2:])
    return channel


def download(url, destdir='.', clobber=True, in_memory=False):
    filename = url.split('/')[-1]

    if destdir != '.':
        os.makedirs(destdir, mode=0o775, exist_ok=True)

    outfile = os.path.join(destdir, filename);
    if not clobber and os.path.exists(outfile):
        print("Skipping: {}".format(outfile))
        return outfile

    if not url.startswith('http'):
        if url.startswith('file://'):
            url = url.replace('file://', '')

        print("Copying: {} -> {}".format(url, destdir))
        shutil.copy2(url, outfile)
        return outfile

    print("Downloading: {} -> {}".format(url, destdir))
    r = requests.get(url, stream = True)

    if r.status_code != 200:
        print("HTTP ERROR[{}]: Could not download: {}".format(r.status_code, url))
        return ""

    if in_memory:
        return r.contents

    with open(outfile,"w+b") as fp:
        for chunk in r.iter_content(chunk_size=0xFFFF):
            if chunk:
                fp.write(chunk)
    return outfile


def spec_read(filename):
    urls = []
    with open(filename, 'r') as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('@'):
                continue
            urls.append(line)
    return urls

def spec_search(input_dir, patterns):
    results = []

    for root, _, files in os.walk(input_dir):
        for fname in files:
            path = os.path.join(root, fname)
            for pattern in patterns:
                if fnmatch.fnmatch(path, pattern):
                    results.append(path)

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-dir', required=True, help='Path to astroconda-releases directory')
    parser.add_argument('-o', '--output-dir', required=True, help='Path to output directory')
    parser.add_argument('-c', '--clobber', action='store_true', help='Overwrite existing packages')
    parser.add_argument('-p', '--pattern', action='append', help='Search tree for directories and filenames matching patterns (e.g. \'*/latest-*\')')
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    pattern = ['*']
    if args.pattern:
        pattern = args.pattern

    for spec in spec_search(input_dir, pattern):
        urls = spec_read(spec)
        channel_parent = channel_dir(spec)
        for url in urls:
            channel_sibling = channel_dir(url)
            new_channel = os.path.join(output_dir, channel_parent, channel_sibling)
            download(url, destdir=new_channel, clobber=args.clobber);


