import re, collections, sys
s = open(sys.argv[1]).read()
items = re.findall(r"<item>(.*?)</item>", s, re.S)
by = collections.defaultdict(list)
for it in items:
    cat = re.search(r"<category>'?([^<']+)'?</category>", it).group(1)
    vals = re.findall(r"<value>([^<]+)</value>", it)
    by[cat].append(vals)
print("TOTAL", len(items))
for cat, lst in sorted(by.items()):
    print(f"== {cat}: {len(lst)}")
    for v in lst[:5]:
        print("   ", v)
