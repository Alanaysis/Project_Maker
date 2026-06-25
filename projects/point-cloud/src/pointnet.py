"""
PointNet 模型实现

参考论文: PointNet: Deep Learning on Point Sets for 3D Classification and Segmentation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class TNet(nn.Module):
    """
    空间变换网络 (Spatial Transformer Network)

    学习输入点云的对齐变换矩阵，保证模型对点云刚性变换的不变性。
    """

    def __init__(self, k=3):
        super().__init__()
        self.k = k

        # 共享 MLP
        self.conv1 = nn.Conv1d(k, 64, 1)
        self.conv2 = nn.Conv1d(64, 128, 1)
        self.conv3 = nn.Conv1d(128, 1024, 1)

        # 全连接层
        self.fc1 = nn.Linear(1024, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, k * k)

        # BatchNorm
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)
        self.bn4 = nn.BatchNorm1d(512)
        self.bn5 = nn.BatchNorm1d(256)

    def forward(self, x):
        """
        Args:
            x: (batch_size, k, num_points) 输入点云

        Returns:
            matrix: (batch_size, k, k) 变换矩阵
        """
        batch_size = x.size(0)

        # 共享 MLP + BatchNorm + ReLU
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))

        # 全局最大池化
        x = torch.max(x, 2, keepdim=True)[0]
        x = x.view(-1, 1024)

        # 全连接层
        x = F.relu(self.bn4(self.fc1(x)))
        x = F.relu(self.bn5(self.fc2(x)))
        x = self.fc3(x)

        # 初始化为单位矩阵
        iden = torch.eye(self.k, device=x.device).view(1, self.k * self.k).repeat(batch_size, 1)
        x = x + iden
        x = x.view(-1, self.k, self.k)

        return x


class SharedMLP(nn.Module):
    """
    共享 MLP 层

    对点云的每个点应用相同的 MLP，用于提取逐点特征。
    """

    def __init__(self, in_channels, out_channels, use_bn=True):
        super().__init__()
        layers = [nn.Conv1d(in_channels, out_channels, 1)]
        if use_bn:
            layers.append(nn.BatchNorm1d(out_channels))
        layers.append(nn.ReLU(inplace=True))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class GlobalFeatureExtractor(nn.Module):
    """
    全局特征提取器

    通过共享 MLP 逐层提取特征，最后使用对称函数（最大池化）
    获取全局特征，保证对点云排列的不变性。
    """

    def __init__(self, use_tnet=True):
        super().__init__()
        self.use_tnet = use_tnet

        # 输入变换网络 (3x3)
        if use_tnet:
            self.input_transform = TNet(k=3)

        # 特征变换网络 (64x64)
        if use_tnet:
            self.feature_transform = TNet(k=64)

        # 共享 MLP 层
        self.mlp1 = SharedMLP(3, 64)
        self.mlp2 = SharedMLP(64, 64)
        self.mlp3 = SharedMLP(64, 128)
        self.mlp4 = SharedMLP(128, 1024)

    def forward(self, x):
        """
        Args:
            x: (batch_size, 3, num_points) 点云坐标

        Returns:
            global_feature: (batch_size, 1024) 全局特征
            local_feature: (batch_size, 64, num_points) 局部特征 (用于分割)
            trans_input: 输入变换矩阵
            trans_feat: 特征变换矩阵
        """
        batch_size, _, num_points = x.size()

        trans_input = None
        trans_feat = None

        # 输入变换
        if self.use_tnet:
            trans_input = self.input_transform(x)
            x = x.transpose(2, 1)
            x = torch.bmm(x, trans_input)
            x = x.transpose(2, 1)

        # 第一层 MLP
        x = self.mlp1(x)
        x = self.mlp2(x)

        # 保存局部特征
        local_feature = x

        # 特征变换
        if self.use_tnet:
            trans_feat = self.feature_transform(x)
            x = x.transpose(2, 1)
            x = torch.bmm(x, trans_feat)
            x = x.transpose(2, 1)

        # 更多 MLP 层
        x = self.mlp3(x)
        x = self.mlp4(x)

        # 对称函数: 全局最大池化
        global_feature = torch.max(x, 2, keepdim=False)[0]

        return global_feature, local_feature, trans_input, trans_feat


class PointNetClassifier(nn.Module):
    """
    PointNet 分类网络

    架构: 点云输入 → 特征提取 → 对称函数 → 分类
    """

    def __init__(self, num_classes=10, use_tnet=True):
        super().__init__()
        self.num_classes = num_classes

        # 全局特征提取器
        self.feature_extractor = GlobalFeatureExtractor(use_tnet=use_tnet)

        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        """
        Args:
            x: (batch_size, 3, num_points) 点云坐标

        Returns:
            logits: (batch_size, num_classes) 分类 logits
            trans_input: 输入变换矩阵
            trans_feat: 特征变换矩阵
        """
        global_feature, _, trans_input, trans_feat = self.feature_extractor(x)
        logits = self.classifier(global_feature)
        return logits, trans_input, trans_feat


class PointNetSegmentor(nn.Module):
    """
    PointNet 分割网络

    架构: 点云输入 → 特征提取 → 特征拼接 → 逐点分类
    """

    def __init__(self, num_classes=10, use_tnet=True):
        super().__init__()
        self.num_classes = num_classes

        # 全局特征提取器
        self.feature_extractor = GlobalFeatureExtractor(use_tnet=use_tnet)

        # 逐点分割头
        self.segmentation_head = nn.Sequential(
            SharedMLP(1024 + 64, 512),
            SharedMLP(512, 256),
            SharedMLP(256, 128),
            nn.Conv1d(128, num_classes, 1),
        )

    def forward(self, x):
        """
        Args:
            x: (batch_size, 3, num_points) 点云坐标

        Returns:
            logits: (batch_size, num_points, num_classes) 逐点分割 logits
            trans_input: 输入变换矩阵
            trans_feat: 特征变换矩阵
        """
        global_feature, local_feature, trans_input, trans_feat = self.feature_extractor(x)

        # 扩展全局特征并与局部特征拼接
        batch_size, _, num_points = x.size()
        global_feature_expanded = global_feature.unsqueeze(2).expand(-1, -1, num_points)

        # 拼接全局和局部特征
        combined = torch.cat([global_feature_expanded, local_feature], dim=1)

        # 逐点分类
        logits = self.segmentation_head(combined)
        logits = logits.transpose(2, 1)  # (batch_size, num_points, num_classes)

        return logits, trans_input, trans_feat


def pointnet_loss(logits, targets, trans_feat=None, alpha=0.001):
    """
    PointNet 损失函数

    包含分类/分割损失和正则化损失（特征变换矩阵应接近正交矩阵）

    Args:
        logits: 模型输出
        targets: 标签
        trans_feat: 特征变换矩阵
        alpha: 正则化系数

    Returns:
        loss: 总损失
    """
    # 主损失
    loss = F.cross_entropy(logits, targets)

    # 正则化损失 (特征变换矩阵应接近正交)
    if trans_feat is not None:
        batch_size = trans_feat.size(0)
        I = torch.eye(64, device=trans_feat.device).unsqueeze(0).repeat(batch_size, 1, 1)
        AAt = torch.bmm(trans_feat, trans_feat.transpose(2, 1))
        reg_loss = torch.mean(torch.norm(AAt - I, dim=(1, 2)))
        loss = loss + alpha * reg_loss

    return loss
