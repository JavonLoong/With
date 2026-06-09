import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from pathlib import Path

configs = {
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "font.size": 12,
    "axes.unicode_minus": False,
}
rcParams.update(configs)


def metric_classify(pred, true):
    # 将模型输出转换为预测类别标签
    true = true.astype(int)
    pred = pred.astype(int)

    # 计算各项指标
    accuracy = accuracy_score(true, pred)
    precision = precision_score(true, pred, average="weighted", zero_division=0)
    recall = recall_score(true, pred, average="weighted", zero_division=0)
    f1 = f1_score(true, pred, average="weighted", zero_division=0)

    return {
        "acc": accuracy,
        "pre": precision,
        "rec": recall,
        "f1": f1,
    }


def _label_records(values, fault_labels):
    values = np.asarray(values).astype(int)
    total = len(values)
    records = []

    for label_name, label in fault_labels.items():
        count = int(np.sum(values == label))
        records.append(
            {
                "label": label,
                "label_name": label_name,
                "count": count,
                "ratio": count / total if total else 0.0,
            }
        )

    return records


def save_label_table_and_bar(values, fault_labels, csv_path, fig_path, title):
    records = _label_records(values, fault_labels)
    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    plt.figure(figsize=(7, 4.5))
    plt.bar(df["label_name"], df["count"], color="#4E79A7")
    plt.title(title)
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()


def save_sample_waveforms(X, y, fault_labels, fig_path):
    line_styles = ["-", "--", "-.", ":", "-"]

    plt.figure(figsize=(9, 5))
    for index, (label_name, label) in enumerate(fault_labels.items()):
        sample_ids = np.where(y == label)[0]
        if len(sample_ids) == 0:
            continue
        plt.plot(
            X[sample_ids[0]],
            linestyle=line_styles[index % len(line_styles)],
            linewidth=1.0,
            alpha=0.85,
            label=label_name,
        )

    plt.title("Sample waveform by class")
    plt.xlabel("Sample index")
    plt.ylabel("Vibration value")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()


def evaluate_and_visualize(
    X,
    y,
    y_pred,
    y_pred_test,
    fault_labels,
    output_dir,
    y_all=None,
    X_for_plot=None,
    y_for_plot=None,
):
    output_dir = Path(output_dir)
    metric = metric_classify(pred=y_pred, true=y)

    if y_all is None:
        y_all = y
    if X_for_plot is None:
        X_for_plot = X
    if y_for_plot is None:
        y_for_plot = y

    output_files = {
        "sample_waveforms": output_dir / "sample_waveforms.png",
        "class_counts_csv": output_dir / "class_counts.csv",
        "class_counts_png": output_dir / "class_counts.png",
        "prediction_distribution_csv": output_dir / "prediction_distribution.csv",
        "prediction_distribution_png": output_dir / "prediction_distribution.png",
    }

    save_sample_waveforms(
        X_for_plot,
        y_for_plot,
        fault_labels,
        output_files["sample_waveforms"],
    )
    save_label_table_and_bar(
        y_all,
        fault_labels,
        output_files["class_counts_csv"],
        output_files["class_counts_png"],
        "Training samples by class",
    )
    save_label_table_and_bar(
        y_pred_test,
        fault_labels,
        output_files["prediction_distribution_csv"],
        output_files["prediction_distribution_png"],
        "Predicted labels on test set",
    )

    return metric, output_files


def write_report(
    num_train,
    num_val,
    num_test,
    dim_feature,
    metric,
    output_files,
    report_path="./report.txt",
):
    """
    生成并保存分析报告
    
    Args:
        num_train: 训练集样本数
        num_val: 验证集样本数
        num_test: 测试集样本数
        dim_feature: 特征维度
        metric: 包含评价指标的字典
        output_files: 程序生成的图片和表格文件
        report_path: 报告保存路径
    """
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("========== 齿轮箱振动信号分类分析报告 ==========\n")
        f.write(f"数据加载情况：训练样本数：{num_train}, 验证样本数：{num_val}, 测试样本数：{num_test}, 特征维度：{dim_feature}\n")
        f.write("--- 随机森林基线模型 ---\n")
        f.write(f"验证集准确率：{metric['acc']:.4f}\n")
        f.write(f"验证集精确率：{metric['pre']:.4f}\n")
        f.write(f"验证集召回率：{metric['rec']:.4f}\n")
        f.write(f"验证集F1分数：{metric['f1']:.4f}\n")
        f.write("--- 文件输出 ---\n")
        f.write("测试集预测结果已保存至：output.csv\n")
        for path in output_files.values():
            f.write(f"结果文件已保存至：{Path(path).name}\n")
