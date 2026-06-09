
# 摄氏度转华氏度
def c_to_f(c):
    """摄氏度转华氏度"""
    return c * 9 / 5 + 32

# 华氏度转摄氏度
def f_to_c(f):
    """华氏度转摄氏度"""
    return (f - 32) * 5 / 9

if __name__ == "__main__":
    mode = input("请选择转换模式（1-摄氏转华氏，2-华氏转摄氏）：")
    if mode == "1":
        c = float(input("请输入摄氏度："))
        f = c_to_f(c)
        print(f"{c} 摄氏度 = {f} 华氏度")
    elif mode == "2":
        f = float(input("请输入华氏度："))
        c = f_to_c(f)
        print(f"{f} 华氏度 = {c} 摄氏度")
    else:
        print("输入有误，请输入1或2")
