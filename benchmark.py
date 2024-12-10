import os
import subprocess
import threading
import time
from datetime import datetime

OUTPUT_DIR = "./output"
RESULT_FILE = os.path.join(OUTPUT_DIR, "benchmark_results.txt")
STATS_LOG_FILE = os.path.join(OUTPUT_DIR, "stats_log.txt")
monitoring = False

def clear_docker_logs():
    print("Clearing Docker logs...")
    try:
        subprocess.run(
            "truncate -s 0 $(docker inspect --format='{{.LogPath}}' $(docker ps -a -q))",
            shell=True,
            check=True
        )
        print("Docker logs cleared.")
    except subprocess.CalledProcessError as e:
        print(f"Error clearing Docker logs: {e}")

def monitor_stats(container_names):
    """
    指定したコンテナのリソース使用率をリアルタイムで取得し、ログに記録
    """
    global monitoring
    with open(STATS_LOG_FILE, "w") as f:
        f.write("Time, Container, CPU(%), MEM\n")
        while monitoring:
            for container_name in container_names:
                try:
                    stats = subprocess.check_output(
                        f"docker stats {container_name} --no-stream --format '{{{{.CPUPerc}}}},{{{{.MemUsage}}}}'",
                        shell=True,
                    ).decode("utf-8").strip()
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{timestamp}, {container_name}, {stats}\n")
                except subprocess.CalledProcessError as e:
                    print(f"Error fetching stats for container {container_name}: {e}")
            time.sleep(1)  # 1秒ごとに取得

def wait_for_master_completion():
    print("Waiting for master to complete tasks...")
    process = subprocess.Popen(
        "docker logs --follow master", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        while True:
            line = process.stdout.readline()
            if line:
                decoded_line = line.decode("utf-8").strip()
                print(decoded_line)
                if "最終結果を保存しました" in decoded_line:
                    print("Master has completed tasks.")
                    break
            else:
                time.sleep(1)
    finally:
        process.terminate()

def stop_docker_containers():
    print("Stopping Docker containers...")
    try:
        subprocess.run("docker-compose down", shell=True, check=True)
        print("Docker containers stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error stopping Docker containers: {e}")

def write_benchmark_result(start_time, end_time):
    """
    ベンチマーク結果をファイルに出力
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(RESULT_FILE, "w") as f:
        f.write("Benchmark Results\n")
        f.write("=================\n")
        f.write(f"Start Time: {start_time}\n")
        f.write(f"End Time: {end_time}\n")
        f.write(f"Total Duration: {end_time - start_time}\n\n")
        f.write(f"Resource usage logged to: {STATS_LOG_FILE}\n")
    print(f"Benchmark results saved to {RESULT_FILE}")

def main():
    global monitoring
    print("Starting benchmark...")

    clear_docker_logs()

    start_time = datetime.now()

    print("Starting Docker containers...")
    subprocess.run("docker-compose up -d", shell=True)

    # コンテナリスト
    containers = ["master", "worker-1"]
    #, "worker-2", "worker-3", "worker-4"

    # リアルタイムでリソース使用率を監視
    monitoring = True
    stats_thread = threading.Thread(target=monitor_stats, args=(containers,))
    stats_thread.start()

    # Masterコンテナのタスク完了を待機
    wait_for_master_completion()

    # 監視停止
    monitoring = False
    stats_thread.join()

    end_time = datetime.now()

    write_benchmark_result(start_time, end_time)

    stop_docker_containers()

    print("Benchmark completed.")

if __name__ == "__main__":
    main()
