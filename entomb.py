#!/usr/bin/env python
import os
import argparse
import requests
import shutil


def channel_dir(d):
    dname = os.path.dirname(d)
    channel = '/'.join(dname.split('/')[-2:])
    return channel


def download(url, destdir='.', clobber=True):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base-dir')
    parser.add_argument('-c', '--clobber', action='store_true')
    parser.add_argument('spec_file')
    args = parser.parse_args()

    base_dir = args.base_dir
    #spec_url = 'https://ssb.stsci.edu/releases/jwstdp/0.13.8/latest-linux'
    spec_url = args.spec_file
    spec_dir = os.path.join('specs', base_dir)

    spec_file = download(spec_url, destdir=spec_dir)
    urls = spec_read(spec_file)

    for url in urls:
        new_channel = os.path.join(base_dir, channel_dir(url))
        download(url, new_channel, clobber=args.clobber);

