//! 曲线编辑器
//!
//! 提供贝塞尔曲线的编辑操作，包括移动控制点、分割曲线、反转方向等。

use crate::point::Point;
use crate::bezier::{QuadraticBezier, CubicBezier, BezierCurve, BezierCurveType};
use crate::subdivision::{subdivide_quadratic, subdivide_cubic};

/// 曲线编辑器
#[derive(Debug)]
pub struct CurveEditor {
    /// 当前编辑的曲线
    curves: Vec<BezierCurveType>,
    /// 选中的曲线索引
    selected_curve: Option<usize>,
    /// 选中的控制点索引
    selected_point: Option<usize>,
}

impl CurveEditor {
    /// 创建新的编辑器
    pub fn new() -> Self {
        Self {
            curves: Vec::new(),
            selected_curve: None,
            selected_point: None,
        }
    }

    /// 添加二次贝塞尔曲线
    pub fn add_quadratic(&mut self, curve: QuadraticBezier) -> usize {
        let index = self.curves.len();
        self.curves.push(BezierCurveType::Quadratic(curve));
        index
    }

    /// 添加三次贝塞尔曲线
    pub fn add_cubic(&mut self, curve: CubicBezier) -> usize {
        let index = self.curves.len();
        self.curves.push(BezierCurveType::Cubic(curve));
        index
    }

    /// 获取曲线数量
    pub fn curve_count(&self) -> usize {
        self.curves.len()
    }

    /// 获取指定曲线的引用
    pub fn get_curve(&self, index: usize) -> Option<&BezierCurveType> {
        self.curves.get(index)
    }

    /// 获取指定曲线的可变引用
    pub fn get_curve_mut(&mut self, index: usize) -> Option<&mut BezierCurveType> {
        self.curves.get_mut(index)
    }

    /// 选择曲线
    pub fn select_curve(&mut self, index: usize) -> bool {
        if index < self.curves.len() {
            self.selected_curve = Some(index);
            self.selected_point = None;
            true
        } else {
            false
        }
    }

    /// 选择控制点
    pub fn select_point(&mut self, curve_index: usize, point_index: usize) -> bool {
        if let Some(curve) = self.curves.get(curve_index) {
            let points = curve.control_points_vec();
            if point_index < points.len() {
                self.selected_curve = Some(curve_index);
                self.selected_point = Some(point_index);
                return true;
            }
        }
        false
    }

    /// 获取选中的曲线索引
    pub fn selected_curve(&self) -> Option<usize> {
        self.selected_curve
    }

    /// 获取选中的控制点索引
    pub fn selected_point(&self) -> Option<usize> {
        self.selected_point
    }

    /// 移动选中的控制点
    pub fn move_selected_point(&mut self, delta: Point) -> bool {
        if let (Some(curve_idx), Some(point_idx)) = (self.selected_curve, self.selected_point) {
            self.move_point(curve_idx, point_idx, delta)
        } else {
            false
        }
    }

    /// 移动指定控制点
    pub fn move_point(&mut self, curve_index: usize, point_index: usize, delta: Point) -> bool {
        match self.curves.get_mut(curve_index) {
            Some(BezierCurveType::Quadratic(ref mut curve)) => {
                match point_index {
                    0 => { curve.p0 = curve.p0 + delta; true }
                    1 => { curve.p1 = curve.p1 + delta; true }
                    2 => { curve.p2 = curve.p2 + delta; true }
                    _ => false,
                }
            }
            Some(BezierCurveType::Cubic(ref mut curve)) => {
                match point_index {
                    0 => { curve.p0 = curve.p0 + delta; true }
                    1 => { curve.p1 = curve.p1 + delta; true }
                    2 => { curve.p2 = curve.p2 + delta; true }
                    3 => { curve.p3 = curve.p3 + delta; true }
                    _ => false,
                }
            }
            None => false,
        }
    }

    /// 设置指定控制点的位置
    pub fn set_point(
        &mut self,
        curve_index: usize,
        point_index: usize,
        position: Point,
    ) -> bool {
        match self.curves.get_mut(curve_index) {
            Some(BezierCurveType::Quadratic(ref mut curve)) => {
                match point_index {
                    0 => { curve.p0 = position; true }
                    1 => { curve.p1 = position; true }
                    2 => { curve.p2 = position; true }
                    _ => false,
                }
            }
            Some(BezierCurveType::Cubic(ref mut curve)) => {
                match point_index {
                    0 => { curve.p0 = position; true }
                    1 => { curve.p1 = position; true }
                    2 => { curve.p2 = position; true }
                    3 => { curve.p3 = position; true }
                    _ => false,
                }
            }
            None => false,
        }
    }

    /// 在指定参数处分割曲线
    ///
    /// 返回新插入的两条曲线的索引
    pub fn split_curve(&mut self, curve_index: usize, t: f64) -> Option<(usize, usize)> {
        if curve_index >= self.curves.len() {
            return None;
        }

        let t = t.max(0.0).min(1.0);
        let curve = self.curves.remove(curve_index);

        match curve {
            BezierCurveType::Quadratic(quad) => {
                let (left, right) = subdivide_quadratic(&quad, t);
                self.curves.insert(curve_index, BezierCurveType::Quadratic(right));
                self.curves.insert(curve_index, BezierCurveType::Quadratic(left));
                Some((curve_index, curve_index + 1))
            }
            BezierCurveType::Cubic(cubic) => {
                let (left, right) = subdivide_cubic(&cubic, t);
                self.curves.insert(curve_index, BezierCurveType::Cubic(right));
                self.curves.insert(curve_index, BezierCurveType::Cubic(left));
                Some((curve_index, curve_index + 1))
            }
        }
    }

    /// 反转曲线方向
    pub fn reverse_curve(&mut self, curve_index: usize) -> bool {
        match self.curves.get_mut(curve_index) {
            Some(BezierCurveType::Quadratic(ref mut curve)) => {
                std::mem::swap(&mut curve.p0, &mut curve.p2);
                true
            }
            Some(BezierCurveType::Cubic(ref mut curve)) => {
                std::mem::swap(&mut curve.p0, &mut curve.p3);
                std::mem::swap(&mut curve.p1, &mut curve.p2);
                true
            }
            None => false,
        }
    }

    /// 提升二次曲线到三次
    pub fn elevate_to_cubic(&mut self, curve_index: usize) -> bool {
        if let Some(BezierCurveType::Quadratic(quad)) = self.curves.get(curve_index) {
            let cubic = quad.elevate_to_cubic();
            self.curves[curve_index] = BezierCurveType::Cubic(cubic);
            true
        } else {
            false
        }
    }

    /// 删除曲线
    pub fn remove_curve(&mut self, index: usize) -> Option<BezierCurveType> {
        if index < self.curves.len() {
            if self.selected_curve == Some(index) {
                self.selected_curve = None;
                self.selected_point = None;
            } else if self.selected_curve.map(|i| i > index).unwrap_or(false) {
                self.selected_curve = self.selected_curve.map(|i| i - 1);
            }
            Some(self.curves.remove(index))
        } else {
            None
        }
    }

    /// 获取所有曲线的控制点列表
    pub fn all_control_points(&self) -> Vec<Vec<Point>> {
        self.curves.iter().map(|c| c.control_points_vec()).collect()
    }

    /// 查找最近的控制点
    pub fn find_nearest_control_point(&self, position: Point, max_distance: f64) -> Option<(usize, usize)> {
        let mut best = None;
        let mut best_dist_sq = max_distance * max_distance;

        for (curve_idx, curve) in self.curves.iter().enumerate() {
            for (point_idx, point) in curve.control_points_vec().iter().enumerate() {
                let dist_sq = position.distance_squared_to(point);
                if dist_sq < best_dist_sq {
                    best_dist_sq = dist_sq;
                    best = Some((curve_idx, point_idx));
                }
            }
        }

        best
    }

    /// 查找最近的曲线上的点
    pub fn find_nearest_curve_point(&self, position: Point) -> Option<(usize, f64)> {
        let mut best = None;
        let mut best_dist_sq = f64::MAX;

        for (curve_idx, curve) in self.curves.iter().enumerate() {
            let t = match curve {
                BezierCurveType::Quadratic(c) => {
                    c.closest_point_parameter(&position, 100)
                }
                BezierCurveType::Cubic(c) => {
                    c.closest_point_parameter(&position, 100)
                }
            };

            let point_on_curve = curve.evaluate(t);
            let dist_sq = position.distance_squared_to(&point_on_curve);

            if dist_sq < best_dist_sq {
                best_dist_sq = dist_sq;
                best = Some((curve_idx, t));
            }
        }

        best
    }
}

impl Default for CurveEditor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_editor_add_curves() {
        let mut editor = CurveEditor::new();

        let quad = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );
        let idx = editor.add_quadratic(quad);
        assert_eq!(idx, 0);
        assert_eq!(editor.curve_count(), 1);

        let cubic = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(25.0, 100.0),
            Point::new(75.0, 100.0),
            Point::new(100.0, 0.0),
        );
        let idx = editor.add_cubic(cubic);
        assert_eq!(idx, 1);
        assert_eq!(editor.curve_count(), 2);
    }

    #[test]
    fn test_editor_select() {
        let mut editor = CurveEditor::new();

        let quad = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );
        editor.add_quadratic(quad);

        assert!(editor.select_curve(0));
        assert_eq!(editor.selected_curve(), Some(0));

        assert!(editor.select_point(0, 1));
        assert_eq!(editor.selected_point(), Some(1));
    }

    #[test]
    fn test_editor_move_point() {
        let mut editor = CurveEditor::new();

        let quad = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );
        editor.add_quadratic(quad);

        editor.select_point(0, 1);
        editor.move_selected_point(Point::new(10.0, -20.0));

        if let Some(BezierCurveType::Quadratic(curve)) = editor.get_curve(0) {
            assert!((curve.p1.x - 60.0).abs() < 1e-10);
            assert!((curve.p1.y - 80.0).abs() < 1e-10);
        } else {
            panic!("Expected quadratic curve");
        }
    }

    #[test]
    fn test_editor_split_curve() {
        let mut editor = CurveEditor::new();

        let cubic = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(25.0, 100.0),
            Point::new(75.0, 100.0),
            Point::new(100.0, 0.0),
        );
        editor.add_cubic(cubic);
        assert_eq!(editor.curve_count(), 1);

        let result = editor.split_curve(0, 0.5);
        assert!(result.is_some());
        assert_eq!(editor.curve_count(), 2);
    }

    #[test]
    fn test_editor_reverse_curve() {
        let mut editor = CurveEditor::new();

        let quad = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );
        editor.add_quadratic(quad);

        editor.reverse_curve(0);

        if let Some(BezierCurveType::Quadratic(curve)) = editor.get_curve(0) {
            assert!((curve.p0.x - 100.0).abs() < 1e-10);
            assert!((curve.p2.x - 0.0).abs() < 1e-10);
        } else {
            panic!("Expected quadratic curve");
        }
    }

    #[test]
    fn test_editor_elevate_to_cubic() {
        let mut editor = CurveEditor::new();

        let quad = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );
        editor.add_quadratic(quad);

        assert!(editor.elevate_to_cubic(0));

        if let Some(BezierCurveType::Cubic(_)) = editor.get_curve(0) {
            // 成功提升到三次曲线
        } else {
            panic!("Expected cubic curve after elevation");
        }
    }

    #[test]
    fn test_editor_find_nearest() {
        let mut editor = CurveEditor::new();

        let quad = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );
        editor.add_quadratic(quad);

        // 查找接近 (50, 100) 的控制点
        let result = editor.find_nearest_control_point(Point::new(48.0, 102.0), 10.0);
        assert!(result.is_some());
        let (curve_idx, point_idx) = result.unwrap();
        assert_eq!(curve_idx, 0);
        assert_eq!(point_idx, 1); // p1 = (50, 100)
    }
}
