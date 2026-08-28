import json
for line in open('transcript_tools.txt', encoding='utf8'):
    if 'TargetContent' in line:
        print(line[:500])
