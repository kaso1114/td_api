# SPX option 準日交易
因為我在台灣，時間都以 台灣時間為主 (UTC+8)

台灣時間 二~六 早上3點35分 下單 明天到期的 (SPXW * 0.96)/((SPXW * 0.96)-50) 價格的 sell put spreads

選擇權的價格為當前中間價 + 0.05

## Install
### 修改為台灣時區
```bash
timedatectl
sudo timedatectl set-timezone Asia/Taipei
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

## Run Script
Run script in crontab
```bash
35 03 * * 2-6 cd /home/kaso1114/td_api/; .venv/bin/python send_spx_sp_spread.py >> log.txt 2>&1
```