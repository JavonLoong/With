# 定义一个列表，存储风机的编号
turbines = ["WT01", "WT02", "WT03", "WT04", "WT05"]

# 定义一个列表，存储每台风机对应的发电量
power = [3200, 2850, 3400, 3100, 2850]

# 使用zip函数将风机编号和发电量配对，然后用dict函数转换成字典
# wind_dict的键是风机编号，值是对应的发电量
wind_dict = dict(zip(turbines, power))

# 打印整个风机编号与发电量的字典
print(wind_dict)

# 遍历字典中的每一对风机编号和发电量
for turbine, gen in wind_dict.items():
	# 打印每台风机的编号和对应的发电量
	print(f"风机编号: {turbine}, 发电量: {gen}")

# 对字典中的项目（风机编号和发电量）按发电量进行排序
# key=lambda x: x[1] 表示按每一项的第二个元素（即发电量）排序
sorted_turbines = sorted(wind_dict.items(), key=lambda x: x[1])

# 取排序后最后一个元素（发电量最大），获取其风机编号
max_turbine = sorted_turbines[-1][0]

# 打印发电量最高的风机编号
print(f"发电量最高的风机编号: {max_turbine}")