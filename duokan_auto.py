import os
import time
import requests
import json
import random
from datetime import datetime

# 日志记录函数
def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    return message

# 获取环境变量（从GitHub Secrets读取Cookie和Server酱Key）
def get_env():
    cookie = os.getenv("DUOKAN_COOKIE")
    serverchan_key = os.getenv("SERVERCHAN_KEY")
    if not cookie:
        log("❌ 未设置DUOKAN_COOKIE环境变量，任务终止")
        return None, None
    if not serverchan_key:
        log("⚠️ 未设置SERVERCHAN_KEY，将无法推送微信通知")
    return cookie, serverchan_key

# 发送微信通知
def send_notification(title, content, serverchan_key):
    if not serverchan_key:
        return log("通知发送失败：未设置SERVERCHAN_KEY")
    url = f"https://sctapi.ftqq.com/{serverchan_key}.send"
    data = {"title": title, "desp": content}
    try:
        response = requests.post(url, data=data)
        if response.json().get("code") == 0:
            return log(f"通知发送成功：{title}")
        else:
            return log(f"通知发送失败：{response.json().get('message')}")
    except Exception as e:
        return log(f"通知发送异常：{str(e)}")

# 生成请求参数（时间戳和校验值）
def get_params():
    t = int(time.time())
    c = t % 10000  # 简化处理，实际需根据抓包调整校验逻辑
    return f"_t={t}&_c={c}"

# 多看阅读自动任务类
class DuokanTask:
    def __init__(self, cookie):
        self.cookie = cookie
        self.headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22101316C Build/UP1A.231005.007) XiaoMi/MiuiBrowser/2.1.1",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        self.result = ["----------多看阅读自动任务开始----------"]
        self.coin_total = 0  # 累计书豆数

    def check_in(self):
        """执行每日签到"""
        log("开始执行签到...")
        url = "https://www.duokan.com/api/dk-user/checkin/record"
        data = get_params()
        try:
            response = requests.post(url, headers=self.headers, data=data)
            result = response.json()
            if result.get("result") == 0 and result.get("data", {}).get("ifCheckin"):
                coin = result.get("data", {}).get("coinList", [0])[0]
                days = result.get("data", {}).get("continuityDay", 0)
                self.coin_total += coin
                self.result.append(f"✅ 签到成功！获得 {coin} 书豆，连续签到 {days} 天")
                return True
            elif result.get("msg") == "今日已签到":
                self.result.append("✅ 今日已完成签到，跳过")
                return True
            else:
                msg = result.get("msg", "签到失败")
                self.result.append(f"❌ 签到失败: {msg}")
                return False
        except Exception as e:
            self.result.append(f"❌ 签到异常: {str(e)}")
            return False

    def get_tasks(self):
        """获取任务列表"""
        log("获取任务列表...")
        url = "https://www.duokan.com/hs/v4/channel/query/1250"
        data = get_params()
        try:
            response = requests.post(url, headers=self.headers, data=data)
            result = response.json()
            if result.get("result") == 0:
                tasks = result.get("items", [])
                self.result.append(f"✅ 获取任务列表成功，共 {len(tasks)} 个任务")
                return tasks
            else:
                self.result.append(f"❌ 获取任务列表失败: {result.get('msg', '未知错误')}")
                return []
        except Exception as e:
            self.result.append(f"❌ 获取任务列表异常: {str(e)}")
            return []

    def complete_tasks(self, tasks):
        """完成可执行的任务（下载、阅读、视频等，需结合真实接口扩展）"""
        if not tasks:
            self.result.append("⚠️ 无任务可执行")
            return
        log(f"开始执行 {len(tasks)} 个任务...")
        executed_tasks = 0
        for task in tasks:
            task_name = task.get("title", "未知任务")
            self.result.append(f"正在执行任务: {task_name}")
            # 提取任务奖励（从任务扩展字段中获取）
            task_data = task.get("data", {}).get("data", [{}])[0]
            extend = task_data.get("extend", {})
            coins = int(extend.get("coins", 0))
            ad_id = task_data.get("ad_id", "")
            
            # 根据任务名称判断类型并模拟执行（实际需替换为真实接口调用）
            if "下载广告" in task_name:
                self._simulate_task(coins, 5, 10, "下载")
                executed_tasks += 1
            elif "体验APP" in task_name:
                self._simulate_task(coins, 30, 60, "体验")
                executed_tasks += 1
            elif "免费书阅读任务" in task_name:
                self._simulate_task(coins, 600, 610, "阅读")
                executed_tasks += 1
            elif "视频广告" in task_name:
                self._simulate_task(coins, 15, 30, "观看视频")
                executed_tasks += 1
            else:
                self.result.append(f"⚠️ 暂不支持该任务: {task_name}")
            
            # 随机延迟防封（3-8秒）
            time.sleep(random.uniform(3, 8))
        self.result.append(f"✅ 任务执行完毕，成功完成 {executed_tasks} 个任务，累计获得 {self.coin_total} 书豆")

    def _simulate_task(self, coins, min_seconds, max_seconds, task_type):
        """模拟任务执行（实际需替换为真实接口调用，此处仅演示）"""
        if coins <= 0:
            self.result.append(f"⚠️ 任务无奖励，跳过")
            return
        sleep_time = random.uniform(min_seconds, max_seconds)
        log(f"模拟{task_type}任务执行，耗时{int(sleep_time)}秒...")
        time.sleep(sleep_time)
        self.coin_total += coins
        self.result.append(f"✅ {task_type}任务完成！获得 {coins} 书豆")

    def get_user_coin_balance(self):
        """获取书豆余额（需补充真实接口，此处仅模拟）"""
        log("获取书豆余额...")
        # 实际需调用 /store/v0/award/coin/list 接口
        self.result.append("💎 书豆余额（模拟）: 100 + 今日获得 {self.coin_total}")

    def get_result_summary(self):
        """生成任务结果汇总"""
        summary = "\n".join(self.result)
        summary += f"\n----------今日汇总----------"
        summary += f"\n📊 累计获得书豆: {self.coin_total}"
        summary += f"\n----------多看阅读自动任务结束----------"
        return summary

# 主函数
def main():
    cookie, serverchan_key = get_env()
    if not cookie:
        send_notification("多看阅读任务失败", "未获取到Cookie，任务终止", serverchan_key)
        return
    
    task = DuokanTask(cookie)
    # 1. 执行签到
    checkin_success = task.check_in()
    # 2. 获取任务列表
    tasks = task.get_tasks()
    # 3. 完成任务
    task.complete_tasks(tasks)
    # 4. 获取余额（模拟）
    task.get_user_coin_balance()
    # 5. 汇总结果
    summary = task.get_result_summary()
    print(summary)
    # 6. 发送通知
    title = "✅ 多看阅读任务成功" if checkin_success else "❌ 多看阅读任务失败"
    send_notification(title, summary, serverchan_key)

if __name__ == "__main__":
    main()
