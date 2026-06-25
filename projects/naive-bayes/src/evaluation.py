"""
朴素贝叶斯分类器评估模块

提供以下评估指标:
- 准确率 (Accuracy)
- 精确率 (Precision)
- 召回率 (Recall)
- F1 分数
- 混淆矩阵 (Confusion Matrix)
"""

from typing import Any


def accuracy(y_true: list[Any], y_pred: list[Any]) -> float:
    """
    计算准确率

    准确率 = 正确预测的样本数 / 总样本数

    Args:
        y_true: 真实标签
        y_pred: 预测标签

    Returns:
        准确率 (0-1)
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true 和 y_pred 长度必须相同")

    if len(y_true) == 0:
        raise ValueError("标签列表不能为空")

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)


def confusion_matrix(
    y_true: list[Any], y_pred: list[Any], labels: list[Any] | None = None
) -> dict[tuple[Any, Any], int]:
    """
    计算混淆矩阵

    混淆矩阵[i][j] 表示真实类别为i但被预测为j的样本数。

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        labels: 类别列表，如果为None则自动推断

    Returns:
        混淆矩阵字典，键为 (真实类别, 预测类别)，值为计数
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true 和 y_pred 长度必须相同")

    if len(y_true) == 0:
        raise ValueError("标签列表不能为空")

    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    # 初始化混淆矩阵
    matrix: dict[tuple[Any, Any], int] = {}
    for true_label in labels:
        for pred_label in labels:
            matrix[(true_label, pred_label)] = 0

    # 填充混淆矩阵
    for t, p in zip(y_true, y_pred):
        if (t, p) in matrix:
            matrix[(t, p)] += 1

    return matrix


def confusion_matrix_to_table(
    matrix: dict[tuple[Any, Any], int], labels: list[Any]
) -> list[list[int]]:
    """
    将混淆矩阵字典转换为二维列表格式

    Args:
        matrix: 混淆矩阵字典
        labels: 类别列表

    Returns:
        二维列表，行表示真实类别，列表示预测类别
    """
    n = len(labels)
    table = [[0] * n for _ in range(n)]

    for i, true_label in enumerate(labels):
        for j, pred_label in enumerate(labels):
            table[i][j] = matrix.get((true_label, pred_label), 0)

    return table


def precision(
    y_true: list[Any],
    y_pred: list[Any],
    labels: list[Any] | None = None,
    average: str = "macro",
) -> float | dict[Any, float]:
    """
    计算精确率

    精确率 = TP / (TP + FP)
    即: 预测为正类的样本中，实际为正类的比例

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        labels: 类别列表
        average: 平均方式
            - 'macro': 宏平均，各类别精确率的算术平均
            - 'micro': 微平均，全局TP/FP计算
            - 'weighted': 加权平均，按类别样本数加权
            - None: 返回各类别的精确率

    Returns:
        精确率或各类别精确率字典
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true 和 y_pred 长度必须相同")

    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    matrix = confusion_matrix(y_true, y_pred, labels)

    if average == "micro":
        # 微平均: 全局TP / (全局TP + 全局FP)
        total_tp = sum(matrix.get((c, c), 0) for c in labels)
        total_pred = sum(
            matrix.get((t, c), 0) for t in labels for c in labels
        )
        return total_tp / total_pred if total_pred > 0 else 0.0

    # 计算每个类别的精确率
    precisions: dict[Any, float] = {}
    for label in labels:
        tp = matrix.get((label, label), 0)
        fp = sum(matrix.get((t, label), 0) for t in labels) - tp
        precisions[label] = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    if average is None:
        return precisions

    if average == "macro":
        return sum(precisions.values()) / len(precisions)

    if average == "weighted":
        class_counts = {}
        for t in y_true:
            class_counts[t] = class_counts.get(t, 0) + 1
        total = len(y_true)
        return sum(
            precisions[c] * class_counts.get(c, 0) / total for c in labels
        )

    raise ValueError(f"不支持的 average 类型: {average}")


def recall(
    y_true: list[Any],
    y_pred: list[Any],
    labels: list[Any] | None = None,
    average: str = "macro",
) -> float | dict[Any, float]:
    """
    计算召回率

    召回率 = TP / (TP + FN)
    即: 实际为正类的样本中，被正确预测的比例

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        labels: 类别列表
        average: 平均方式
            - 'macro': 宏平均
            - 'micro': 微平均
            - 'weighted': 加权平均
            - None: 返回各类别的召回率

    Returns:
        召回率或各类别召回率字典
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true 和 y_pred 长度必须相同")

    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    matrix = confusion_matrix(y_true, y_pred, labels)

    if average == "micro":
        # 微平均: 全局TP / (全局TP + 全局FN)
        total_tp = sum(matrix.get((c, c), 0) for c in labels)
        total_true = len(y_true)
        return total_tp / total_true if total_true > 0 else 0.0

    # 计算每个类别的召回率
    recalls: dict[Any, float] = {}
    for label in labels:
        tp = matrix.get((label, label), 0)
        fn = sum(matrix.get((label, p), 0) for p in labels) - tp
        recalls[label] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    if average is None:
        return recalls

    if average == "macro":
        return sum(recalls.values()) / len(recalls)

    if average == "weighted":
        class_counts = {}
        for t in y_true:
            class_counts[t] = class_counts.get(t, 0) + 1
        total = len(y_true)
        return sum(
            recalls[c] * class_counts.get(c, 0) / total for c in labels
        )

    raise ValueError(f"不支持的 average 类型: {average}")


def f1_score(
    y_true: list[Any],
    y_pred: list[Any],
    labels: list[Any] | None = None,
    average: str = "macro",
) -> float | dict[Any, float]:
    """
    计算F1分数

    F1 = 2 * precision * recall / (precision + recall)

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        labels: 类别列表
        average: 平均方式

    Returns:
        F1分数或各类别F1分数字典
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true 和 y_pred 长度必须相同")

    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    if average is None:
        p = precision(y_true, y_pred, labels, average=None)
        r = recall(y_true, y_pred, labels, average=None)
        assert isinstance(p, dict) and isinstance(r, dict)
        f1s: dict[Any, float] = {}
        for label in labels:
            if p[label] + r[label] > 0:
                f1s[label] = 2 * p[label] * r[label] / (p[label] + r[label])
            else:
                f1s[label] = 0.0
        return f1s

    p = precision(y_true, y_pred, labels, average=average)
    r = recall(y_true, y_pred, labels, average=average)
    assert isinstance(p, float) and isinstance(r, float)

    if p + r > 0:
        return 2 * p * r / (p + r)
    return 0.0


def classification_report(
    y_true: list[Any],
    y_pred: list[Any],
    labels: list[Any] | None = None,
) -> str:
    """
    生成分类报告

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        labels: 类别列表

    Returns:
        格式化的分类报告字符串
    """
    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    p = precision(y_true, y_pred, labels, average=None)
    r = recall(y_true, y_pred, labels, average=None)
    f1 = f1_score(y_true, y_pred, labels, average=None)
    assert isinstance(p, dict) and isinstance(r, dict) and isinstance(f1, dict)

    # 统计每个类别的样本数
    class_counts: dict[Any, int] = {}
    for t in y_true:
        class_counts[t] = class_counts.get(t, 0) + 1

    # 生成报告
    lines = []
    header = f"{'':>12} {'precision':>10} {'recall':>10} {'f1-score':>10} {'support':>10}"
    lines.append(header)
    lines.append("-" * len(header))

    total_support = 0
    weighted_p = 0.0
    weighted_r = 0.0
    weighted_f1 = 0.0

    for label in labels:
        support = class_counts.get(label, 0)
        total_support += support
        weighted_p += p[label] * support
        weighted_r += r[label] * support
        weighted_f1 += f1[label] * support

        line = f"{str(label):>12} {p[label]:>10.4f} {r[label]:>10.4f} {f1[label]:>10.4f} {support:>10}"
        lines.append(line)

    lines.append("-" * len(header))

    # 宏平均
    macro_p = sum(p.values()) / len(p)
    macro_r = sum(r.values()) / len(r)
    macro_f1 = sum(f1.values()) / len(f1)
    lines.append(
        f"{'macro avg':>12} {macro_p:>10.4f} {macro_r:>10.4f} {macro_f1:>10.4f} {total_support:>10}"
    )

    # 加权平均
    if total_support > 0:
        lines.append(
            f"{'weighted avg':>12} {weighted_p / total_support:>10.4f} {weighted_r / total_support:>10.4f} {weighted_f1 / total_support:>10.4f} {total_support:>10}"
        )

    return "\n".join(lines)


def print_confusion_matrix(
    y_true: list[Any],
    y_pred: list[Any],
    labels: list[Any] | None = None,
) -> str:
    """
    生成可打印的混淆矩阵

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        labels: 类别列表

    Returns:
        格式化的混淆矩阵字符串
    """
    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    matrix = confusion_matrix(y_true, y_pred, labels)
    table = confusion_matrix_to_table(matrix, labels)

    # 计算列宽
    max_label_len = max(len(str(l)) for l in labels)
    max_val_len = max(
        len(str(table[i][j])) for i in range(len(labels)) for j in range(len(labels))
    )
    col_width = max(max_label_len, max_val_len) + 2

    lines = []

    # 表头
    header = " " * (col_width + 2) + "预测标签"
    lines.append(header)
    header = " " * col_width + "".join(str(l).center(col_width) for l in labels)
    lines.append(header)
    lines.append("-" * (col_width * (len(labels) + 1)))

    # 表体
    for i, label in enumerate(labels):
        row = f"{str(label).center(col_width)}|"
        row += "".join(str(table[i][j]).center(col_width) for j in range(len(labels)))
        lines.append(row)

    # 添加说明
    lines.append("")
    lines.append("行: 真实标签, 列: 预测标签")

    return "\n".join(lines)


def evaluate_model(
    y_true: list[Any],
    y_pred: list[Any],
    labels: list[Any] | None = None,
) -> dict[str, Any]:
    """
    综合评估模型

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        labels: 类别列表

    Returns:
        包含所有评估指标的字典
    """
    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))

    return {
        "accuracy": accuracy(y_true, y_pred),
        "precision_macro": precision(y_true, y_pred, labels, average="macro"),
        "precision_weighted": precision(
            y_true, y_pred, labels, average="weighted"
        ),
        "recall_macro": recall(y_true, y_pred, labels, average="macro"),
        "recall_weighted": recall(y_true, y_pred, labels, average="weighted"),
        "f1_macro": f1_score(y_true, y_pred, labels, average="macro"),
        "f1_weighted": f1_score(y_true, y_pred, labels, average="weighted"),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels),
        "report": classification_report(y_true, y_pred, labels),
    }
