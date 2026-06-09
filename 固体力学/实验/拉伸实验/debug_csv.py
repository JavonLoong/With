import csv
f = open('52低碳钢破坏wn.csv','r',encoding='gbk')
r = csv.reader(f)
for _ in range(3): next(r)  # skip headers
count_by_cols = {}
for row in r:
    n = len(row)
    count_by_cols[n] = count_by_cols.get(n, 0) + 1
f.close()
print("Column count distribution:", count_by_cols)

# Check some specific rows
f = open('52低碳钢破坏wn.csv','r',encoding='gbk')
r = csv.reader(f)
for _ in range(3): next(r)
good = 0
for i, row in enumerate(r):
    try:
        vals = [float(row[j]) for j in range(7)]
        good += 1
    except (ValueError, IndexError) as e:
        if good < 31370:  # only print errors near boundaries
            pass
        if i < 5 or i > 31370:
            print(f"Row {i}: len={len(row)}, err={e}, data={row[:3]}")
print(f"Successfully parsed: {good} rows")
f.close()

# Also check ext_s column specifically
f = open('52低碳钢破坏wn.csv','r',encoding='gbk')
r = csv.reader(f)
for _ in range(3): next(r)
ext_empty = 0
for row in r:
    if len(row) >= 7:
        try:
            float(row[6])
        except ValueError:
            ext_empty += 1
print(f"Rows with empty/invalid ext_strain (col 6): {ext_empty}")
f.close()
