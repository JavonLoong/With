"""
探索任务 1：文件 I/O 与数据保存练习

围绕"计算好的特征值如何保存和管理"进行探索：
    - 使用 NumPy 计算每个样本的基础摘要特征
    - 使用 pandas 将特征值整理为 DataFrame
    - 按类别分别建立文件夹，例如 features_by_class/Health/
    - 将不同类别的特征保存为 .csv、.npy、.txt 三种格式
    - 将类别样本数量、预测标签分布等结果保存为 CSV 文件
"""

import numpy as np
import pandas as pd
from pathlib import Path

from data_prepare import consolidate, BasicFeatureExtractor, data_provider
from sklearn.ensemble import RandomForestClassifier

# ── 标签字典 ──────────────────────────────────────────────
fault_labels = {
    'Health': 0,
    'Chipped': 1,
    'Miss': 2,
    'Root': 3,
    'Surface': 4,
}

FEATURE_NAMES = [
    'mean', 'std', 'max', 'min',
    'rms', 'peak_to_peak', 'max_abs', 'abs_mean',
]

np.random.seed(1)


def save_features_by_class(features, y, output_root):
    """按类别建立子文件夹，将特征分别保存为 csv / npy / txt 三种格式。"""
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    for label_name, label_id in fault_labels.items():
        mask = (y == label_id)
        class_features = features[mask]

        class_dir = output_root / label_name
        class_dir.mkdir(parents=True, exist_ok=True)

        # CSV（pandas）
        df = pd.DataFrame(class_features, columns=FEATURE_NAMES)
        df.to_csv(class_dir / 'features.csv', index=False, encoding='utf-8-sig')

        # NPY（NumPy 二进制）
        np.save(class_dir / 'features.npy', class_features)

        # TXT（纯文本，空格分隔）
        np.savetxt(class_dir / 'features.txt', class_features,
                   fmt='%.6f', header='  '.join(FEATURE_NAMES), comments='')

        print(f"  [{label_name}] {class_features.shape[0]} samples -> {class_dir}")


def save_class_counts(y, output_path):
    """统计各类别样本数量，保存为 CSV。"""
    total = len(y)
    records = []
    for label_name, label_id in fault_labels.items():
        count = int(np.sum(y == label_id))
        records.append({
            'label': label_id,
            'label_name': label_name,
            'count': count,
            'ratio': f'{count / total:.2%}',
        })
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n  class_counts -> {output_path}")
    print(df.to_string(index=False))


def save_prediction_distribution(y_pred, output_path):
    """统计测试集预测标签分布，保存为 CSV。"""
    total = len(y_pred)
    records = []
    for label_name, label_id in fault_labels.items():
        count = int(np.sum(y_pred == label_id))
        records.append({
            'label': label_id,
            'label_name': label_name,
            'predicted_count': count,
            'ratio': f'{count / total:.2%}',
        })
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n  prediction_distribution -> {output_path}")
    print(df.to_string(index=False))


def verify_saved_files(output_root):
    """读取保存的文件，验证内容完整性。"""
    output_root = Path(output_root)
    print("\n========== verify ==========")
    for label_name in fault_labels:
        d = output_root / label_name
        try:
            df = pd.read_csv(d / 'features.csv')
            arr = np.load(d / 'features.npy')
            txt = np.loadtxt(d / 'features.txt', skiprows=1)
            print(f"  [{label_name}] CSV {df.shape}  NPY {arr.shape}  TXT {txt.shape}  OK")
        except FileNotFoundError as e:
            print(f"  [{label_name}] MISSING: {e}")


# ── main ──────────────────────────────────────────────────
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent

    # 1. read data
    data_train = np.load(base_dir / 'data_train.npz')
    data_test = np.load(base_dir / 'data_test.npz')
    X_all, y_all = consolidate(data_train, fault_labels)

    # 2. extract features
    extractor = BasicFeatureExtractor(fs=5120)
    features_all = extractor.feature(X_all)
    print(f"features_all.shape = {features_all.shape}")

    # 3. preview
    df_preview = pd.DataFrame(features_all[:5], columns=FEATURE_NAMES)
    print("\nFirst 5 samples:")
    print(df_preview.to_string(index=False))

    # 4. save features by class
    feat_dir = base_dir / 'features_by_class'
    print("\n--- save features by class ---")
    save_features_by_class(features_all, y_all, feat_dir)

    # 5. save class counts
    print("\n--- class counts ---")
    save_class_counts(y_all, base_dir / 'class_counts_summary.csv')

    # 6. train model and save prediction distribution
    (_, feat_train, y_train,
     _, feat_val, y_val,
     _, feat_test) = data_provider(data_train, data_test, fault_labels)

    model = RandomForestClassifier(n_estimators=100, random_state=1)
    model.fit(feat_train, y_train)
    y_pred_test = model.predict(feat_test)

    print("\n--- prediction distribution ---")
    save_prediction_distribution(y_pred_test, base_dir / 'prediction_distribution_summary.csv')

    # 7. verify
    verify_saved_files(feat_dir)

    print("\n[DONE]")
