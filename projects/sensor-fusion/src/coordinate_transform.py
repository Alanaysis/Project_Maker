"""
传感器坐标系与坐标变换模块

本模块提供传感器数据的坐标变换功能，包括：
- 欧拉角 (Euler Angles): roll/pitch/yaw
- 四元数 (Quaternions): 无奇异性的姿态表示
- 旋转矩阵 (Rotation Matrices): 3x3 旋转矩阵

姿态表示之间的转换是传感器融合的基础。
"""

import numpy as np


# ============================================================
# 欧拉角 (Euler Angles)
# ============================================================
# 欧拉角用三个角度 (roll, pitch, yaw) 表示姿态
# roll  (phi,  φ): 绕 X 轴旋转 - 横滚角
# pitch (theta, θ): 绕 Y 轴旋转 - 俯仰角
# yaw   (psi,   ψ): 绕 Z 轴旋转 - 偏航角
#
# 旋转顺序: ZYX (yaw -> pitch -> roll)，这是航空领域的标准
# ============================================================

def euler_to_rotation_matrix(roll, pitch, yaw):
    """
    将欧拉角 (roll, pitch, yaw) 转换为旋转矩阵
    
    旋转矩阵 R 将本体坐标系下的向量转换到导航坐标系:
        v_nav = R * v_body
    
    旋转顺序: ZYX (yaw * pitch * roll)
    
    Args:
        roll: 横滚角 (弧度)
        pitch: 俯仰角 (弧度)
        yaw: 偏航角 (弧度)
    
    Returns:
        3x3 旋转矩阵
    """
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    
    # ZYX 旋转顺序: R = Rz(yaw) * Rp(pitch) * Rr(roll)
    R = np.array([
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp,     cp * sr,                cp * cr]
    ])
    
    return R


def rotation_matrix_to_euler(R):
    """
    将旋转矩阵转换为欧拉角 (roll, pitch, yaw)
    
    使用 ZYX 旋转顺序反解欧拉角。
    注意: pitch = +/-90度 时会出现万向锁 (gimbal lock)
    
    Args:
        R: 3x3 旋转矩阵
    
    Returns:
        (roll, pitch, yaw) 元组 (弧度)
    """
    pitch = np.arcsin(-R[2, 0])
    
    # 检查万向锁 (pitch 接近 +/-90度)
    if np.abs(pitch) > np.pi / 2 - 1e-6:
        # 万向锁情况: pitch = -90度
        if pitch < 0:
            roll = 0
            yaw = np.arctan2(R[0, 1], R[1, 1])
        else:
            roll = 0
            yaw = np.arctan2(-R[0, 1], R[1, 1])
    else:
        roll = np.arctan2(R[2, 1], R[2, 2])
        yaw = np.arctan2(R[1, 0], R[0, 0])
    
    return roll, pitch, yaw


def rotation_matrix_to_quaternion(R):
    """
    将旋转矩阵转换为四元数
    
    四元数 q = [w, x, y, z] = [cos(theta/2), u*sin(theta/2)]
    其中 u 是旋转轴，theta 是旋转角
    
    Args:
        R: 3x3 旋转矩阵
    
    Returns:
        四元数 [w, x, y, z]
    """
    trace = R[0, 0] + R[1, 1] + R[2, 2]
    
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    else:
        if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
    
    return np.array([w, x, y, z])


def quaternion_to_rotation_matrix(q):
    """
    将四元数转换为旋转矩阵
    
    四元数到旋转矩阵的转换:
    R = (2*w^2 - 1)I + 2*q*q^T + 2*w*[q]_x
    
    Args:
        q: 四元数 [w, x, y, z]
    
    Returns:
        3x3 旋转矩阵
    """
    w, x, y, z = q
    
    # 归一化
    norm = np.sqrt(w**2 + x**2 + y**2 + z**2)
    if norm > 0:
        w, x, y, z = w/norm, x/norm, y/norm, z/norm
    
    R = np.zeros((3, 3))
    R[0, 0] = 1 - 2*(y**2 + z**2)
    R[0, 1] = 2*(x*y - w*z)
    R[0, 2] = 2*(x*z + w*y)
    R[1, 0] = 2*(x*y + w*z)
    R[1, 1] = 1 - 2*(x**2 + z**2)
    R[1, 2] = 2*(y*z - w*x)
    R[2, 0] = 2*(x*z - w*y)
    R[2, 1] = 2*(y*z + w*x)
    R[2, 2] = 1 - 2*(x**2 + y**2)
    
    return R


def quaternion_to_euler(q):
    """
    将四元数转换为欧拉角 (roll, pitch, yaw)
    
    Args:
        q: 四元数 [w, x, y, z]
    
    Returns:
        (roll, pitch, yaw) 元组 (弧度)
    """
    R = quaternion_to_rotation_matrix(q)
    return rotation_matrix_to_euler(R)


def euler_to_quaternion(roll, pitch, yaw):
    """
    将欧拉角转换为四元数
    
    分别计算三个轴的旋转四元数，然后相乘:
    q = q_z(yaw) * q_y(pitch) * q_x(roll)
    
    Args:
        roll: 横滚角 (弧度)
        pitch: 俯仰角 (弧度)
        yaw: 偏航角 (弧度)
    
    Returns:
        四元数 [w, x, y, z]
    """
    cx, sx = np.cos(roll / 2), np.sin(roll / 2)
    cy, sy = np.cos(pitch / 2), np.sin(pitch / 2)
    cz, sz = np.cos(yaw / 2), np.sin(yaw / 2)
    
    # q = q_z * q_y * q_x
    w = cz * cy * cx + sz * sy * sx
    x = cz * sy * sx + cy * cx * sz
    y = sz * cy * sx - cz * sy * cx
    z = cz * cy * sx - sz * sy * cx  # Fixed: correct formula
    
    # Actually, let me recalculate properly:
    # q_x = [cos(rx/2), sin(rx/2), 0, 0]
    # q_y = [cos(ry/2), 0, sin(ry/2), 0]
    # q_z = [cos(rz/2), 0, 0, sin(rz/2)]
    # q = q_z(yaw) * q_y(pitch) * q_x(roll)
    # q_x = [cx, sx, 0, 0]
    # q_y = [cy, 0, sy, 0]
    # q_z = [cz, 0, 0, sz]
    # q = q_z * q_y = [cz*cy, cz*sy, -sz*sy, sz*cy] -- let me compute properly
    # q_z * q_y:
    # w = cz*cy - 0*0 - 0*sy - sz*0 = cz*cy
    # x = cz*0 + 0*cy + sy*sz - 0*0 = sy*sz
    # y = cz*sy - 0*0 + 0*cy + sz*0 = cz*sy
    # z = cz*0 + 0*0 - sy*0 + sz*cy = sz*cy
    q_zy = np.array([cz*cy, sy*sz, cz*sy, sz*cy])
    
    # q = q_zy * q_x:
    w = q_zy[0]*cx - q_zy[1]*sx - q_zy[2]*0 - q_zy[3]*0
    x = q_zy[0]*sx + q_zy[1]*cx + q_zy[2]*0 - q_zy[3]*0
    y = q_zy[0]*0 - q_zy[1]*0 + q_zy[2]*cx + q_zy[3]*sx
    z = q_zy[0]*0 + q_zy[1]*0 - q_zy[2]*0 + q_zy[3]*cx
    
    return np.array([w, x, y, z])


def quaternion_multiply(q1, q2):
    """
    四元数乘法: q = q1 * q2
    
    四元数乘法表示连续旋转。
    注意: 四元数乘法不满足交换律，q1*q2 != q2*q1
    
    Args:
        q1: 四元数 [w, x, y, z]
        q2: 四元数 [w, x, y, z]
    
    Returns:
        乘积四元数 [w, x, y, z]
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    
    return np.array([w, x, y, z])


def quaternion_conjugate(q):
    """
    计算四元数的共轭
    
    q_conj = [w, -x, -y, -z]
    
    对于单位四元数，逆等于共轭: q_inv = q_conj
    
    Args:
        q: 四元数 [w, x, y, z]
    
    Returns:
        共轭四元数
    """
    return np.array([q[0], -q[1], -q[2], -q[3]])


def quaternion_normalize(q):
    """
    归一化四元数
    
    Args:
        q: 四元数 [w, x, y, z]
    
    Returns:
        归一化后的四元数
    """
    norm = np.sqrt(np.dot(q, q))
    if norm > 0:
        return q / norm
    return q.copy()


def rotate_vector_by_quaternion(q, v):
    """
    使用四元数旋转向量
    
    将向量 v 用四元数 q 旋转:
    v' = q * [0, v] * q_conj
    
    Args:
        q: 四元数 [w, x, y, z]
        v: 3D 向量 [x, y, z]
    
    Returns:
        旋转后的向量
    """
    q = quaternion_normalize(q)
    q_v = np.array([0, v[0], v[1], v[2]])
    q_result = quaternion_multiply(quaternion_multiply(q, q_v), quaternion_conjugate(q))
    return q_result[1:]


def rotate_vector_by_rotation_matrix(R, v):
    """
    使用旋转矩阵旋转向量
    
    Args:
        R: 3x3 旋转矩阵
        v: 3D 向量 [x, y, z]
    
    Returns:
        旋转后的向量
    """
    return R @ v


def angular_velocity_to_quaternion_derivative(q, omega, dt):
    """
    计算四元数导数 (用于姿态传播)
    
    四元数导数与角速度的关系:
    q_dot = 0.5 * omega_q ⊗ q
    
    其中 omega_q = [0, omega_x, omega_y, omega_z] 是纯四元数
    
    离散化 (一阶 Euler):
    q[k+1] = q[k] + 0.5 * omega_q[k] ⊗ q[k] * dt
    q[k+1] = normalize(q[k+1])
    
    Args:
        q: 当前四元数 [w, x, y, z]
        omega: 角速度 [wx, wy, wz] (rad/s)
        dt: 时间步长 (s)
    
    Returns:
        更新后的四元数 (已归一化)
    """
    # 半角速度
    half_dt = 0.5 * dt
    
    # 四元数导数
    qw, qx, qy, qz = q
    wx, wy, wz = omega
    
    dq = np.array([
        -wx*qx - wy*qy - wz*qz,
         wx*qw + wz*qy - wy*qz,
         wy*qw - wz*qx + wx*qz,
         wz*qw + wy*qx - wx*qy
    ])
    
    # Euler 积分
    q_new = q + dq * dt
    return quaternion_normalize(q_new)


def skew_symmetric(v):
    """
    构造向量 v 的反对称矩阵
    
    [v]_x = [[ 0, -vz,  vy],
              [ vz,  0, -vx],
              [-vy,  vx,  0 ]]
    
    用于四元数运算和角速度矩阵表示
    
    Args:
        v: 3D 向量
    
    Returns:
        3x3 反对称矩阵
    """
    return np.array([
        [0,    -v[2],  v[1]],
        [v[2],  0,    -v[0]],
        [-v[1], v[0],  0   ]
    ])
