"""
图像数据集模型（从 Prisma Schema 转换）
注意：ImageDataset模型定义在images/models.py中，这里重新导出以避免循环导入
"""
# 从images应用导入ImageDataset模型
from images.models import ImageDataset

__all__ = ['ImageDataset']
