import os
import time
import yaml
import requests
from seleniumbase import SB
from util.utils import setup_logger,decrypt_password,notify_feishu_bot

logger = setup_logger('/var/log/bmc_alert_fetcher.log', 1024 * 1024 * 1024, 5)
current_dir = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(current_dir, 'config')
yml_path = os.path.join(config_dir, 'bmc_info.yml')


def get_alert_info(bmc_ip,user_name,password):
    with SB() as sb:
        login_url = f"http://{bmc_ip}/#login"
        logs_url = f"http://{bmc_ip}/#logs/alertLog"
        sb.open(login_url)
        sb.js_click_if_present("#details-button")
        sb.js_click_if_present("#proceed-link")
        sb.wait_for_element_present("#userid")
        sb.type("#userid", user_name)  
        sb.type("#password", password) 
        sb.click("#btn-login")
        sb.wait_for_element_present("#download")
        seleniumbase_cookies=sb.get_cookies()
        session = requests.Session()
        for cookie in seleniumbase_cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
        current_alert_url = f"http://{bmc_ip}/#logs/alertLog"  
        response = session.get(current_alert_url,verify=False)
        if response.status_code != 200:
            logger.info(f"response content() {response.content.decode('utf-8')}")
            logger.info(f"response status_code {response.status_code}")
            return None
        sb.open(logs_url)
        sb.sleep(3)
        alert_info = sb.get_text("tbody#event-content")
        logger.info(f"BMC Alert Logs {alert_info}")
        return alert_info

def main():
    
    while True:
        try:
            with open(yml_path, 'r') as file:
                config_info = yaml.safe_load(file)
                bmc_ips = config_info["bmc_credentials"]['bmc_ips']
                user_name = config_info["bmc_credentials"]['user_name']
                key = config_info["bmc_credentials"]['key']
                logger.info(f"key: {key}")
                encrypted_password = config_info["bmc_credentials"]['encrypted_password']
                password = decrypt_password(key.encode(),encrypted_password.encode())
                for bmc_ip in bmc_ips:
                    alert_info=get_alert_info(bmc_ip,user_name,password)
                    if "no current alarms" in alert_info:
                        logger.info(f"There is no current alarms")
                    else:
                        msg =f"bmc_ip:{bmc_ip} alert_info:{alert_info}"
                        notify_feishu_bot(msg)
                    
        except Exception as e:
            logger.error(f"get_alert_info error: {e}")
        # time.sleep(1)            
        time.sleep(300)
        
        
if __name__ == "__main__":
    main()