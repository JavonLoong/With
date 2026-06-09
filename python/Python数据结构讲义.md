~~~markdown
# Python语言基础回顾讲义：数据结构

## 一、学习目标

通过本讲内容回顾，要求达到以下目标：

1. 掌握 Python 中四类常用数据结构：**列表、元组、字典、集合**
2. 理解它们的定义方式、基本特点和典型应用场景
3. 能够熟练使用**列表**和**字典**进行基础编程
4. 熟悉**元组**和**集合**的基本应用方式与特点
5. 能根据实际问题选择合适的数据结构

---

## 二、什么是数据结构

数据结构可以理解为：**组织和存储数据的方式**。

在 Python 中，常见的数据结构包括：

- **列表（list）**：有序、可修改、可重复
- **元组（tuple）**：有序、不可修改、可重复
- **字典（dict）**：键值对存储、可修改、键不能重复
- **集合（set）**：无序、元素唯一、可进行集合运算

不同的数据结构适合解决不同类型的问题。

---

## 三、列表（list）

## 1. 列表的概念

列表是 Python 中最常用的数据结构之一，用于按顺序存放一组数据。

列表的特点：

- 元素**有顺序**
- 元素**可以修改**
- 元素**可以重复**
- 可以存放**不同类型**的数据

例如：

```python
scores = [85, 90, 78, 92]
names = ["Tom", "Alice", "Jack"]
mixed = [100, "Python", 3.14, True]
~~~

------

## 2. 列表的定义

列表使用方括号 `[]` 表示，多个元素之间用逗号分隔。

```python
numbers = [1, 2, 3, 4, 5]
fruits = ["apple", "banana", "orange"]
empty_list = []
```

------

## 3. 列表的访问

列表中的元素有位置编号，称为**索引**。

- 第一个元素索引为 `0`
- 第二个元素索引为 `1`
- 倒数第一个元素索引为 `-1`

```python
fruits = ["apple", "banana", "orange"]

print(fruits[0])   # apple
print(fruits[1])   # banana
print(fruits[-1])  # orange
```

------

## 4. 列表的常用操作

### （1）获取长度

```python
nums = [10, 20, 30]
print(len(nums))
```

### （2）修改元素

```python
nums = [10, 20, 30]
nums[1] = 99
print(nums)
```

### （3）添加元素

#### 在末尾添加一个元素：`append()`

```python
nums = [1, 2, 3]
nums.append(4)
print(nums)
```

#### 在指定位置插入元素：`insert()`

```python
nums = [1, 2, 3]
nums.insert(1, 100)
print(nums)
```

### （4）删除元素

#### 删除末尾元素：`pop()`

```python
nums = [1, 2, 3]
nums.pop()
print(nums)
```

#### 删除指定位置元素：`pop(index)`

```python
nums = [1, 2, 3]
nums.pop(1)
print(nums)
```

#### 按值删除：`remove()`

```python
nums = [1, 2, 3, 2]
nums.remove(2)
print(nums)
```

说明：`remove()` 只删除第一个匹配到的元素。

### （5）查找元素

```python
nums = [10, 20, 30, 20]
print(nums.index(20))   # 返回第一次出现的位置
print(30 in nums)       # 判断元素是否存在
```

### （6）排序

```python
nums = [5, 2, 8, 1]
nums.sort()
print(nums)
```

降序排序：

```python
nums = [5, 2, 8, 1]
nums.sort(reverse=True)
print(nums)
```

### （7）反转

```python
nums = [1, 2, 3, 4]
nums.reverse()
print(nums)
```

------

## 5. 列表切片

切片可以一次取出列表中的一部分元素。

语法格式：

```python
列表名[开始:结束:步长]
```

示例：

```python
nums = [10, 20, 30, 40, 50]

print(nums[1:4])   # [20, 30, 40]
print(nums[:3])    # [10, 20, 30]
print(nums[2:])    # [30, 40, 50]
print(nums[::2])   # [10, 30, 50]
```

------

## 6. 列表遍历

列表经常与循环结合使用。

### 使用 `for` 遍历元素

```python
names = ["Tom", "Alice", "Jack"]

for name in names:
    print(name)
```

### 使用索引遍历

```python
names = ["Tom", "Alice", "Jack"]

for i in range(len(names)):
    print(i, names[i])
```

------

## 7. 列表的典型应用

### 示例 1：计算列表中所有元素的和

```python
nums = [10, 20, 30, 40]
total = 0

for x in nums:
    total += x

print("总和为：", total)
```

### 示例 2：找出列表中的最大值

```python
nums = [45, 67, 12, 89, 34]
max_num = nums[0]

for x in nums:
    if x > max_num:
        max_num = x

print("最大值为：", max_num)
```

### 示例 3：统计及格人数

```python
scores = [58, 76, 89, 45, 92, 61]
count = 0

for score in scores:
    if score >= 60:
        count += 1

print("及格人数：", count)
```

------

## 四、元组（tuple）

## 1. 元组的概念

元组与列表类似，也是一组有序数据的组合。

元组的特点：

- 元素**有顺序**
- 元素**不能修改**
- 元素**可以重复**

例如：

```python
t = (10, 20, 30)
names = ("Tom", "Alice", "Jack")
```

------

## 2. 元组的定义

元组使用圆括号 `()` 表示。

```python
t1 = (1, 2, 3)
t2 = ("a", "b", "c")
```

定义单个元素的元组时，要注意逗号：

```python
t = (5,)
print(type(t))
```

如果写成：

```python
t = (5)
```

这不是元组，而是整数。

------

## 3. 元组的访问

元组和列表一样，可以通过索引访问元素。

```python
t = ("red", "green", "blue")

print(t[0])
print(t[-1])
```

------

## 4. 元组的特点与应用

由于元组不可修改，因此适合表示**固定不变的数据**。

例如：

- 一个坐标点：`(x, y)`
- 一个日期：`(2025, 3, 10)`
- 一个学生信息的固定记录

示例：

```python
point = (3, 5)
date = (2026, 3, 20)
```

元组也支持遍历：

```python
t = (10, 20, 30)

for x in t:
    print(x)
```

------

## 五、字典（dict）

## 1. 字典的概念

字典是 Python 中非常重要的数据结构，用于存放**键值对**数据。

字典的形式为：

```python
键: 值
```

例如：

```python
student = {
    "name": "Tom",
    "age": 18,
    "score": 92
}
```

字典的特点：

- 按**键值对**存储数据
- 通过**键**访问对应的值
- **键不能重复**
- 字典**可修改**
- 适合表示“属性—值”对应关系

------

## 2. 字典的定义

字典使用花括号 `{}` 表示。

```python
student = {
    "name": "Alice",
    "age": 20,
    "major": "Computer Science"
}
```

空字典：

```python
d = {}
```

------

## 3. 字典的访问

通过键访问值：

```python
student = {
    "name": "Tom",
    "age": 18,
    "score": 90
}

print(student["name"])
print(student["score"])
```

注意：如果访问不存在的键，会报错。

更安全的方式是使用 `get()`：

```python
print(student.get("name"))
print(student.get("gender"))        # 不存在时返回 None
print(student.get("gender", "无"))  # 可指定默认值
```

------

## 4. 字典的常用操作

### （1）修改值

```python
student = {"name": "Tom", "age": 18}
student["age"] = 19
print(student)
```

### （2）添加键值对

```python
student = {"name": "Tom"}
student["score"] = 95
print(student)
```

### （3）删除键值对

```python
student = {"name": "Tom", "age": 18, "score": 95}
del student["age"]
print(student)
```

也可以使用 `pop()`：

```python
student = {"name": "Tom", "age": 18}
student.pop("age")
print(student)
```

### （4）获取所有键、值、键值对

```python
student = {"name": "Tom", "age": 18, "score": 95}

print(student.keys())
print(student.values())
print(student.items())
```

------

## 5. 字典遍历

### 遍历键

```python
student = {"name": "Tom", "age": 18, "score": 95}

for key in student:
    print(key, student[key])
```

### 遍历键值对

```python
student = {"name": "Tom", "age": 18, "score": 95}

for key, value in student.items():
    print(key, value)
```

------

## 6. 字典的典型应用

### 示例 1：存储学生信息

```python
student = {
    "name": "Alice",
    "age": 19,
    "score": 88
}

print("姓名：", student["name"])
print("年龄：", student["age"])
print("成绩：", student["score"])
```

### 示例 2：统计字符出现次数

```python
text = "banana"
count_dict = {}

for ch in text:
    if ch in count_dict:
        count_dict[ch] += 1
    else:
        count_dict[ch] = 1

print(count_dict)
```

运行结果：

```python
{'b': 1, 'a': 3, 'n': 2}
```

### 示例 3：统计学生成绩等级人数

```python
scores = [95, 82, 76, 58, 91, 67, 45]
result = {"优秀": 0, "良好": 0, "及格": 0, "不及格": 0}

for score in scores:
    if score >= 90:
        result["优秀"] += 1
    elif score >= 80:
        result["良好"] += 1
    elif score >= 60:
        result["及格"] += 1
    else:
        result["不及格"] += 1

print(result)
```

------

## 六、集合（set）

## 1. 集合的概念

集合用于存放**不重复元素**。

集合的特点：

- 元素**无序**
- 元素**唯一**
- 集合本身**可修改**
- 常用于**去重**和**集合运算**

例如：

```python
s = {1, 2, 3, 4}
```

------

## 2. 集合的定义

```python
s = {1, 2, 3}
```

空集合不能写成 `{}`，因为 `{}` 表示空字典。

应写为：

```python
s = set()
```

------

## 3. 集合的基本操作

### 添加元素

```python
s = {1, 2, 3}
s.add(4)
print(s)
```

### 删除元素

```python
s = {1, 2, 3}
s.remove(2)
print(s)
```

### 判断元素是否存在

```python
s = {1, 2, 3}
print(2 in s)
```

------

## 4. 集合的典型应用

### 示例 1：列表去重

```python
nums = [1, 2, 2, 3, 4, 4, 5]
result = set(nums)
print(result)
```

### 示例 2：交集、并集

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

print(a & b)   # 交集
print(a | b)   # 并集
print(a - b)   # 差集
```

集合特别适合解决“重复元素处理”和“共同元素查找”等问题。

------

## 七、四种数据结构对比

| 数据结构   | 表示方式        | 是否有序 | 是否可重复 | 是否可修改 | 典型用途                 |
| ---------- | --------------- | -------- | ---------- | ---------- | ------------------------ |
| 列表 list  | `[]`            | 有序     | 可重复     | 可修改     | 存放一组按顺序排列的数据 |
| 元组 tuple | `()`            | 有序     | 可重复     | 不可修改   | 表示固定不变的数据       |
| 字典 dict  | `{键:值}`       | 键值对应 | 键不可重复 | 可修改     | 存储属性信息、映射关系   |
| 集合 set   | `{}` 或 `set()` | 无序     | 不可重复   | 可修改     | 去重、集合运算           |

------

## 八、如何选择合适的数据结构

在编程中，应根据问题特点选择数据结构。

### 1. 需要按顺序保存多个数据，并且经常修改

使用**列表**

例如：

- 学生成绩列表
- 商品价格列表
- 一组测量数据

### 2. 数据内容固定，不希望被修改

使用**元组**

例如：

- 坐标
- 日期
- 固定配置项

### 3. 需要表示“名称—值”对应关系

使用**字典**

例如：

- 学生信息
- 用户资料
- 统计结果

### 4. 需要去重或查找共同元素

使用**集合**

例如：

- 去除重复编号
- 比较两组数据是否有相同项

------

## 九、综合示例

## 示例 1：使用列表计算平均分

```python
scores = [80, 92, 76, 88, 95]
total = 0

for score in scores:
    total += score

average = total / len(scores)
print("平均分为：", average)
```

------

## 示例 2：使用字典存储学生信息并输出

```python
student = {
    "name": "Tom",
    "age": 18,
    "class": "Class 1",
    "score": 93
}

for key, value in student.items():
    print(key, ":", value)
```

------

## 示例 3：列表与字典结合使用

```python
students = [
    {"name": "Tom", "score": 85},
    {"name": "Alice", "score": 92},
    {"name": "Jack", "score": 76}
]

for student in students:
    print(student["name"], "的成绩是", student["score"])
```

说明：

- 列表用于存放多个学生
- 字典