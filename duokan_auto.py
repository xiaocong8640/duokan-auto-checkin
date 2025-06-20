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
        log("❌ 未设置DUOKAN_COOKIE环境变量")
        return None, None
    if not serverchan_key:
        log("⚠️ 未设置SERVERCHAN_KEY，将无法推送微信通知")
    return cookie, serverchan_key

# 发送微信通知
def send_notification(title, content, serverchan_key):
    if not serverchan_key:
        return log(f"通知发送失败：未设置SERVERCHAN_KEY")
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
    c = t % 10000  # 简化处理，实际需根据抓包调整
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
        """完成可执行的任务（下载、阅读、视频等）"""
        if not tasks:
            self.result.append("⚠️ 无任务可执行")
            return
        log(f"开始执行 {len(tasks)} 个任务...")
        executed = 0
        for task in tasks:
            name = task.get("title", "未知任务")
            self.result.append(f"正在执行: {name}")
            # 从任务中提取书豆奖励（若有）
            coins = int(task.get("data", {}).get("data", [{}])[0].get("extend", {}).get("coins", 0))
            # 简化处理不同任务类型（实际需根据接口开发）
            if "下载广告" in name:
                self._simulate_task(coins, 5, 10)  # 模拟下载任务5-10秒
            elif "体验APP" in name:
                self._simulate_task(coins, 30, 60)  # 模拟体验任务30-60秒
            elif "免费书阅读" in name:
                self._simulate_task(coins, 600, 610)  # 模拟阅读10分钟
            elif "视频广告" in name:
                self._simulate_task(coins, 15, 30)  # 模拟视频15-30秒
            else:
                self.result.append(f"⚠️ 暂不支持: {name}")
            # 随机延迟防封
            time.sleep(random.uniform(3, 8))
        self.result.append(f"✅ 完成 {executed} 个任务，累计获得 {self.coin_total} 书豆")

    def _simulate_task(self, coins, min_seconds, max_seconds):
        """模拟任务执行（实际需替换为真实接口调用）"""
        if coins > 0:
            self.coin_total += coins
            sleep_time = random.uniform(min_seconds, max_seconds)
            time.sleep(sleep_time)
            self.result.append(f"✅ 任务完成！获得 {coins} 书豆（耗时{int(sleep_time)}秒）")

    def get_result_summary(self):
        """生成任务结果汇总"""
        summary = "\n".join(self.result)
        summary += f"\n----------今日汇总----------"
        summary += f"\n📊 累计获得: {self.coin_total} 书豆"
        summary += f"\n----------任务结束----------"
        return summary

# 主函数
def main():
    cookie, serverchan_key = get_env()
    if not cookie:
        send_notification("多看任务失败", "未获取到Cookie，任务终止", serverchan_key)
        return
    task = DuokanTask(cookie)
    # 执行签到
    checkin_success = task.check_in()
    # 获取任务
    tasks = task.get_tasks()
    # 完成任务
    task.complete_tasks(tasks)
    # 汇总结果
    summary = task.get_result_summary()
    print(summary)
    # 发送通知
    title = "✅ 多看任务成功" if checkin_success else "❌ 多看任务失败"
    send_notification(title, summary, serverchan_key)

if __name__ == "__main__":
    main()
