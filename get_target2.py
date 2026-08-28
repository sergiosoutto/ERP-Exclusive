import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
for line in open('transcript_tools.txt', encoding='utf8'):
    if 'ABA 1: NOVO ATENDIMENTO' in line:
        print(line)
