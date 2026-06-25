"""
评估器模块
==========

NER 评估指标:
1. 准确率 (Accuracy): token 级别的预测正确比例
2. 精确率 (Precision): 预测为实体的结果中，正确比例
3. 召回率 (Recall): 真实实体中，被正确识别的比例
4. F1 分数: 精确率和召回率的调和平均

实体级别的评估:
- 只有当实体的边界和类型都正确时，才算正确
- B-PER I-PER 对应 B-PER I-PER 才算正确
- B-PER I-PER 对应 B-PER O 是错误的 (边界错误)
"""

from typing import List, Dict, Tuple
from collections import defaultdict


class Evaluator:
    """
    NER 评估器

    使用实体级别评估:
    - 将 BIO 标签序列转换为实体
    - 计算每个实体类型的精确率、召回率和 F1
    - 计算 token 级别的准确率
    """

    def __init__(self, tag_vocab):
        """
        参数:
            tag_vocab: 标签表，用于将索引转换为标签
        """
        self.tag_vocab = tag_vocab

    def evaluate(self, true_tags: List[List[str]],
                 pred_tags: List[List[str]]) -> Dict:
        """
        评估 NER 结果

        参数:
            true_tags: 真实标签序列列表
            pred_tags: 预测标签序列列表

        返回:
            metrics: 包含整体和各实体类型的 Accuracy, P, R, F1
        """
        # 计算 token 级别准确率
        accuracy = self._compute_accuracy(true_tags, pred_tags)

        # 提取实体
        true_entities = self._extract_entities(true_tags)
        pred_entities = self._extract_entities(pred_tags)

        # 计算各类型的指标
        entity_types = set()
        for entities in true_entities:
            for entity in entities:
                entity_types.add(entity[0])
        for entities in pred_entities:
            for entity in entities:
                entity_types.add(entity[0])

        results = {}
        total_correct = 0
        total_pred = 0
        total_true = 0

        for entity_type in sorted(entity_types):
            correct, pred_count, true_count = self._count_matches(
                true_entities, pred_entities, entity_type
            )

            precision = correct / pred_count if pred_count > 0 else 0.0
            recall = correct / true_count if true_count > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)
                  if (precision + recall) > 0 else 0.0)

            results[entity_type] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "correct": correct,
                "predicted": pred_count,
                "actual": true_count
            }

            total_correct += correct
            total_pred += pred_count
            total_true += true_count

        # 整体指标 (micro-average)
        total_precision = total_correct / total_pred if total_pred > 0 else 0.0
        total_recall = total_correct / total_true if total_true > 0 else 0.0
        total_f1 = (2 * total_precision * total_recall /
                    (total_precision + total_recall)
                    if (total_precision + total_recall) > 0 else 0.0)

        results["overall"] = {
            "accuracy": accuracy,
            "precision": total_precision,
            "recall": total_recall,
            "f1": total_f1,
            "correct": total_correct,
            "predicted": total_pred,
            "actual": total_true
        }

        return results

    def _compute_accuracy(self, true_tags: List[List[str]],
                          pred_tags: List[List[str]]) -> float:
        """
        计算 token 级别的准确率

        准确率 = 正确预测的 token 数 / 总 token 数

        参数:
            true_tags: 真实标签序列列表
            pred_tags: 预测标签序列列表

        返回:
            accuracy: 准确率
        """
        total = 0
        correct = 0

        for true_seq, pred_seq in zip(true_tags, pred_tags):
            for true_tag, pred_tag in zip(true_seq, pred_seq):
                total += 1
                if true_tag == pred_tag:
                    correct += 1

        return correct / total if total > 0 else 0.0

    def evaluate_from_indices(self, true_indices: List[List[int]],
                              pred_indices: List[List[int]],
                              masks: List[List[int]]) -> Dict:
        """
        从索引评估

        参数:
            true_indices: 真实标签索引序列列表
            pred_indices: 预测标签索引序列列表
            masks: 掩码列表

        返回:
            metrics: 评估指标
        """
        true_tags = []
        pred_tags = []

        for true_seq, pred_seq, mask in zip(true_indices, pred_indices, masks):
            seq_len = int(sum(mask))
            true_tags.append([
                self.tag_vocab.get_tag(idx) for idx in true_seq[:seq_len]
            ])
            pred_tags.append([
                self.tag_vocab.get_tag(idx) for idx in pred_seq[:seq_len]
            ])

        return self.evaluate(true_tags, pred_tags)

    def _extract_entities(self, tag_sequences: List[List[str]]) -> List[List[Tuple]]:
        """
        从 BIO 标签序列提取实体

        参数:
            tag_sequences: 标签序列列表

        返回:
            entities: 实体列表，每个实体是 (类型, 开始位置, 结束位置)
        """
        all_entities = []

        for tag_seq in tag_sequences:
            entities = []
            current_entity = None
            current_start = None

            for i, tag in enumerate(tag_seq):
                if tag.startswith("B-"):
                    # 保存之前的实体
                    if current_entity is not None:
                        entities.append((current_entity, current_start, i - 1))
                    # 开始新实体
                    current_entity = tag[2:]
                    current_start = i

                elif tag.startswith("I-"):
                    entity_type = tag[2:]
                    if current_entity == entity_type:
                        # 继续当前实体
                        continue
                    else:
                        # 类型不匹配，结束之前的实体
                        if current_entity is not None:
                            entities.append(
                                (current_entity, current_start, i - 1)
                            )
                        current_entity = None
                        current_start = None

                else:  # O 标签
                    if current_entity is not None:
                        entities.append(
                            (current_entity, current_start, i - 1)
                        )
                        current_entity = None
                        current_start = None

            # 最后一个实体
            if current_entity is not None:
                entities.append(
                    (current_entity, current_start, len(tag_seq) - 1)
                )

            all_entities.append(entities)

        return all_entities

    def _count_matches(self, true_entities: List[List[Tuple]],
                       pred_entities: List[List[Tuple]],
                       entity_type: str) -> Tuple[int, int, int]:
        """
        计算匹配数量

        参数:
            true_entities: 真实实体列表
            pred_entities: 预测实体列表
            entity_type: 实体类型

        返回:
            (正确数量, 预测数量, 真实数量)
        """
        correct = 0
        pred_count = 0
        true_count = 0

        for true_ents, pred_ents in zip(true_entities, pred_entities):
            # 转换为集合以便比较
            true_set = {(t, s, e) for t, s, e in true_ents if t == entity_type}
            pred_set = {(t, s, e) for t, s, e in pred_ents if t == entity_type}

            true_count += len(true_set)
            pred_count += len(pred_set)
            correct += len(true_set & pred_set)

        return correct, pred_count, true_count

    def print_results(self, results: Dict):
        """打印评估结果"""
        print("\n" + "=" * 60)
        print("NER Evaluation Results")
        print("=" * 60)
        print(f"{'Type':<10} {'Prec':>8} {'Recall':>8} {'F1':>8} "
              f"{'Correct':>8} {'Pred':>8} {'True':>8}")
        print("-" * 60)

        for entity_type in sorted(results.keys()):
            if entity_type == "overall":
                continue
            m = results[entity_type]
            print(f"{entity_type:<10} {m['precision']:>8.4f} "
                  f"{m['recall']:>8.4f} {m['f1']:>8.4f} "
                  f"{m['correct']:>8d} {m['predicted']:>8d} "
                  f"{m['actual']:>8d}")

        print("-" * 60)
        m = results["overall"]
        print(f"{'Overall':<10} {m['precision']:>8.4f} "
              f"{m['recall']:>8.4f} {m['f1']:>8.4f} "
              f"{m['correct']:>8d} {m['predicted']:>8d} "
              f"{m['actual']:>8d}")
        print("=" * 60)
