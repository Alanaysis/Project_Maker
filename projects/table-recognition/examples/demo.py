"""
表格识别演示脚本

展示如何使用表格识别系统。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import cv2
import numpy as np
from src.pipeline import TableRecognitionPipeline, ResultExporter
from src.utils import create_sample_table_image, create_sample_image_with_tables


def demo_basic_usage():
    """基础使用演示"""
    print("=" * 60)
    print("表格识别系统 - 基础使用演示")
    print("=" * 60)

    # 1. 创建示例表格图像
    print("\n[1] 创建示例表格图像...")
    table_image = create_sample_table_image(rows=3, cols=4)
    output_path = project_root / "examples" / "sample_table.png"
    cv2.imwrite(str(output_path), table_image)
    print(f"    保存到: {output_path}")

    # 2. 初始化处理管道
    print("\n[2] 初始化处理管道...")
    pipeline = TableRecognitionPipeline(
        detector_type="simple",
        recognizer_type="morphological",
        use_ocr=False,
    )
    print("    管道初始化完成")

    # 3. 处理图像
    print("\n[3] 处理图像...")
    result = pipeline.process_image(table_image)

    # 4. 显示结果
    print("\n[4] 处理结果:")
    print(f"    图像尺寸: {result['image_size']}")
    print(f"    检测到表格数量: {len(result['tables'])}")
    print(f"    处理时间: {result['processing_time']:.2f} 秒")

    for table in result["tables"]:
        print(f"\n    表格 {table['index'] + 1}:")
        print(f"      位置: {table['bbox']}")
        print(f"      行数: {table['rows']}")
        print(f"      列数: {table['columns']}")
        print(f"      单元格数量: {len(table['cells'])}")

        if table['data']:
            print(f"      数据:")
            for i, row in enumerate(table['data']):
                print(f"        行 {i}: {row}")

    return result


def demo_visualization():
    """可视化演示"""
    print("\n" + "=" * 60)
    print("表格识别系统 - 可视化演示")
    print("=" * 60)

    # 创建示例图像
    print("\n[1] 创建示例图像...")
    image = create_sample_image_with_tables(num_tables=2)
    output_path = project_root / "examples" / "sample_tables.png"
    cv2.imwrite(str(output_path), image)
    print(f"    保存到: {output_path}")

    # 初始化管道
    print("\n[2] 初始化处理管道...")
    pipeline = TableRecognitionPipeline(
        detector_type="simple",
        recognizer_type="morphological",
    )

    # 处理图像
    print("\n[3] 处理图像...")
    result = pipeline.process_image(image)

    # 可视化结果
    print("\n[4] 生成可视化结果...")
    vis_image = pipeline.visualize_result(image, result, show_cells=True)

    vis_path = project_root / "examples" / "visualization_result.png"
    cv2.imwrite(str(vis_path), vis_image)
    print(f"    可视化结果保存到: {vis_path}")

    return vis_image


def demo_export_formats():
    """导出格式演示"""
    print("\n" + "=" * 60)
    print("表格识别系统 - 导出格式演示")
    print("=" * 60)

    # 创建示例表格
    print("\n[1] 创建示例表格...")
    table_image = create_sample_table_image(rows=3, cols=3)

    # 处理图像
    print("\n[2] 处理图像...")
    pipeline = TableRecognitionPipeline(
        detector_type="simple",
        recognizer_type="morphological",
    )
    result = pipeline.process_image(table_image)

    # 导出为不同格式
    print("\n[3] 导出结果...")

    # JSON 格式
    json_path = project_root / "examples" / "result.json"
    ResultExporter.to_json(result, json_path)
    print(f"    JSON: {json_path}")

    # CSV 格式
    csv_path = project_root / "examples" / "result.csv"
    ResultExporter.to_csv(result, csv_path)
    print(f"    CSV: {csv_path}")

    # HTML 格式
    html_path = project_root / "examples" / "result.html"
    ResultExporter.to_html(result, html_path)
    print(f"    HTML: {html_path}")

    return result


def demo_advanced_usage():
    """高级使用演示"""
    print("\n" + "=" * 60)
    print("表格识别系统 - 高级使用演示")
    print("=" * 60)

    from src.detector import SimpleTableDetector
    from src.structure import StructureRecognizer
    from src.extractor import CellExtractor, CellMerger

    # 创建复杂表格图像
    print("\n[1] 创建复杂表格图像...")
    image = np.ones((500, 700, 3), dtype=np.uint8) * 255

    # 绘制表格
    cv2.rectangle(image, (50, 50), (650, 450), (0, 0, 0), 2)

    # 绘制水平线
    for y in [150, 250, 350]:
        cv2.line(image, (50, y), (650, y), (0, 0, 0), 1)

    # 绘制垂直线
    for x in [200, 350, 500]:
        cv2.line(image, (x, 50), (x, 450), (0, 0, 0), 1)

    # 保存图像
    output_path = project_root / "examples" / "complex_table.png"
    cv2.imwrite(str(output_path), image)
    print(f"    保存到: {output_path}")

    # 分步骤处理
    print("\n[2] 分步骤处理...")

    # 步骤 1: 表格检测
    print("\n    步骤 1: 表格检测")
    detector = SimpleTableDetector()
    detections = detector.detect(image)
    print(f"    检测到 {len(detections)} 个表格")

    # 步骤 2: 结构识别
    print("\n    步骤 2: 结构识别")
    recognizer = StructureRecognizer()
    for i, detection in enumerate(detections):
        bbox = detection["bbox"]
        x1, y1, x2, y2 = bbox
        table_image = image[y1:y2, x1:x2]

        structure = recognizer.recognize(table_image)
        print(f"    表格 {i + 1}: {structure['rows']} 行 x {structure['columns']} 列")

        # 步骤 3: 单元格提取
        print("\n    步骤 3: 单元格提取")
        extractor = CellExtractor()
        cells = extractor.extract(table_image, structure)
        print(f"    提取了 {len(cells)} 个单元格")

        # 步骤 4: 单元格合并
        print("\n    步骤 4: 单元格合并")
        merger = CellMerger()
        merged_cells = merger.merge_cells(cells)
        print(f"    合并后 {len(merged_cells)} 个单元格")

    return detections, structure, cells


def demo_batch_processing():
    """批量处理演示"""
    print("\n" + "=" * 60)
    print("表格识别系统 - 批量处理演示")
    print("=" * 60)

    # 创建多个表格图像
    print("\n[1] 创建多个表格图像...")
    images = []
    for i in range(3):
        rows = np.random.randint(2, 5)
        cols = np.random.randint(2, 4)
        image = create_sample_table_image(rows=rows, cols=cols)
        images.append(image)

        output_path = project_root / "examples" / f"batch_table_{i}.png"
        cv2.imwrite(str(output_path), image)

    print(f"    创建了 {len(images)} 个表格图像")

    # 初始化管道
    print("\n[2] 初始化处理管道...")
    pipeline = TableRecognitionPipeline(
        detector_type="simple",
        recognizer_type="morphological",
    )

    # 批量处理
    print("\n[3] 批量处理...")
    results = []
    for i, image in enumerate(images):
        print(f"    处理图像 {i + 1}/{len(images)}...")
        result = pipeline.process_image(image)
        results.append(result)

    # 汇总结果
    print("\n[4] 处理结果汇总:")
    for i, result in enumerate(results):
        print(f"    图像 {i + 1}: 检测到 {len(result['tables'])} 个表格")

    return results


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("表格识别系统 - 完整演示")
    print("=" * 60)

    # 运行各个演示
    try:
        # 基础使用
        result1 = demo_basic_usage()

        # 可视化
        vis_image = demo_visualization()

        # 导出格式
        result2 = demo_export_formats()

        # 高级使用
        detections, structure, cells = demo_advanced_usage()

        # 批量处理
        results = demo_batch_processing()

        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n输出文件位置:")
        print("  - examples/sample_table.png")
        print("  - examples/sample_tables.png")
        print("  - examples/visualization_result.png")
        print("  - examples/result.json")
        print("  - examples/result.csv")
        print("  - examples/result.html")
        print("  - examples/complex_table.png")
        print("  - examples/batch_table_*.png")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
