import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

fs = 5120


def consolidate(data, fault_labels):
    """Merge the samples from each fault type and build the label vector."""
    all_samples = []
    all_labels = []

    for fault_type, samples in data.items():
        if fault_type not in fault_labels:
            continue
        all_samples.append(samples)
        all_labels.extend([fault_labels[fault_type]] * samples.shape[0])

    all_samples = np.concatenate(all_samples)
    all_labels = np.array(all_labels)

    return all_samples, all_labels


class BasicFeatureExtractor:
    """
    Extract a small set of easy-to-understand signal summary features.

    The goal of this teaching version is to keep the classroom task focused on
    data loading, calling a baseline model, reading the report, and interpreting
    the output. More advanced feature sets can be added later as an optional
    extension.
    """

    def __init__(self, fs=5120):
        # 保留采样率参数，便于课堂说明类的属性；当前基础特征暂不使用它。
        self.fs = fs

    def feature(self, signal):
        signal = np.asarray(signal, dtype=float)
        mean_value = np.mean(signal, axis=-1)
        std_value = np.std(signal, axis=-1)
        max_value = np.max(signal, axis=-1)
        min_value = np.min(signal, axis=-1)
        rms_value = np.sqrt(np.mean(signal ** 2, axis=-1))
        peak_to_peak = max_value - min_value
        max_abs = np.max(np.abs(signal), axis=-1)
        abs_mean = np.mean(np.abs(signal), axis=-1)

        return np.stack(
            (
                mean_value,
                std_value,
                max_value,
                min_value,
                rms_value,
                peak_to_peak,
                max_abs,
                abs_mean,
            ),
            axis=-1,
        )


def data_provider(data_train, data_test, fault_labels):
    X, y = consolidate(data_train, fault_labels)
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=1,
        stratify=y,
    )
    X_test = data_test['samples']

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    feature_extractor = BasicFeatureExtractor(fs=fs)
    feature_train = feature_extractor.feature(X_train)
    feature_val = feature_extractor.feature(X_val)
    feature_test = feature_extractor.feature(X_test)

    scaler_feature = StandardScaler()
    feature_train = scaler_feature.fit_transform(feature_train)
    feature_val = scaler_feature.transform(feature_val)
    feature_test = scaler_feature.transform(feature_test)

    return X_train, feature_train, y_train, X_val, feature_val, y_val, X_test, feature_test
