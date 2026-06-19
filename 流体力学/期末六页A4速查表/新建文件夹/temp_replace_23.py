import re

file_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace Sub-library 2
start_str2 = r"\infoh{选择判断秒杀库-2. (第5章) 理想不可压缩流体的二维无旋和有旋流动}"
end_str2 = r"\infoh{选择判断秒杀库-3. (第7章) 气体动力学基础}"
start_idx2 = content.find(start_str2)
end_idx2 = content.find(end_str2)

if start_idx2 != -1 and end_idx2 != -1:
    new_block2 = start_str2 + "\n" + r"""\infotxt{%
1. \key{流函数存在条件}：\\
{\fontspec{SimSun}①} \warn{二维}（平面或轴对称）且\warn{不可压缩}流动。\\
{\fontspec{SimSun}②} 源于连续性方程（质量守恒），粘性流体只要满足该条件\warn{也有流函数$\psi$}。\\
{\fontspec{SimSun}③} 其存在与有无粘性、有旋无旋、定常与否无关。\\
2. \key{势函数存在条件}：\\
{\fontspec{SimSun}①} 流动\warn{无旋}（旋度 $\nabla\times\bm V=0$）。\\
{\fontspec{SimSun}②} 源于无旋定义，\warn{与维数、压缩性、有无粘性、定常与否无关}。\\
3. \key{混淆要点}：\\
{\fontspec{SimSun}①} 非定常不可压流场可能存在流函数（二维即存在），有流函数不一定有势函数（可能有旋）。\\
{\fontspec{SimSun}②} 二维不可压有旋流动有流函数但无势函数。\\
{\fontspec{SimSun}③} 三维无旋流动有势函数但无二维流函数。\\
{\fontspec{SimSun}④} 有粘流动在局部无旋时也可以存在势函数。\\
{\fontspec{SimSun}⑤} 二维无旋流动中，\warn{流线与等势线总是正交的}。\\
4. \key{圆柱绕流与升力}：\\
{\fontspec{SimSun}①} 有速度环量 $\Gamma$ 产生升力 $L=\rho V \Gamma$（库塔-儒可夫斯基定理）。\\
{\fontspec{SimSun}②} \key{K-J假设（后缘条件）}：在理想流体假设下流过平板（或机翼等）时，首尾端点速度绝对值为无穷大，与实际流动不符。为在理想流体假设下模拟真实流动，库塔-儒克夫斯基提出假设：在平板（或机翼等）有攻角绕流中，一定存在速度环量，其大小恰好能使背面的驻点移至后缘，使后缘端点的速度保持为有限值。
}

"""
    content = content[:start_idx2] + new_block2 + content[end_idx2:]
    print("Sub-library 2 replaced successfully")
else:
    print("WARNING: Sub-library 2 indices not found")

# Re-read content or update indices since content changed size
start_str3 = r"\infoh{选择判断秒杀库-3. (第7章) 气体动力学基础}"
end_str3 = r"\infoh{选择判断秒杀库-4. (第8章) 相似理论与量纲分析}"
start_idx3 = content.find(start_str3)
end_idx3 = content.find(end_str3)

if start_idx3 != -1 and end_idx3 != -1:
    new_block3 = start_str3 + "\n" + r"""\infotxt{%
1. \key{声速与马赫数}：\\
{\fontspec{SimSun}①} 声速 $c=\sqrt{\gamma RT}$ 仅是温度的函数。\\
{\fontspec{SimSun}②} 马赫数 $Ma=V/c$ 反映可压缩程度，当 $Ma < 0.3$ 时可近似为不可压缩流动。\\
{\fontspec{SimSun}③} 声波传播极快，\warn{为等熵过程，而非等温过程}。\\
2. \key{气体动力流动与波}：\\
{\fontspec{SimSun}①} 微弱扰动线在超声速流（$Ma>1$）中形成的线为\warn{马赫线}（其半顶角为马赫角 $\alpha = \arcsin(1/Ma)$）。\\
{\fontspec{SimSun}②} 扰动只能传向马赫锥内部，外部为未扰动区。亚声速中扰动传向全场。\\
{\fontspec{SimSun}③} 激波后压力、温度、密度骤升，\warn{流速骤降（超变亚）}。激波仅在超声速流动中可能产生。\\
3. \key{喷管核心结论}：\\
{\fontspec{SimSun}①} 渐缩喷管出口最大只能达声速；渐缩渐扩（拉瓦尔）喷管喉部达声速，出口可达超声速。\\
{\fontspec{SimSun}②} \warn{最大质量流量唯一由喉部面积和上游滞止状态决定}，管道存在正激波或出口有膨胀波不改变此最大流量。
}

"""
    content = content[:start_idx3] + new_block3 + content[end_idx3:]
    print("Sub-library 3 replaced successfully")
else:
    print("WARNING: Sub-library 3 indices not found")

start_str4 = r"\infoh{选择判断秒杀库-4. (第8章) 相似理论与量纲分析}"
end_str4 = r"\infoh{选择判断秒杀库-5. (第9章) 湍流}"
start_idx4 = content.find(start_str4)
end_idx4 = content.find(end_str4)

if start_idx4 != -1 and end_idx4 != -1:
    new_block4 = start_str4 + "\n" + r"""\infotxt{%
1. \key{相似性三个条件}：\\
{\fontspec{SimSun}①} 几何相似（对应线性尺度比例相同）、运动相似（对应点速度方向相同、大小比例相同）、动力相似（对应点受力方向相同、大小比例相同）。\\
{\fontspec{SimSun}②} 几何相似是前提，动力相似是保证，\warn{运动相似是目的}。\\
2. \key{动力相似准则}：\\
{\fontspec{SimSun}①} 重力起主导作用取\warn{弗劳德数相似 $Fr = V/\sqrt{gl}$}（如明渠流动、船舶阻力）。\\
{\fontspec{SimSun}②} 粘性力起主导作用取\warn{雷诺数相似 $Re = \rho V l/\mu$}（如管流、低速飞行器绕流）。\\
{\fontspec{SimSun}③} 压力起主导作用取\warn{欧拉数相似 $Eu = p/\rho V^2$}。弹性力起主导作用取\warn{马赫数相似 $Ma = V/c$}。\\
3. \key{模型试验限制}：\\
{\fontspec{SimSun}①} 重力与粘性力同时起主导作用时，普通工作介质的缩尺试验\warn{无法同时保证 $Re$ 相似和 $Fr$ 相似}（因为速度比与尺度比的缩放关系冲突）。\\
4. \key{量纲分析基本原则}：\\
{\fontspec{SimSun}①} 白金汉 $\pi$ 定理中无量纲自变量 $\pi$ 数等于变量数 $n$ 减去基本量纲数 $m$。\\
{\fontspec{SimSun}②} 量纲分析中只要选取的重复变量在量纲上相互独立即可（如可取 $\rho,V,L$ 或 $p,V,L$）。
}

"""
    content = content[:start_idx4] + new_block4 + content[end_idx4:]
    print("Sub-library 4 replaced successfully")
else:
    print("WARNING: Sub-library 4 indices not found")

start_str5 = r"\infoh{选择判断秒杀库-5. (第9章) 湍流}"
end_str5 = r"\infoh{选择判断秒杀库-6. (第10章) 边界层理论基础}"
start_idx5 = content.find(start_str5)
end_idx5 = content.find(end_str5)

if start_idx5 != -1 and end_idx5 != -1:
    new_block5 = start_str5 + "\n" + r"""\infotxt{%
1. \key{转捩与稳定性}：\\
{\fontspec{SimSun}①} 流态由层流向湍流转捩的临界雷诺数受壁面粗糙度和外界干扰影响，\warn{不是确定的常数}。\\
2. \key{雷诺应力与混合长度}：\\
{\fontspec{SimSun}①} RANS方程因脉动应力不封闭。紊流圆管中总切应力沿断面呈线性分布。\\
{\fontspec{SimSun}②} Prandtl\key{混合长度理论的物理意义}：将湍流中微团的脉动与气体分子的运动相比拟。\\
{\fontspec{SimSun}③} 假定流动微团横向移动混合长度 $l$ 后与周围流体混合并传递时均物理量。\\
3. \key{数值模拟方法对比}：\\
{\fontspec{SimSun}①} \warn{DNS（直接模拟）}不加近似，网格极密，计算量最大，仅适合低Re。\\
{\fontspec{SimSun}②} \warn{LES（大涡模拟）}大涡求解，小涡使用SGS模型近似，计算量中等。\\
{\fontspec{SimSun}③} \warn{RANS（时均方程）}只求解时均流动，脉动应力用湍流模型闭合，最实用。
}

"""
    content = content[:start_idx5] + new_block5 + content[end_idx5:]
    print("Sub-library 5 replaced successfully")
else:
    print("WARNING: Sub-library 5 indices not found")

start_str6 = r"\infoh{选择判断秒杀库-6. (第10章) 边界层理论基础}"
# Sub-library 6 goes to the end of multicols
end_str6 = r"\end{multicols*}"
start_idx6 = content.find(start_str6)
end_idx6 = content.find(end_str6)

if start_idx6 != -1 and end_idx6 != -1:
    new_block6 = start_str6 + "\n" + r"""\infotxt{%
1. \key{边界层外界线与摩擦阻力}：\\
{\fontspec{SimSun}①} 由名义厚度 $\delta$ 标定的外界线不是流线。排挤厚度 $\delta^*$ 和动量损失厚度 $\theta$ 均显著小于 $\delta$。\\
{\fontspec{SimSun}②} \key{摩擦阻力定义}：当物体与流体有相对运动时与流体接触的物体表面要受到流体剪应力作用，剪应力的合力称为摩擦阻力。\\
2. \key{流动分离与卡门涡街}：\\
{\fontspec{SimSun}①} 绕流钝体两侧边界层因逆压与粘性脱流形成卡门涡街，其频率 $f = St \frac{U}{d}$，阻力危机前 $St \approx 0.2$。\\
{\fontspec{SimSun}②} 流动分离的两个条件：存在逆压梯度区；壁面及粘性对流体的阻滞作用。\\
{\fontspec{SimSun}③} 高Re流线体后部仍会出现逆压区，在大攻角等工况下仍可能发生分离。\\
3. \key{阻力危机}：\\
{\fontspec{SimSun}①} 球/圆柱在临界 $Re$ 附近边界层由层流转捩为湍流，抗逆压梯度能力增强，分离点后移、尾迹变窄，使\warn{阻力系数 $C_D$ 骤降}。
}

"""
    content = content[:start_idx6] + new_block6 + content[end_idx6:]
    print("Sub-library 6 replaced successfully")
else:
    print("WARNING: Sub-library 6 indices not found")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Finished all replacements.")
