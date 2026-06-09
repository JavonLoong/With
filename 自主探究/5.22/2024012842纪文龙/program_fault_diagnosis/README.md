# 齿轮箱振动状态识别基础程序

本程序用于课堂基础练习，读取齿轮箱振动数据，生成简单摘要特征，调用一个随机森林基线模型，并输出报告、预测结果和图像。课堂重点是 Python 基础语法、NumPy、pandas、Matplotlib、文件输出和模块化组织；`sklearn` 只作为现成工具调用。

## 文件说明

- `data_train.npz`：训练数据
- `data_test.npz`：测试数据
- `main.py`：程序入口
- `data_prepare.py`：数据合并、标签生成、标准化和基础摘要特征
- `postprocess.py`：评价指标、图片绘制和报告写出
- `report.txt`：示例运行报告
- `output.csv`：测试集预测结果
- `sample_waveforms.png`：不同状态样本曲线图
- `class_counts.csv`：训练样本类别数量表
- `class_counts.png`：训练样本类别数量柱状图
- `prediction_distribution.csv`：测试集预测标签分布表
- `prediction_distribution.png`：测试集预测标签分布柱状图

## 运行方法

在课程根目录运行：

```bash
python 00_课前发送材料/program_fault_diagnosis/main.py
```

或进入本文件夹运行：

```bash
python main.py
```

程序将：

1. 读取 `data_train.npz` 和 `data_test.npz`
2. 在终端输出训练文件包含的状态名称、每类数据矩阵形状和测试集 `samples` 形状
3. 合并 5 类训练样本并生成标签
4. 划分训练集和验证集
5. 生成 8 个基础摘要特征
6. 调用随机森林基线模型
7. 输出验证集指标
8. 生成测试集预测结果 `output.csv`
9. 生成报告、统计表格和基础图像

## 课堂定位

本程序适合用于以下内容的入门复习：

- NumPy 数据读取
- 数组形状理解
- 字典与标签编码
- 函数和类的组织
- pandas 读取和整理 `output.csv`
- Matplotlib 绘制样本曲线和柱状图
- Scikit-learn 基础接口调用
- 报告和 CSV 文件输出
