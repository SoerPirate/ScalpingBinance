# Подключаемся к Binance Api
from binance.client import Client
from binance import BinanceSocketManager
from binance.enums import *
# Звуки
from playsound import playsound
# Работа с excel
import pandas as pd
# Дата + время
from datetime import datetime
# Работа со временем
import time
# Работа с вычислениями
import math

# Api key
api_key = ''
# Secret Api key
api_secret = ''
# Client
client = Client(api_key, api_secret)

# К какой монете искать пары
FIND = 'BTC'
# Сколько раз выполнять цикл 
LOOP_RANGE = 4000
# Какой процент считается СПРЕДОМ (минимум надо БОЛЬШЕ чем 0,15)
GROW_PERCENT = 0.3

files_path = ''
TIME = 3
ASSET = ''
RESULT = {}


''' ЗАПУСК '''
for z in range(LOOP_RANGE): 
    
    start_time = time.time()
    
    now = datetime.now()
    current_time = now.strftime("%D:%H:%M:%S")
    print(" =====================  " + str(z+1) + "  ================================= ")
    print("Current Time = ", current_time)

    time.sleep(TIME)
    
    ResValue = []

    try:
        tickers = client.get_orderbook_tickers()
    except Exception as e:
            print('пауза на 5 мин: ' + str(e))
            time.sleep(1500)
            continue
    
    if not RESULT:
        RESULT = {'Монета': []}
        for n in tickers:
            ASSET = n['symbol'] 
            if (ASSET.find(FIND) > 0) and (not 'UP' in ASSET) and (not 'DOWN' in ASSET) and (not 'BEAR' in ASSET) and (not 'BULL' in ASSET):
                RESULT['Монета'].append(ASSET)
                        
    for n in tickers:
        ASSET = n['symbol']
        if (ASSET.find(FIND) > 0) and (not 'UP' in ASSET) and (not 'DOWN' in ASSET) and (not 'BEAR' in ASSET) and (not 'BULL' in ASSET): 
            
            # Отсев валют с ценой 0
            ask = n['askPrice']
            bid = n['bidPrice']

            if (bid == '0.0') or (ask == '0.0'):              
                ResValue.append(0)
                continue

            ask = float(n['askPrice'])
            bid = float(n['bidPrice'])

            # Сколько нулей надо срезать с конца?
            zero_count_ask = 0
            for x in n['askPrice'][::-1]:
                if x == '0':
                    zero_count_ask+=1
                else:
                    break

            zero_count_bid = 0
            for x in n['bidPrice'][::-1]:
                if x == '0':
                    zero_count_bid+=1
                else:
                    break

            if zero_count_bid >= zero_count_ask:
                zero_count = zero_count_ask
            else:
                zero_count = zero_count_bid

            tickSize_count = 8 - zero_count

            tickSize = '0.' + '0' * (tickSize_count-1) + '1'
            tickSize = float('0.' + '0' * (tickSize_count-1) + '1')
 
            spread = ask * 100 / bid - 100

            spread_total = 0
            modify_bid = bid
            
            while True:
                modify_bid = modify_bid + tickSize
                if modify_bid >= ask:
                    break
                else:
                    spread_total +=1

            # Есть спред?                   
            if (spread > GROW_PERCENT) and (spread_total >= 2):
                ResValue.append(1)
            else:
                ResValue.append(0)

    RESULT[current_time] = ResValue
     
    df = pd.DataFrame(RESULT)
    df.to_excel(files_path + 'BTC.xlsx')     

    print("--- %s seconds ---" % (time.time() - start_time))
    print('')
    print('')
        
playsound(files_path + "zvuk-monety.mp3") 


