#!/usr/bin/python
# ----------------------------------------------------------------------------
# SLVideoUtil: video process, convert mp4 to image like jpg, png. and convert image to mp4 in reverse
#
# Author: Hui Zhen
# Copyright 2018 (C) SourceLight . inc
#
# ----------------------------------------------------------------------------
'''
video process
'''

# python

import os.path,zipfile
import cv2
import SLUtil

#get the joined path by relative path
def convert_mp4_jpg(mp4FilePath, destPath):
    
    if os.path.isfile(mp4FilePath) == False:
        print("mp4FilePath %s is not a file", mp4FilePath)
        return

    #get the frame prefix
    framePrefix = SLUtil.get_file_name_without_ext(mp4FilePath)

    #get the new dest path
    destPath = os.path.join(destPath,framePrefix)
    SLUtil.mkdirIfNotExist(destPath)

    c=0  
    vc = cv2.VideoCapture(mp4FilePath) #读入视频文件 
    rval=vc.isOpened()  
    if rval == False:
        print("mp4FilePath %s is not a validate mp4 file", mp4FilePath)
        return

    while rval:   #循环读取视频帧  
        c = c + 1  
        rval, frame = vc.read()   
        if rval:  
            destFilePath = os.path.join(destPath,framePrefix+str(c).zfill(8) + '.jpg')
            cv2.imwrite(destFilePath, frame) #存储为图像  
        else:  
            break  
    return destPath,c
    
    

