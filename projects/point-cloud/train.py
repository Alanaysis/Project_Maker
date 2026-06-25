"""
点云处理训练脚本

支持分类和分割任务的命令行训练。
"""

import argparse
import os
import torch

from src import (
    PointNetClassifier,
    PointNetSegmentor,
    PointCloudDataset,
    PointCloudTrainer,
    PointCloudVisualizer,
    generate_random_pointcloud,
    generate_segmentation_data,
    PointCloudAugmentation,
)


def parse_args():
    parser = argparse.ArgumentParser(description="PointNet 训练脚本")

    parser.add_argument("--task", type=str, default="classification",
                        choices=["classification", "segmentation"],
                        help="任务类型")
    parser.add_argument("--num_classes", type=int, default=10,
                        help="类别/部件数")
    parser.add_argument("--num_points", type=int, default=1024,
                        help="每个点云的点数")
    parser.add_argument("--num_train", type=int, default=1000,
                        help="训练样本数")
    parser.add_argument("--num_val", type=int, default=200,
                        help="验证样本数")
    parser.add_argument("--epochs", type=int, default=50,
                        help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="批次大小")
    parser.add_argument("--lr", type=float, default=0.001,
                        help="学习率")
    parser.add_argument("--use_tnet", action="store_true", default=True,
                        help="使用 TNet")
    parser.add_argument("--no_tnet", action="store_true",
                        help="不使用 TNet")
    parser.add_argument("--augment", action="store_true",
                        help="使用数据增强")
    parser.add_argument("--output_dir", type=str, default="outputs",
                        help="输出目录")
    parser.add_argument("--save_model", type=str, default=None,
                        help="模型保存路径")

    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print(f"PointNet {args.task.capitalize()} 训练")
    print("=" * 60)

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 设备
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n设备: {device}")

    # 生成数据
    print(f"\n生成数据 ({args.task})...")
    if args.task == "classification":
        train_points, train_labels = generate_random_pointcloud(
            num_points=args.num_points,
            num_classes=args.num_classes,
            num_samples=args.num_train,
        )
        val_points, val_labels = generate_random_pointcloud(
            num_points=args.num_points,
            num_classes=args.num_classes,
            num_samples=args.num_val,
        )
    else:
        train_points, train_labels = generate_segmentation_data(
            num_points=args.num_points,
            num_parts=args.num_classes,
            num_samples=args.num_train,
        )
        val_points, val_labels = generate_segmentation_data(
            num_points=args.num_points,
            num_parts=args.num_classes,
            num_samples=args.num_val,
        )

    # 数据增强
    transform = PointCloudAugmentation() if args.augment else None

    # 创建数据集
    train_dataset = PointCloudDataset(
        train_points, train_labels,
        task=args.task, transform=transform,
    )
    val_dataset = PointCloudDataset(
        val_points, val_labels, task=args.task,
    )

    print(f"  训练集: {len(train_dataset)} 样本")
    print(f"  验证集: {len(val_dataset)} 样本")

    # 创建训练器
    use_tnet = not args.no_tnet
    if args.task == "classification":
        trainer = PointCloudTrainer.create_classifier(
            num_classes=args.num_classes, use_tnet=use_tnet, device=device,
        )
    else:
        trainer = PointCloudTrainer.create_segmentor(
            num_classes=args.num_classes, use_tnet=use_tnet, device=device,
        )

    param_count = sum(p.numel() for p in trainer.model.parameters())
    print(f"  模型参数: {param_count:,}")

    # 训练
    print(f"\n开始训练 (epochs={args.epochs}, lr={args.lr})...")
    history = trainer.train(
        train_dataset, val_dataset,
        epochs=args.epochs, lr=args.lr, batch_size=args.batch_size,
    )

    # 可视化训练历史
    print("\n保存训练历史...")
    PointCloudVisualizer.plot_training_history(
        history,
        save_path=os.path.join(args.output_dir, "training_history.png"),
    )

    # 保存模型
    if args.save_model:
        trainer.save_model(args.save_model)
    else:
        model_path = os.path.join(args.output_dir, f"pointnet_{args.task}.pth")
        trainer.save_model(model_path)

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
