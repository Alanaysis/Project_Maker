"""
VQA 推理示例

演示如何使用训练好的 VQA 模型进行推理。
"""

import torch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import VQAModel, Vocab
from src.dataset import create_sample_data


def create_sample_model():
    """创建一个示例模型用于演示"""
    # 创建词汇表
    questions = [
        "what color is the cat",
        "is there a dog",
        "how many birds are there",
        "what is this",
    ]
    vocab = Vocab()
    for q in questions:
        for word in q.lower().split():
            vocab.add_word(word)

    # 创建模型
    model = VQAModel(
        vocab_size=len(vocab),
        num_answers=10,
        image_feature_dim=256,
        text_feature_dim=256,
        fusion_dim=512,
        hidden_dim=256,
    )

    return model, vocab


def main():
    """推理示例"""
    print("=" * 60)
    print("VQA 推理示例")
    print("=" * 60)

    # 创建模型和词汇表
    print("\n1. 加载模型和词汇表...")
    model, vocab = create_sample_model()
    model.eval()

    model_info = model.get_model_info()
    print(f"   模型参数量: {model_info['total_params']:,}")

    # 模拟图像特征（实际应用中使用真实图像）
    print("\n2. 准备输入数据...")

    # 示例问题
    questions = [
        "what color is the cat",
        "is there a dog",
        "what is this",
    ]

    print("   示例问题:")
    for q in questions:
        print(f"   - {q}")

    # 编码问题
    print("\n3. 编码问题...")
    question_ids = []
    for q in questions:
        ids = vocab.encode(q, max_len=10)
        question_ids.append(ids)
        print(f"   '{q}' -> {ids[:5]}...")

    question_tensor = torch.tensor(question_ids, dtype=torch.long)

    # 模拟图像特征
    print("\n4. 准备图像特征...")
    image_features = torch.randn(len(questions), 256)
    print(f"   图像特征形状: {image_features.shape}")

    # 进行预测
    print("\n5. 进行预测...")
    with torch.no_grad():
        predictions, confidence = model.predict(
            image_features=image_features,
            question_ids=question_tensor,
        )

    # 显示结果
    print("\n6. 预测结果:")
    print("-" * 60)

    # 答案标签（示例）
    answer_labels = [
        "red", "yes", "cat", "dog", "blue",
        "no", "two", "bird", "car", "tree",
    ]

    for i, q in enumerate(questions):
        pred_idx = predictions[i].item()
        conf = confidence[i].item()
        pred_answer = answer_labels[pred_idx] if pred_idx < len(answer_labels) else f"answer_{pred_idx}"

        print(f"\n   问题: {q}")
        print(f"   预测答案: {pred_answer}")
        print(f"   置信度: {conf:.2%}")

    # Top-K 预测
    print("\n7. Top-3 预测:")
    print("-" * 60)

    with torch.no_grad():
        top_k_preds, top_k_conf = model.predictor.predict_top_k(
            model.fusion(
                image_features,
                model.text_encoder(question_tensor),
            ),
            k=3,
        )

    for i, q in enumerate(questions):
        print(f"\n   问题: {q}")
        for k in range(3):
            pred_idx = top_k_preds[i][k].item()
            conf = top_k_conf[i][k].item()
            pred_answer = answer_labels[pred_idx] if pred_idx < len(answer_labels) else f"answer_{pred_idx}"
            print(f"   Top-{k+1}: {pred_answer} ({conf:.2%})")

    print("\n" + "=" * 60)
    print("推理完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
