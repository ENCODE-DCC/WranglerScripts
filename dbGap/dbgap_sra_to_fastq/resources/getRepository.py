import sys

folder_name=sys.stdin.read().strip().split("/")[-1]
print folder_name[:len(folder_name)-2]
