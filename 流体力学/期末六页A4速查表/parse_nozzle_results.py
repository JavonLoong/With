with open('nozzle_results.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for idx, line in enumerate(lines):
    if 'U00012' in line or '螺栓' in line:
        if 'D1=200' in line or 'D1 = 200' in line or '绝对压强' in line or '345' in line:
            start = max(0, idx - 10)
            end = min(len(lines), idx + 50)
            out.append(f"--- line {idx} ---")
            out.extend(lines[start:end])
            out.append("="*60)

with open('nozzle_solution_extracted.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(out))
print("Done")
