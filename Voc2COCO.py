# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 11:13:25 2022

@author: intel
"""

#!/usr/bin/python

# pip install lxml

import sys
import os
import json
import xml.etree.ElementTree as ET
import glob
import math

START_BOUNDING_BOX_ID = 1
PRE_DEFINE_CATEGORIES = None
# If necessary, pre-define category and its id
#  PRE_DEFINE_CATEGORIES = {"aeroplane": 1, "bicycle": 2, "bird": 3, "boat": 4,
#  "bottle":5, "bus": 6, "car": 7, "cat": 8, "chair": 9,
#  "cow": 10, "diningtable": 11, "dog": 12, "horse": 13,
#  "motorbike": 14, "person": 15, "pottedplant": 16,
#  "sheep": 17, "sofa": 18, "train": 19, "tvmonitor": 20}

def convertTxt(xml_files, json_file):
    json_dict = {"images": [], "type": "instances", "annotations": [], "categories": []}
    if PRE_DEFINE_CATEGORIES is not None:
        categories = PRE_DEFINE_CATEGORIES
    else:
        categories = {'txtBBX':0} #get_categories(xml_files)
    bnd_id = START_BOUNDING_BOX_ID
    for xml_file in xml_files:
        filename = os.path.basename(xml_file)
        
        path =xml_file #os.path.join(os.getcwd(), 'annotation',filename)
        image_id = get_filename_as_int(xml_file)
        width= 600
        height = 450
        
        image = {
            "file_name": filename.replace(filename.split('.')[-1],'jpg'),
            "height": height,
            "width": width,
            "id": image_id,
        }
        json_dict["images"].append(image)
        
        COORDS=[]
        with open(path, encoding='utf-8') as rdr:
            data = rdr.readlines()
        for line in data:
            line = line.split()[:-1]
            line = [float(num) for num in line]
            COORDS.append(line)
            print(line)
            
        for rec in COORDS:
                
            x1,x2,x3,x4 = rec[0],rec[1],rec[2],rec[3]
            y1,y2,y3,y4 = rec[4],rec[5],rec[6],rec[7]    

            w = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            h = math.sqrt((x3-x2)**2 + (y3-y2)**2)
            ann = {
                "area": w * h,
                "iscrowd": 0,
                "image_id": image_id,
                "bbox": [x1, y1, w, h],
                "category_id": 0,
                "id": bnd_id,
                "ignore": 0,
                "segmentation": [],
            }
            json_dict["annotations"].append(ann)
            bnd_id = bnd_id + 1
            
    for cate, cid in categories.items():
        cat = {"supercategory": "none", "id": cid, "name": cate}
        json_dict["categories"].append(cat)

    #os.makedirs(os.path.dirname(json_file), exist_ok=True)
    cwd = os.getcwd() 
    jsonOut_mode = 'a' if os.path.exists(cwd+ f"/{json_file}") else 'w'
    json_fp = open(json_file, jsonOut_mode)
    json_str = json.dumps(json_dict)
    json_fp.write(json_str)
    json_fp.close()
    

def get(root, name):
    vars = root.findall(name)
    return vars


def get_and_check(root, name, length):
    vars = root.findall(name)
    if len(vars) == 0:
        raise ValueError("Can not find %s in %s." % (name, root.tag))
    if length > 0 and len(vars) != length:
        raise ValueError(
            "The size of %s is supposed to be %d, but is %d."
            % (name, length, len(vars))
        )
    if length == 1:
        vars = vars[0]
    return vars


def get_filename_as_int(filename):
    try:
        filename = filename.replace("\\", "/")
        filename = os.path.splitext(os.path.basename(filename))[0]
        return int(filename)
    except:
        raise ValueError("Filename %s is supposed to be an integer." % (filename))


def get_categories(xml_files):
    """Generate category name to id mapping from a list of xml files.
    
    Arguments:
        xml_files {list} -- A list of xml file paths.
    
    Returns:
        dict -- category name to id mapping.
    """
    classes_names = []
    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for member in root.findall("object"):
            classes_names.append(member[0].text)
    classes_names = list(set(classes_names))
    classes_names.sort()
    return {name: i for i, name in enumerate(classes_names)}


def convert(xml_files, json_file):
    json_dict = {"images": [], "type": "instances", "annotations": [], "categories": []}
    if PRE_DEFINE_CATEGORIES is not None:
        categories = PRE_DEFINE_CATEGORIES
    else:
        categories = get_categories(xml_files)
    bnd_id = START_BOUNDING_BOX_ID
    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        path = get(root, "path")
        if len(path) == 1:
            filename = os.path.basename(path[0].text)
        elif len(path) == 0:
            filename = get_and_check(root, "filename", 1).text
        else:
            raise ValueError("%d paths found in %s" % (len(path), xml_file))
        ## The filename must be a number
        image_id = get_filename_as_int(filename)
        size = get_and_check(root, "size", 1)
        width = int(get_and_check(size, "width", 1).text)
        height = int(get_and_check(size, "height", 1).text)
        image = {
            "file_name": filename,
            "height": height,
            "width": width,
            "id": image_id,
        }
        json_dict["images"].append(image)
        ## Currently we do not support segmentation.
        #  segmented = get_and_check(root, 'segmented', 1).text
        #  assert segmented == '0'
        for obj in get(root, "object"):
            category = get_and_check(obj, "name", 1).text
            if category not in categories:
                new_id = len(categories)
                categories[category] = new_id
            category_id = categories[category]
            bndbox = get_and_check(obj, "bndbox", 1)
            xmin = int(get_and_check(bndbox, "xmin", 1).text) - 1
            ymin = int(get_and_check(bndbox, "ymin", 1).text) - 1
            xmax = int(get_and_check(bndbox, "xmax", 1).text)
            ymax = int(get_and_check(bndbox, "ymax", 1).text)
            assert xmax > xmin
            assert ymax > ymin
            o_width = abs(xmax - xmin)
            o_height = abs(ymax - ymin)
            ann = {
                "area": o_width * o_height,
                "iscrowd": 0,
                "image_id": image_id,
                "bbox": [xmin, ymin, o_width, o_height],
                "category_id": category_id,
                "id": bnd_id,
                "ignore": 0,
                "segmentation": [],
            }
            json_dict["annotations"].append(ann)
            bnd_id = bnd_id + 1

    for cate, cid in categories.items():
        cat = {"supercategory": "none", "id": cid, "name": cate}
        json_dict["categories"].append(cat)

    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    json_fp = open(json_file, "w")
    json_str = json.dumps(json_dict)
    json_fp.write(json_str)
    json_fp.close()


if __name__ == "__main__":
    total = 0
    cwd= os.getcwd()
    imageFolder =cwd + "/image"    
    numOfFolders = len(next(os.walk(imageFolder))[1])
    for i in range(1,26,1):
        annotationFolder = cwd + "/annotation/"
        annotationFolder = annotationFolder + f"/{i}/*.txt"
        txtFiles = glob.glob(annotationFolder)        
        convertTxt(txtFiles, "myOutput.json")
        total = total + len(txtFiles)
    print(total)
    
    # print("Number of txt files: {}".format(len(txtFiles)))
    # convertTxt(txtFiles, "myOutput01.json")
    # print("Success: myOutput.json")
