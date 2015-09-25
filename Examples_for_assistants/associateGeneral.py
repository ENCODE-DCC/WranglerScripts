f = open('objDict')
lines = f.readlines()
f.close()

dictionary = {}
for line in  lines:
  temp=line.strip()
  line=temp.split('\t')
  key = line[0]
  value = line[1]
  dictionary[key] = value

f = open('list')
lines = f.readlines()
f.close()

for line in  lines:
  temp=line.strip()
  if temp in dictionary:
     print temp,'	',dictionary[temp]
  else:
     print temp  
  #if temp not in dictionary: 
  #  print '	',temp   
  #else:
  #  print dictionary[temp],'	',temp

#open the file that needs assigning
#for each line in file
#read in the dictionary entry

