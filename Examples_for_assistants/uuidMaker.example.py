import uuid
import sys

count = int(sys.argv[len(sys.argv)-1])

for i in range (0, count):
  print uuid.uuid4()
