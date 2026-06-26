"""
外部排序 (External Sorting) - 大文件排序算法

外部排序用于排序超出内存容量的大文件。
核心思想：将大文件分成可放入内存的小块，分别排序后，
通过多路归并合并所有有序块。

Algorithm Overview:
External sorting is used to sort large files that exceed available memory.
The core idea: split the large file into chunks that fit in memory,
sort each chunk, then merge all sorted chunks using k-way merge.
"""
