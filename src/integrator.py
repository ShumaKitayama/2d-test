from sympy import symbols, sympify
import numpy as np

class Integrator:
    def __init__(self, func_str, x_range, y_range):
        self.x, self.y = symbols('x y')
        self.func = sympify(func_str)
        self.x_range = x_range
        self.y_range = y_range
    
    def divide_tasks(self, num_workers):
        """領域を指定された数のサブ領域に分割"""
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
    def numerical_integration(func_str, x_range, y_range, num_points=1000):
        """数値積分の実行"""
        x = symbols('x')
        y = symbols('y')
        func = sympify(func_str)
        
        x_points = np.linspace(x_range[0], x_range[1], num_points)
        y_points = np.linspace(y_range[0], y_range[1], num_points)
        dx = (x_range[1] - x_range[0]) / num_points
        dy = (y_range[1] - y_range[0]) / num_points
        
        total = 0
        for xi in x_points:
            for yi in y_points:
                try:
                    total += float(func.subs([(x, xi), (y, yi)]))
                except Exception as e:
                    print(f"積分計算中のエラー: {e}")
                    return None  # エラーが発生した場合は終了
        
        return total * dx * dy
