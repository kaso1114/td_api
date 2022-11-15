# SPX option 準日交易
因為我在台灣 (UTC+8)，美東時間 15:35，在台灣是凌晨 03:35，在睡夢中是無法盯盤的

所以程式會在 美東時間 星期一~五 16:35 下單 明天到期的
    (SPXW * 0.96)/((SPXW * 0.96)-50) 價格的 sell put spreads 和
    (SPXW * 1.04)/((SPXW * 1.04)+50) 價格的 sell call spreads

選擇權的價格為當前 **中間價**

## Install
### 修改為美東時區
```bash
timedatectl
sudo timedatectl set-timezone America/New_York
systemctl restart cron
```

### Install td_api
```bash
sudo apt update
sudo apt install python3-pip python3.8-venv git
git clone https://github.com/kaso1114/td_api
cd td_api
python3 -m venv .venv
source .venv/bin/activate
pip install tda-api pandas
```

### Create secretsTDA file
1. 去 https://developer.tdameritrade.com/ 創建 MyApps，MyApps 的 Consumer Key 即為 **api_key**
2. **account_id** 即為 TD 官網裡的 Account number
3. 創建 secretsTDA.py 檔案到 td_api 目錄裡
4. 把你的 api_key 和 account_id 填到 secretsTDA.py
    ```
    api_key = 'ABCDABCDABCDABCDABCDABCDABCDABCD'
    account_id = 812345678
    token_path = 'token.json'
    redirect_uri = 'https://localhost'
    ```
5. 假如你有 slack webhook，可填入 URL 到 secretsTDA.py，並且 ENABLE_WEBHOOK＝True，即可每日通知結果
    ```
    webhook_url = "https://hooks.slack.com/services/
    ```

## Run Script
Run script in crontab
```bash
35 15 * * 1-5 cd /home/kaso1114/td_api/; .venv/bin/python send_daily_spx_spread.py >> log.txt 2>&1
```