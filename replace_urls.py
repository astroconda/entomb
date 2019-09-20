#!/usr/bin/env python
import argparse
import entomb
import fnmatch
import os


def get_input_dirs(d):
    result = []
    for root, dirs, files in os.walk(d):
        for dname in files:
            path = os.path.join(root, dname)
            if not fnmatch.fnmatch(path, '*/latest-*'):
                continue
            result.append(entomb.channel_dir(path))

    return set(result)


def get_template_dirs(d):
    result = []
    for root, dirs, files in os.walk(d):
        for dname in files:
            path = os.path.join(root, dname)
            if not fnmatch.fnmatch(path, '*/*.tar.bz2'):
                continue
            kludge = '/'.join(os.path.dirname(path).rsplit('/', 3))
            result.append(kludge)

    return sorted(set(result))


def channel_from_template(templates, needle):
    if fnmatch.fnmatch(needle, "*/conda-dev/*"):
        needle = needle.replace('conda-dev', 'astroconda-dev')

    for dname in templates:
        if needle in dname:
            return dname


def replace_urls(spec, prefix, templates, new_url):
    with open(spec, 'r') as fp:
        data = fp.read()

    new_data = []

    for line in data.splitlines():
        line = line.strip()
        if line.startswith('#') or line.startswith('@'):
            new_data.append(line)
            continue
        tail = '/'.join(os.path.dirname(line).rsplit('/', 2)[1:])
        needle = prefix + '/' + tail
        intermediate = channel_from_template(templates, needle)
        intermediate = '/'.join(intermediate.split('/')[1:])
        url, package = line.rsplit('/', 1)
        url = '/'.join([new_url, intermediate])
        new_data.append('/'.join([url, package]))

    return '\n'.join(new_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-dir', required=True, help='Path to astroconda-releases')
    parser.add_argument('-t', '--template-dir', required=True, help='Path to parent of new channel tree')
    parser.add_argument('new_url')
    args = parser.parse_args()

    input_dir = args.input_dir
    template_dir = args.template_dir
    templates = get_template_dirs(template_dir)
    new_url = args.new_url
    dirs = get_input_dirs(input_dir)
    specs = []

    for spec_base in dirs:
        spec_root = os.path.join(input_dir, spec_base)
        specs.append(entomb.spec_search(spec_root, ['*{}/latest-*'.format(spec_root)]))

    for spec_tree in specs:
        for spec_file in spec_tree:
            print("Processing: {}".format(spec_file))
            tree = '/'.join(spec_file.split(os.sep, 3)[1:-1])
            spec_new = replace_urls(spec_file, tree, templates, new_url)
            open(spec_file, 'w+').write(spec_new)
