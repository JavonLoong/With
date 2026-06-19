import subprocess
import os

files = [
    (r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex", r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表"),
    (r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex", r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹")
]

for tex_path, cwd in files:
    print(f"Compiling {os.path.basename(tex_path)} in {cwd}...")
    try:
        res = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", os.path.basename(tex_path)],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            print(f"Successfully compiled {os.path.basename(tex_path)}!")
        else:
            print(f"Compilation failed for {os.path.basename(tex_path)} (code: {res.returncode})!")
            print("Error output snippet:")
            # Print last 20 lines of stdout/stderr
            print("\n".join(res.stdout.splitlines()[-20:]))
    except Exception as e:
        print(f"Error executing xelatex: {e}")
