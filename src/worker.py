import json
import redis
from integrator import Integrator
import os

class Worker:
    def __init__(self):
        # Redisホストを正しい名前に設定
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.worker_id = os.getenv('WORKER_ID', '0')
    
    def start(self):
        """ワーカープロセスのメインループ"""
        print(f"ワーカーノード {self.worker_id} を開始します...")
        while True:
            print(f"ワーカー {self.worker_id}: タスクを待機しています...")
            # タスクの取得
            task = self.redis_client.blpop('tasks', timeout=0)
            if task:
                task_data = json.loads(task[1])
                print(f"ワーカー {self.worker_id}: タスクを取得しました: {task_data}")

                try:
                    # サブタスクごとの積分計算
                    result = Integrator.numerical_integration(
                        task_data['func_str'],
                        task_data['x_range'],
                        task_data['y_range']
                    )
                    print(f"ワーカー {self.worker_id}: 計算結果: {result}")

                    # 部分結果をJSONファイルに保存
                    output_data = {
                        'func_str': task_data['func_str'],
                        'x_range': task_data['x_range'],
                        'y_range': task_data['y_range'],
                        'partial_result': result
                    }
                    json_path = f"/app/output/task-{self.worker_id}.json"  # ファイル名にワーカーIDを含む
                    with open(json_path, 'w') as f:
                        json.dump(output_data, f, indent=4)
                    print(f"ワーカー {self.worker_id}: 部分結果をJSONファイルに保存しました: {json_path}")

                    # Redisカウンターをインクリメント
                    self.redis_client.incr('completed_tasks')

                except Exception as e:
                    print(f"ワーカー {self.worker_id}: エラーが発生しました: {e}")

if __name__ == "__main__":
    worker = Worker()
    worker.start()
