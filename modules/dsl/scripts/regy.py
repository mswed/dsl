import re

text = '''# dsl_button: Clean Camera
# dsl_tab: Main:6:clean_camera()
# dsl_tab: Other:12:
# dsl_color: purple
# dsl_description: create the clean copy of a camera
# dsl_help: To use the script do the following:
# dsl_help: 1. Select a camera
# dsl_help: 2. Run the script.
# dsl_help: 3. Decide of you want a shotCam or a tempCam
# dsl_help: shotCam has a specific naming convention and all its
# dsl_help: channels are locked.'''

location = re.findall("dsl_tab:\s*(\w*):(\d*):(.*[^\n\s])", text)
for loc in location:
    button_tab = loc[0]
    button_line = loc[1]
    button_command = loc[2]
    print '[' + button_command + ']'
    print ('button created for', button_tab, button_line, button_command)
color = re.search('dsl_color:\s*(\w*)', text).group(1)
description = re.search('dsl_description:\s*(.*)', text).group(1)
help = re.findall('dsl_help:\s*(.*)', text)
help = '\n'.join(help)
# color = color.group(1)
print location
print color
print description
print help

if color == 'purple':
    print 'Yay!'
# location = re.match("dsl_tab:(\s*(\w*):(\d*):(.*))", text, re.MULTILINE)

# location = re.findall("dsl_color:", text, re.MULTILINE)
# print location