import sys, os, re

for filename in os.listdir('./raw/'):
    with open('./raw/' + filename, 'r') as file:
        text = file.read()
        
        text = text.replace('\r', '')
        text = re.sub('//.*\n', '\n', text)
        text = re.sub('(?sm)^{.*?^}', '', text)
        text = re.sub('(?sm)^\s*$', '', text)
        text2 = text.replace('\n\n', '\n')
        while (text != text2):
            text = text2
            text2 = text.replace('\n\n', '\n')
        
        text = text.replace('"', '')
        text = text.strip()
        
        print(text)
