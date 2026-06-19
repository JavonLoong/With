import re

file_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_lib1_1 = r"\mbox{①} 任何流体在静止或平衡下\warn{都不能承受切应力而处于平衡状态}，一旦受剪切力必产生连续变形。\mbox{②} 液体的粘度随温度升高而\warn{降低}，气体的粘度随温度升高而\warn{增加}。\mbox{③} \warn{理想流体}是为处理问题方便而人为引入的\warn{理想模型}（真实流体都是有粘性的），当动力粘性系数/速度变化率很小（\warn{剪应力极小}）时可忽略不计。\mbox{④} 理想流体压力是\warn{唯一的表面力}，作用力的大小与方向无关，方向垂直于作用面并指向内法线方向；粘性流体压力是\warn{三个主应力的算术平均值的负值}（即 $p = -(\sigma_x+\sigma_y+\sigma_z)/3$），忽略流体粘性时粘性流体的压力就蜕化为理想流体的压力。\mbox{⑤} 水滴与水中气泡内部压强总是大于外部（$\Delta p = 2\sigma/R$），极细测压管读数（液面高度）不直接是真实静压，须修正毛细上升（$h = \frac{4\sigma}{\rho g d}$）。牙膏、油漆、煤泥水低于屈服应力时不流动，属于宾汉塑性流体。\\"
new_lib1_1 = r"{\fontspec{SimSun}①} 任何流体在静止或平衡下\warn{都不能承受切应力而处于平衡状态}，一旦受剪切力必产生连续变形。{\fontspec{SimSun}②} 液体的粘度随温度升高而\warn{降低}，气体的粘度随温度升高而\warn{增加}。{\fontspec{SimSun}③} \warn{理想流体}是为处理问题方便而人为引入的\warn{理想模型}（真实流体都是有粘性的），当动力粘性系数/速度变化率很小（\warn{剪应力极小}）时可忽略不计。{\fontspec{SimSun}④} 理想流体压力是\warn{唯一的表面力}，作用力的大小与方向无关，方向垂直于作用面并指向内法线方向；粘性流体压力是\warn{三个主应力的算术平均值的负值}（即 $p = -(\sigma_x+\sigma_y+\sigma_z)/3$），忽略流体粘性时粘性流体的压力就蜕化为理想流体的压力。{\fontspec{SimSun}⑤} 水滴与水中气泡内部压强总是大于外部（$\Delta p = 2\sigma/R$），极细测压管读数（液面高度）不直接是真实静压，须修正毛细上升（$h = \frac{4\sigma}{\rho g d}$）。牙膏、油漆、煤泥水低于屈服应力时不流动，属于宾汉塑性流体。\\"

if old_lib1_1 in content:
    content = content.replace(old_lib1_1, new_lib1_1)
    print("Sub-library 1 Point 1 updated successfully with {\fontspec{SimSun}①}")
else:
    print("WARNING: Sub-library 1 Point 1 not found")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Finished updates.")
