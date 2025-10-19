import requests
import json
import os
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SFSign:
    def __init__(self):
        # 从环境变量获取配置
        self.config = {
            "nonce": os.getenv('SF_NONCE'),
            "devicetoken": os.getenv('SF_DEVICETOKEN'),
            "sign": os.getenv('SF_SIGN'),
            "authorization": os.getenv('SF_AUTHORIZATION'),
            "cookie": {
                "sfCommunity": os.getenv('SF_COOKIE_SFCOMMUNITY'),
                "sessionAPP": os.getenv('SF_COOKIE_SESSIONAPP')
            },
            "ntfy_topic": os.getenv('NTFY_TOPIC')
        }
        
        self.base_url = "https://api.sfacg.com"
        self.ntfy_url = "https://ntfy.sh"
        self.session = requests.Session()
        
        # 设置User-Agent
        self.session.headers.update({
            "User-Agent": "boluobao/5.0.32(iOS;14.2)/appStore/5B778D69-AE1B-44EF-A029-0721A394C9F8/appStore",
            "Accept-Language": "zh-Hans-CN;q=1, el-CN;q=0.9, ja-CN;q=0.8"
        })

    def generate_timestamp(self):
        """生成时间戳（毫秒）"""
        return int(datetime.now().timestamp() * 1000)

    def build_sf_security(self, timestamp=None):
        """构建SFSecurity头"""
        ts = timestamp or self.generate_timestamp()
        return f"nonce={self.config['nonce']}&timestamp={ts}&devicetoken={self.config['devicetoken']}&sign={self.config['sign']}"

    def build_cookie(self):
        """构建Cookie头"""
        return f".SFCommunity={self.config['cookie']['sfCommunity']}; session_APP={self.config['cookie']['sessionAPP']}"

    def send_ntfy_notification(self, title, message, priority="default", tags=[]):
        """发送通知到ntfy.sh"""
        try:
            data = message.encode('utf-8')
            headers = {
                "Title": title.encode('utf-8'),
                "Priority": priority,
                "Tags": ",".join(tags)
            }
            response = requests.post(
                f"{self.ntfy_url}/{self.config['ntfy_topic']}",
                data=data,
                headers=headers,
                timeout=10
            )
            logger.info(f"ntfy通知发送成功: {title}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ntfy通知发送失败: {e}")
            return False

    def sign_in(self):
        """执行签到任务"""
        url = f"{self.base_url}/user/newSignInfo"
        current_date = datetime.now().strftime("%Y-%m-%d")

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Accept": "application/vnd.sfacg.api+json;version=1",
            "SFSecurity": self.build_sf_security(),
            "Authorization": f"Basic {self.config['authorization']}",
            "Cookie": self.build_cookie()
        }

        data = {
            "signDate": current_date
        }

        try:
            logger.info(f"开始签到，日期: {current_date}")
            response = self.session.put(url, headers=headers, json=data, timeout=30)
            
            logger.info(f"签到HTTP状态码: {response.status_code}")
            logger.info(f"签到响应内容: {response.text}")

            if response.status_code == 200:
                voucher_result = self.parse_voucher_count(response.text)
                if voucher_result['success']:
                    return {
                        "success": True,
                        "message": f"获得 {voucher_result['count']} {voucher_result['rewardName']}",
                        "voucherCount": voucher_result['count'],
                        "rewardName": voucher_result['rewardName'],
                        "statusCode": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "message": f"签到解析失败\n原始响应: {voucher_result['rawResponse']}",
                        "voucherCount": None,
                        "statusCode": response.status_code
                    }
            else:
                return {
                    "success": False,
                    "message": f"签到失败({response.status_code})\n原始响应: {response.text}",
                    "voucherCount": None,
                    "statusCode": response.status_code
                }
                
        except Exception as e:
            logger.error(f"签到请求异常: {e}")
            return {
                "success": False,
                "message": f"签到网络请求失败: {str(e)}",
                "voucherCount": None,
                "statusCode": None
            }

    def parse_voucher_count(self, response_text):
        """解析响应数据，提取代券数量"""
        try:
            data = json.loads(response_text)
            if data.get('status', {}).get('httpCode') == 200:
                if data.get('data') and len(data['data']) > 0:
                    # 查找代券奖励
                    voucher_item = next((item for item in data['data'] if item.get('name') == '代券'), None)
                    if voucher_item:
                        return {
                            'success': True,
                            'count': voucher_item.get('num'),
                            'rewardName': voucher_item.get('name')
                        }
                    # 如果没有代券，取第一个奖励
                    return {
                        'success': True,
                        'count': data['data'][0].get('num'),
                        'rewardName': data['data'][0].get('name')
                    }
            return {
                'success': False,
                'count': None,
                'rawResponse': response_text
            }
        except Exception as e:
            return {
                'success': False,
                'count': None,
                'rawResponse': response_text
            }

def main():
    """主执行函数"""
    sf_sign = SFSign()
    
    # 检查必要配置
    required_env_vars = [
        'SF_NONCE', 'SF_DEVICETOKEN', 'SF_SIGN', 'SF_AUTHORIZATION',
        'SF_COOKIE_SFCOMMUNITY', 'SF_COOKIE_SESSIONAPP', 'NTFY_TOPIC'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        error_msg = f"缺少环境变量: {', '.join(missing_vars)}"
        logger.error(error_msg)
        # 尝试发送错误通知
        try:
            sf_sign.send_ntfy_notification(
                "❌ SF签到配置错误", 
                error_msg, 
                "high", 
                ["warning", "rotating_light"]
            )
        except:
            pass
        return

    # 执行签到任务
    logger.info("=== 开始执行签到任务 ===")
    sign_result = sf_sign.sign_in()

    # 发送通知
    if sign_result['success']:
        sf_sign.send_ntfy_notification(
            f"🎉 SF签到 +{sign_result['voucherCount']}代券",
            sign_result['message'],
            "default",
            ["white_check_mark", "moneybag"]
        )
    else:
        sf_sign.send_ntfy_notification(
            "❌ SF签到失败",
            sign_result['message'],
            "high",
            ["x", "warning"]
        )

    logger.info("签到任务执行完成")

if __name__ == "__main__":
    main()
