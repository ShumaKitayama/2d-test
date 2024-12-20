from sympy import symbols, sympify, lambdify, sin, cos, exp, sqrt, log
import numpy as np

class Integrator:
    def __init__(self, func_str, x_range, y_range):
        self.x, self.y = symbols('x y')
        self.func = sympify(func_str)
        self.x_range = x_range
        self.y_range = y_range

    def divide_tasks(self, num_workers):
        """領域を指定された数のサブ領域に分割する"""
        x_splits = np.linspace(self.x_range[0], self.x_range[1], num_workers + 1)
        tasks = []
        for i in range(num_workers):
            task = {
                'func_str': str(self.func),
                'x_range': [float(x_splits[i]), float(x_splits[i+1])],
                'y_range': self.y_range
            }
            tasks.append(task)
        return tasks

    @staticmethod
    def numerical_integration(func_str, x_range, y_range, num_points=5000):
        """
        複雑な関数かつ大量の分割数で二次元積分を行い、
        計算量を大幅に増やすことで時間をかける。
        
        func_str: 複雑な関数例
        x_range, y_range: [min, max]
        num_points: 分割数を大幅に増やす
        """
        x, y = symbols('x y')
        func = sympify(func_str)
        
        # lambdifyでsympy関数をnumpy対応関数に変換
        f = lambdify((x, y), func, "numpy")

        # 格子点の生成
        x_points = np.linspace(x_range[0], x_range[1], num_points)
        y_points = np.linspace(y_range[0], y_range[1], num_points)
        dx = (x_range[1] - x_range[0]) / (num_points - 1)
        dy = (y_range[1] - y_range[0]) / (num_points - 1)
        
        X, Y = np.meshgrid(x_points, y_points)
        
        # ベクトル化された関数評価
        Z = f(X, Y)
        
        # 面積要素を掛け合わせて総和
        total = np.sum(Z) * dx * dy
        return total
