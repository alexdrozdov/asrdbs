#!/bin/bash

libru_dir=$1
filelist=$2

echo "Dumping file list to ${filelist}..."

find $libru_dir -name \*.txt > $filelist

linecount=$(wc -l $filelist | cut -d " " -f 1)
sed -i "1i${linecount}" $filelist

echo "Dumped $linecount files"

