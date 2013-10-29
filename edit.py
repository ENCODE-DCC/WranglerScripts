from ENCODETools import ReadJSON
from ENCODETools import WriteJSON

# editing variables
field_edit = u'donor'
old_term_string = 'ENCDO000HUM'
new_term_string = 'ENCDO000XXX'

input_file = 'find.json'
output_file = 'update.json'

# get object list
object_list = ReadJSON(input_file)

# find relevant entries and replace old text with new
counter_edit = 0
for object_item in object_list:
    if old_term_string in object_item[field_edit]:
        object_item[field_edit] = object_item[field_edit].replace(old_term_string,new_term_string)
        counter_edit+=1
        print(object_item[u'accession'] + ' edited. In "' + str(field_edit) + '", ' + old_term_string + ' replaced with ' + new_term_string)        

WriteJSON(object_list,output_file)

print('Edited ' + str(counter_edit) + ' of ' + str(len(object_list)) + ' objects. Saved to ' + output_file + '.')

