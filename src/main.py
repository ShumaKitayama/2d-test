import json
import os
import redis
import glob
import time  # 待機用
from worker import Worker
from integrator import Integrator

class Master:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.last_logged_tasks = 0

    def load_task(self, filepath):
        """設定ファイルからタスクデータを読み込む"""
        with open(filepath, 'r') as file:
            task_data = json.load(file)
        return task_data
    
    def submit_task(self):
        """タスクを分割してRedisに送信する"""
        task_data = self.load_task('/app/input/task.json')
        integrator = Integrator(task_data['func_str'], task_data['x_range'], task_data['y_range'])
        
        # タスクを分割
        sub_tasks = integrator.divide_tasks(num_workers=4)  # ワーカー数に合わせる
        
        # タスク数をRedisに記録
        total_tasks = len(sub_tasks)
        self.redis_client.set('total_tasks', total_tasks)  # 総タスク数
        self.redis_client.set('completed_tasks', 0)        # 完了したタスク数を初期化
        
        # 各タスクをRedisキューに追加
        for sub_task in sub_tasks:
            self.redis_client.rpush('tasks', json.dumps(sub_task))
            print(f"サブタスクをRedisに送信しました: {sub_task}")

    def wait_for_completion(self):
        """すべてのタスクが完了するまで待機"""
        total_tasks = int(self.redis_client.get('total_tasks'))  # 総タスク数
        while True:
            completed_tasks = int(self.redis_client.get('completed_tasks'))  # 完了したタスク数
            if completed_tasks > self.last_logged_tasks:  # 進捗が変わったときのみログ出力
                print(f"完了タスク数: {completed_tasks}/{total_tasks}")
                self.last_logged_tasks = completed_tasks
            if completed_tasks >= total_tasks:
                break
            time.sleep(1)  # 1秒待機

    def calculate_final_result(self):
        """JSONファイルから部分結果を集計して最終結果を計算"""
        partial_results = []
        json_files = glob.glob('/app/output/task-*.json')
        
        if not json_files:
            print("部分結果のJSONファイルが見つかりませんでした。")
            return

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    partial_results.append(data['partial_result'])
                    print(f"読み取った部分結果: {data['partial_result']}")
            except Exception as e:
                print(f"ファイル読み取り中のエラー: {json_file}, エラー: {e}")

        if partial_results:
            final_result = sum(partial_results)
            # 最終結果の保存
            with open('/app/output/result.txt', 'w') as f:
                f.write(f"Final Result: {final_result}\n")
            print(f"最終結果を保存しました: {final_result}")
        else:
            print("部分結果が読み取れませんでした。")

if __name__ == "__main__":
    role = os.getenv('ROLE', 'master')
    
    if role == 'master':
        print("マスターノードを開始します...")
        master = Master()
        master.submit_task()
        master.wait_for_completion()  # 全タスクの完了を待機
        master.calculate_final_result()  # 最終結果を計算
    elif role == 'worker':
        print("ワーカーノードを開始します...")
        worker = Worker()
        worker.start()
    else:
        print("エラー: 不明なROLEです。")
