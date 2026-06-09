"""
探索任务 2：Matplotlib 可视化扩展练习

围绕"如何把振动数据和统计结果画出来"进行探索：
    1. 绘制不同类别样本的振动曲线
    2. 改变线型、颜色、透明度、标题、图例、坐标轴标签等样式
    3. 绘制类别样本数柱状图、预测标签分布柱状图
    4. 使用 seaborn 绘制更美观的柱状图和热力图
    5. 将图像保存为 .png
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.pyplot import rcParams
from pathlib import Path

import seaborn as sns

from data_prepare import consolidate, data_provider
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

# ── 全局样式 ──────────────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.1)
rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "axes.unicode_minus": False,
    "figure.dpi": 120,
})

# 精选调色板
PALETTE = ['#3A86FF', '#FF6B35', '#E5383B', '#2EC4B6', '#6A994E']
BG_COLOR = '#FAFBFC'

fault_labels = {
    'Health': 0,
    'Chipped': 1,
    'Miss': 2,
    'Root': 3,
    'Surface': 4,
}

np.random.seed(1)


# ────────────────────────────────────────────────────────
# 图 1：不同类别样本的振动曲线
# ────────────────────────────────────────────────────────
def plot_waveforms(X, y, output_path):
    line_styles = ['-', '--', '-.', ':', (0, (3, 1, 1, 1))]
    alphas = [0.9, 0.8, 0.75, 0.7, 0.65]

    fig, axes = plt.subplots(5, 1, figsize=(14, 16), sharex=True)
    fig.patch.set_facecolor(BG_COLOR)
    fig.suptitle('Vibration Waveforms by Gear Condition',
                 fontsize=18, fontweight='bold', y=0.98, color='#1A1A2E')

    for idx, (label_name, label_id) in enumerate(fault_labels.items()):
        ax = axes[idx]
        ax.set_facecolor('#FFFFFF')
        sample_ids = np.where(y == label_id)[0]
        if len(sample_ids) == 0:
            continue

        for j, sid in enumerate(sample_ids[:3]):
            ax.plot(
                X[sid],
                linestyle=line_styles[idx],
                linewidth=0.6 + 0.2 * j,
                alpha=0.35 + 0.25 * j,
                color=PALETTE[idx],
                label=f'{label_name} #{j+1}',
            )

        ax.set_ylabel('Amplitude', fontsize=10, color='#444444')
        ax.legend(loc='upper right', fontsize=8, framealpha=0.85,
                  edgecolor='#DDDDDD', fancybox=True)
        ax.set_title(f'{label_name} (label={label_id})',
                     fontsize=12, loc='left', color=PALETTE[idx], fontweight='bold')
        ax.tick_params(colors='#666666', labelsize=9)
        ax.grid(alpha=0.15)

    axes[-1].set_xlabel('Sample Index', fontsize=12, color='#444444')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_path, dpi=220, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close()
    print(f"[1] Waveforms -> {output_path}")


# ────────────────────────────────────────────────────────
# 图 2：训练集类别样本数 — 精致柱状图
# ────────────────────────────────────────────────────────
def plot_class_bar(y, output_path):
    labels = list(fault_labels.keys())
    counts = [int(np.sum(y == lid)) for lid in fault_labels.values()]
    total = sum(counts)

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.bar(labels, counts, color=PALETTE, edgecolor='white',
                  linewidth=2, width=0.6, zorder=3)

    # 柱顶标注：数量 + 百分比
    for bar, count in zip(bars, counts):
        pct = count / total * 100
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 8,
                f'{count}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold',
                color='#333333', linespacing=1.4)

    ax.set_title('Training Samples by Gear Condition',
                 fontsize=16, fontweight='bold', color='#1A1A2E', pad=20)
    ax.set_xlabel('Gear Condition', fontsize=13, color='#444444', labelpad=10)
    ax.set_ylabel('Sample Count', fontsize=13, color='#444444', labelpad=10)
    ax.set_ylim(0, max(counts) * 1.25)
    ax.tick_params(colors='#555555', labelsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis='y', alpha=0.2, zorder=0)

    # 底部添加总数注释
    ax.text(0.98, 0.02, f'Total: {total} samples',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=10, color='#888888', style='italic')

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close()
    print(f"[2] Class bar -> {output_path}")


# ────────────────────────────────────────────────────────
# 图 3：测试集预测标签分布 — 精致柱状图
# ────────────────────────────────────────────────────────
def plot_prediction_bar(y_pred, output_path):
    labels = list(fault_labels.keys())
    counts = [int(np.sum(y_pred == lid)) for lid in fault_labels.values()]
    total = sum(counts)

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.bar(labels, counts, color=PALETTE, edgecolor='white',
                  linewidth=2, width=0.6, zorder=3)

    for bar, count in zip(bars, counts):
        pct = count / total * 100
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 3,
                f'{count}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold',
                color='#333333', linespacing=1.4)

    ax.set_title('Predicted Labels on Test Set',
                 fontsize=16, fontweight='bold', color='#1A1A2E', pad=20)
    ax.set_xlabel('Predicted Condition', fontsize=13, color='#444444', labelpad=10)
    ax.set_ylabel('Count', fontsize=13, color='#444444', labelpad=10)
    ax.set_ylim(0, max(counts) * 1.3)
    ax.tick_params(colors='#555555', labelsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis='y', alpha=0.2, zorder=0)

    ax.text(0.98, 0.02, f'Total: {total} predictions',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=10, color='#888888', style='italic')

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close()
    print(f"[3] Prediction bar -> {output_path}")


# ────────────────────────────────────────────────────────
# 图 4：混淆矩阵热力图 — 精致版
# ────────────────────────────────────────────────────────
def plot_heatmap(y_true, y_pred, output_path):
    cm = confusion_matrix(y_true, y_pred)
    labels = list(fault_labels.keys())

    # 计算百分比
    cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100

    # 构建标注文字：数量 + 百分比
    annot_text = np.empty_like(cm, dtype=object)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            annot_text[i, j] = f'{cm[i, j]}\n({cm_pct[i, j]:.1f}%)'

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor(BG_COLOR)

    sns.heatmap(cm, annot=annot_text, fmt='', cmap='Blues',
                xticklabels=labels, yticklabels=labels,
                linewidths=2, linecolor='white',
                cbar_kws={'label': 'Count', 'shrink': 0.8},
                square=True, ax=ax)

    ax.set_title('Confusion Matrix (Validation Set)',
                 fontsize=16, fontweight='bold', color='#1A1A2E', pad=15)
    ax.set_xlabel('Predicted', fontsize=13, color='#444444', labelpad=10)
    ax.set_ylabel('True', fontsize=13, color='#444444', labelpad=10)
    ax.tick_params(labelsize=11, colors='#555555')

    # 总准确率注释
    acc = np.trace(cm) / cm.sum() * 100
    ax.text(0.98, -0.08, f'Overall Accuracy: {acc:.1f}%',
            transform=ax.transAxes, ha='right', va='top',
            fontsize=11, color='#3A86FF', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close()
    print(f"[4] Heatmap -> {output_path}")


# ── 主程序 ────────────────────────────────────────────────
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / 'visualizations'
    out_dir.mkdir(parents=True, exist_ok=True)

    data_train = np.load(base_dir / 'data_train.npz')
    data_test = np.load(base_dir / 'data_test.npz')
    X_all, y_all = consolidate(data_train, fault_labels)

    # 图 1
    plot_waveforms(X_all, y_all, out_dir / 'waveforms_by_class.png')

    # 图 2
    plot_class_bar(y_all, out_dir / 'class_distribution_seaborn.png')

    # 训练模型
    (X_train, feat_train, y_train,
     X_val, feat_val, y_val,
     X_test, feat_test) = data_provider(data_train, data_test, fault_labels)

    model = RandomForestClassifier(n_estimators=100, random_state=1)
    model.fit(feat_train, y_train)
    y_pred_val = model.predict(feat_val)
    y_pred_test = model.predict(feat_test)

    # 图 3
    plot_prediction_bar(y_pred_test, out_dir / 'prediction_distribution_seaborn.png')

    # 图 4
    plot_heatmap(y_val, y_pred_val, out_dir / 'confusion_heatmap_seaborn.png')

    print(f"\n[DONE] 4 images saved to {out_dir}")
