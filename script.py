import re
text = open("transcript_tools.txt", encoding="utf8").read()
matches = re.findall(r'"TargetContent":"(.*?)"', text, re.DOTALL)
for m in matches:
    if "Pesquisar Cliente" in m:
        try:
            print(m.encode("utf8").decode("unicode_escape")[:1500])
        except Exception as e:
            print("Error decoding:", e)
