import numpy as np
from sklearn.ensemble import RandomForestClassifier
import random
from pathlib import Path

from data_prepare import consolidate, data_provider
from postprocess import evaluate_and_visualize, write_report

random.seed(1)
np.random.seed(1)

fault_labels = {
    'Health': 0, 
    'Chipped': 1, 
    'Miss': 2,
    'Root': 3,
    'Surface': 4,
}


def main():
    base_dir = Path(__file__).resolve().parent

    train_file = base_dir / 'data_train.npz'
    test_file = base_dir / 'data_test.npz'
    if not train_file.exists():
        print(f"文件错误：训练数据不存在：{train_file}")
        return
    if not test_file.exists():
        print(f"文件错误：测试数据不存在：{test_file}")
        return

    try:
        data_train = np.load(train_file)
        data_test = np.load(test_file)
    except OSError as exc:
        print(f"文件读取错误：{exc}")
        return

    train_state_names = list(data_train.files)
    print("训练文件包含的状态名称：", train_state_names)
    for state_name in train_state_names:
        print(f"{state_name} 数据矩阵形状：{data_train[state_name].shape}")

    if "samples" not in data_test.files:
        print("数据错误：测试数据缺少 samples 数组。")
        return
    print(f"测试集 samples 形状：{data_test['samples'].shape}")

    X_all_raw, y_all_raw = consolidate(data_train, fault_labels)

    (
        X_train,
        feature_train,
        y_train,
        X_val,
        feature_val,
        y_val,
        X_test,
        feature_test,
    ) = data_provider(data_train=data_train, data_test=data_test, fault_labels=fault_labels)
    num_train = len(X_train)
    num_val = len(X_val)
    num_test = len(X_test)
    dim_feature = feature_train.shape[1]

    # 调用一个基线模型，课堂重点是理解 fit() 和 predict() 的使用。
    model = RandomForestClassifier(n_estimators=100, random_state=1)
    model.fit(feature_train, y_train)
    y_pred_val = model.predict(feature_val)
    y_pred_test = model.predict(feature_test)

    # 生成评价指标、表格、图像和报告。
    metric, output_files = evaluate_and_visualize(
        X_val,
        y_val,
        y_pred_val,
        y_pred_test,
        fault_labels,
        output_dir=base_dir,
        y_all=y_all_raw,
        X_for_plot=X_all_raw,
        y_for_plot=y_all_raw,
    )
    np.savetxt(base_dir / 'output.csv', y_pred_test, fmt='%d', delimiter=',')
    write_report(
        num_train,
        num_val,
        num_test,
        dim_feature,
        metric,
        output_files,
        report_path=base_dir / 'report.txt',
    )


if __name__ == "__main__":
    main()
