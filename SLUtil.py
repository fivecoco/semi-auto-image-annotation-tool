#!/usr/bin/python
# ----------------------------------------------------------------------------
# SLUtil: command line tool manager for red alert project to prepare the encrypt resource
#
# Author: Hui Zhen
# Copyright 2016 (C) SourceLight, Inc
#
# ----------------------------------------------------------------------------
'''
Command line tool manager for red alert encrypt resource
'''



# python

import os.path,zipfile
import shutil
import sys
import traceback
import distutils
import fileinput
import json
import subprocess
import hashlib


#get the joined path by relative path
def get_joined_path(path,checkExist=True):
    if not os.path.isabs(path):
        path = os.path.join(get_current_path(), path)
        path = os.path.abspath(path)
    if checkExist:
        path = sanitize_path(path)
    return path

#get the fileName only from path
def get_file_name_without_ext(path):
    return os.path.splitext(os.path.basename(path))[0]

#get the current path 
def get_current_path():
    if getattr(sys, 'frozen', None):
        ret = os.path.realpath(os.path.dirname(sys.executable))
    else:
        ret = os.path.realpath(os.path.dirname(__file__))
    return ret

def sanitize_path( path):
    if len(path) == 0:
        return None
    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        print("error in _sanitize_path",path)
        return None
    else:
        print("ok in _sanitize_path",path)
    return path

def mkdirIfNotExist(folder):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        os.makedirs(folder)

def removeAllFiles(folder):
    folder = os.path.abspath(folder)
    if os.path.isdir(folder):
        shutil.rmtree(folder)

def run_shell(cmd, cwd=None):
    p = subprocess.Popen(cmd, shell=True, cwd=cwd)
    p.wait()

    if p.returncode:
        raise subprocess.CalledProcessError(returncode=p.returncode, cmd=cmd)

    return p.returncode


def copy_files_in_dir(src, dst):

    for item in os.listdir(src):
        path = os.path.join(src, item)
        if os.path.isfile(path):
            path = add_path_prefix(path)
            copy_dst = add_path_prefix(dst)
            shutil.copy(path, copy_dst)
        if os.path.isdir(path):
            new_dst = os.path.join(dst, item)
            if not os.path.isdir(new_dst):
                os.makedirs(add_path_prefix(new_dst))
            copy_files_in_dir(path, new_dst)


def copy_files_with_config(config, src_root, dst_root):
    src_dir = config["from"]
    dst_dir = config["to"]

    src_dir = os.path.join(src_root, src_dir)
    dst_dir = os.path.join(dst_root, dst_dir)

    include_rules = None
    if "include" in config:
        include_rules = config["include"]
        include_rules = convert_rules(include_rules)

    exclude_rules = None
    if "exclude" in config:
        exclude_rules = config["exclude"]
        exclude_rules = convert_rules(exclude_rules)

    copy_files_with_rules(
        src_dir, src_dir, dst_dir, include_rules, exclude_rules)


def copy_files_with_rules(src_rootDir, src, dst, include=None, exclude=None):
    if os.path.isfile(src):
        if not os.path.exists(dst):
            os.makedirs(add_path_prefix(dst))

        copy_src = add_path_prefix(src)
        copy_dst = add_path_prefix(dst)
        shutil.copy(copy_src, copy_dst)
        return

    if (include is None) and (exclude is None):
        if not os.path.exists(dst):
            os.makedirs(add_path_prefix(dst))
        copy_files_in_dir(src, dst)
    elif (include is not None):
        # have include
        for name in os.listdir(src):
            abs_path = os.path.join(src, name)
            rel_path = os.path.relpath(abs_path, src_rootDir)
            if os.path.isdir(abs_path):
                sub_dst = os.path.join(dst, name)
                copy_files_with_rules(
                    src_rootDir, abs_path, sub_dst, include=include)
            elif os.path.isfile(abs_path):
                if _in_rules(rel_path, include):
                    if not os.path.exists(dst):
                        os.makedirs(add_path_prefix(dst))

                    abs_path = add_path_prefix(abs_path)
                    copy_dst = add_path_prefix(dst)
                    shutil.copy(abs_path, copy_dst)
    elif (exclude is not None):
        # have exclude
        for name in os.listdir(src):
            abs_path = os.path.join(src, name)
            rel_path = os.path.relpath(abs_path, src_rootDir)
            if os.path.isdir(abs_path):
                sub_dst = os.path.join(dst, name)
                copy_files_with_rules(
                    src_rootDir, abs_path, sub_dst, exclude=exclude)
            elif os.path.isfile(abs_path):
                if not _in_rules(rel_path, exclude):
                    if not os.path.exists(dst):
                        os.makedirs(add_path_prefix(dst))

                    abs_path = add_path_prefix(abs_path)
                    copy_dst = add_path_prefix(dst)
                    shutil.copy(abs_path, copy_dst)


def _in_rules(rel_path, rules):
    import re
    ret = False
    path_str = rel_path.replace("\\", "/")
    for rule in rules:
        if re.match(rule, path_str):
            ret = True

    return ret


def convert_rules(rules):
    ret_rules = []
    for rule in rules:
        ret = rule.replace('.', '\\.')
        ret = ret.replace('*', '.*')
        ret = "%s" % ret
        ret_rules.append(ret)

    return ret_rules


def os_is_win32():
    return sys.platform == 'win32'


def os_is_32bit_windows():
    if not os_is_win32():
        return False

    arch = os.environ['PROCESSOR_ARCHITECTURE'].lower()
    archw = "PROCESSOR_ARCHITEW6432" in os.environ
    return (arch == "x86" and not archw)


def os_is_mac():
    return sys.platform == 'darwin'


def os_is_linux():
    return 'linux' in sys.platform


def add_path_prefix(path_str):
    if not os_is_win32():
        return path_str

    if path_str.startswith("\\\\?\\"):
        return path_str

    ret = "\\\\?\\" + os.path.abspath(path_str)
    ret = ret.replace("/", "\\")
    return ret


# get from http://stackoverflow.com/questions/6194499/python-os-system-pushd
def pushd(newDir):
    previousDir = os.getcwd()
    os.chdir(newDir)
    yield
    os.chdir(previousDir)

def calc_file_md5(fileName):
    if not os.path.isfile(fileName):
        return False,""

    md5 = hashlib.md5()
    f = open(fileName)
    while True:
        data = f.read()
        if not data:
            break
        md5.update(data)
    hashcode = md5.hexdigest()
    return True,hashcode

