"""
鸢尾花分类示例

使用决策树对鸢尾花数据集进行分类，并比较不同决策树算法的性能。

鸢尾花数据集包含 150 个样本，3 个类别：
- 山鸢尾 (Setosa)
- 变色鸢尾 (Versicolor)
- 维吉尼亚鸢尾 (Virginica)

每个样本有 4 个特征：
- 花萼长度 (sepal length)
- 花萼宽度 (sepal width)
- 花瓣长度 (petal length)
- 花瓣宽度 (petal width)
"""

import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.id3 import ID3DecisionTree
from src.c45 import C45DecisionTree
from src.cart_classifier import CARTClassifier
from src.pruning import PrePruningTree, PostPruningTree
from src.utils import train_test_split, accuracy_score
from src.metrics import precision_score, recall_score, f1_score


def load_iris_data():
    """
    加载鸢尾花数据集

    返回:
    X: 特征矩阵 (150, 4)
    y: 标签向量 (150,)
    feature_names: 特征名称
    class_names: 类别名称
    """
    # 简化版鸢尾花数据集
    # 实际应用中应从 sklearn.datasets 导入
    np.random.seed(42)

    # 生成模拟数据
    n_samples_per_class = 50
    n_classes = 3

    # 类别 0: 山鸢尾
    X0 = np.random.randn(n_samples_per_class, 4) * 0.5 + [5.0, 3.4, 1.5, 0.2]

    # 类别 1: 变色鸢尾
    X1 = np.random.randn(n_samples_per_class, 4) * 0.5 + [5.9, 2.8, 4.3, 1.3]

    # 类别 2: 维吉尼亚鸢尾
    X2 = np.random.randn(n_samples_per_class, 4) * 0.5 + [6.6, 3.0, 5.5, 2.0]

    X = np.vstack([X0, X1, X2])
    y = np.array([0] * n_samples_per_class + [1] * n_samples_per_class + [2] * n_samples_per_class)

    feature_names = ['花萼长度', '花萼宽度', '花瓣长度', '花瓣宽度']
    class_names = ['山鸢尾', '变色鸢尾', '维吉尼亚鸢尾']

    return X, y, feature_names, class_names


def evaluate_model(model, X_test, y_test, model_name):
    """
    评估模型性能

    参数:
    ----------
    model : 决策树模型
        训练好的模型
    X_test : numpy.ndarray
        测试特征
    y_test : numpy.ndarray
        测试标签
    model_name : str
        模型名称
    """
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='macro')
    rec = recall_score(y_test, y_pred, average='macro')
    f1 = f1_score(y_test, y_pred, average='macro')

    print(f"\n{model_name} 评估结果:")
    print(f"  准确率 (Accuracy):  {acc:.4f}")
    print(f"  精确率 (Precision): {prec:.4f}")
    print(f"  召回率 (Recall):    {rec:.4f}")
    print(f"  F1 分数 (F1-Score): {f1:.4f}")

    return {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}


def main():
    """主函数"""
    print("=" * 60)
    print("鸢尾花分类示例 - 决策树算法比较")
    print("=" * 60)

    # 1. 加载数据
    print("\n1. 加载鸢尾花数据集...")
    X, y, feature_names, class_names = load_iris_data()
    print(f"   数据集大小: {X.shape[0]} 个样本, {X.shape[1]} 个特征")
    print(f"   类别: {class_names}")

    # 2. 划分数据集
    print("\n2. 划分数据集 (80% 训练, 20% 测试)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"   训练集大小: {X_train.shape[0]}")
    print(f"   测试集大小: {X_test.shape[0]}")

    # 3. 训练不同决策树模型
    print("\n3. 训练决策树模型...")

    # ID3 决策树
    print("\n   训练 ID3 决策树...")
    id3_tree = ID3DecisionTree(max_depth=5)
    id3_tree.fit(X_train, y_train)

    # C4.5 决策树
    print("   训练 C4.5 决策树...")
    c45_tree = C45DecisionTree(max_depth=5)
    c45_tree.fit(X_train, y_train)

    # CART 分类树
    print("   训练 CART 分类树...")
    cart_tree = CARTClassifier(max_depth=5)
    cart_tree.fit(X_train, y_train)

    # 预剪枝决策树
    print("   训练预剪枝决策树...")
    pre_pruning_tree = PrePruningTree(
        max_depth=5,
        min_samples_split=5,
        min_samples_leaf=2,
        min_impurity_decrease=0.01
    )
    pre_pruning_tree.fit(X_train, y_train)

    # 后剪枝决策树
    print("   训练后剪枝决策树...")
    post_pruning_tree = PostPruningTree(max_depth=10, ccp_alpha=0.05)
    post_pruning_tree.fit(X_train, y_train)

    # 4. 评估模型
    print("\n4. 评估模型性能...")
    results = {}
    results['ID3'] = evaluate_model(id3_tree, X_test, y_test, "ID3 决策树")
    results['C4.5'] = evaluate_model(c45_tree, X_test, y_test, "C4.5 决策树")
    results['CART'] = evaluate_model(cart_tree, X_test, y_test, "CART 分类树")
    results['预剪枝'] = evaluate_model(pre_pruning_tree, X_test, y_test, "预剪枝决策树")
    results['后剪枝'] = evaluate_model(post_pruning_tree, X_test, y_test, "后剪枝决策树")

    # 5. 比较结果
    print("\n" + "=" * 60)
    print("模型比较:")
    print("=" * 60)
    print(f"{'模型':<12} {'准确率':<10} {'精确率':<10} {'召回率':<10} {'F1':<10}")
    print("-" * 60)
    for name, metrics in results.items():
        print(f"{name:<12} {metrics['accuracy']:<10.4f} {metrics['precision']:<10.4f} "
              f"{metrics['recall']:<10.4f} {metrics['f1']:<10.4f}")

    # 6. 特征重要性分析
    print("\n5. 特征重要性分析:")
    print("-" * 40)
    for name, model in [('ID3', id3_tree), ('C4.5', c45_tree), ('CART', cart_tree)]:
        if hasattr(model, 'feature_importances_'):
            print(f"\n{name}:")
            for i, (fname, importance) in enumerate(zip(feature_names, model.feature_importances_)):
                print(f"  {fname}: {importance:.4f}")

    # 7. 打印决策树结构（CART）
    print("\n6. CART 决策树结构:")
    print("-" * 40)
    cart_tree.print_tree(feature_names=feature_names)

    return results


if __name__ == "__main__":
    main()
