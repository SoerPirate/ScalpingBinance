# Подключаемся к Binance Api
from binance.client import Client
from binance import BinanceSocketManager
from binance.enums import *
# Telegram bot
import telebot
# Воспроизведение звуков
from playsound import playsound
# Работа с таблицами xlsx
import pandas as pd
# Получить дату и время
from datetime import datetime
# Работа со временем
import time
# Работа с вычислениями
import math
# Многопоточность
import threading
from threading import Thread
# Логи
import logging
# GUI
from tkinter import *


# Api key
api_key = ''
# Secret Api key
api_secret = ''
# Client
client = Client(api_key, api_secret)

# API telegram
bot = telebot.TeleBot('')
# ID получателя в telegram
ID = ''

# Рынок для многопотока
ASSETS = ['HIGHBTC', 'VOXELBTC', 'ACABTC', 'SFPBTC', 'LOKABTC', 'WOOBTC', 'OGNBTC', 'DARBTC', 'SKLBTC', 'SUPERBTC',
          'FETBTC', 'ALPHABTC', 'JOEBTC', 'ROSEBTC', 'MBOXBTC', 'PORTOBTC', 'BNXBTC', 'CVXBTC', 'BONDBTC', 'DODOBTC']   
# Сумма одной сделки
ORDER_VALUE = 0.0005           
# Процент при котором будет совершена продажа (надо БОЛЬШЕ чем 0,15)
GROW_PERCENT = 0.3
# Папка со скриптом и файлами
files_path = ''      

NEED_ORDER_BOOK = False
TIME = 2
TIME_P = 600
MUSIC_PAUSE = 'end.mp3'
RESULT = {}
priceBNB = 0.0
global_work = False
global_stop = False
personal_work = {}
spred_GUI = {}
deal_count = 0
deal_zavis = 0
buy_ord_count = 0
sell_ord_count = 0
zav_pok = 0
nesmog_sell = 0


''' TG - ОТПРАВИТЬ СООБЩЕНИЕ '''
def message(text):
    bot.send_message(ID, text)

''' TG - СООБЩЕНИЕ О ПОКУПКЕ '''
def buy_message_success(ASSET, CRYPTOCURRENCY, CURRENCY)    
    # Получаем последнюю сделку из истории биржи
    data_buy = history(ASSET)[-1]
    sum_buy = data_buy['quoteQty'] 
    message('Покупка \n\nРынок: ' + data_buy['symbol'] + '\nКупленный актив: ' + data_buy['qty'] + ' ' + CRYPTOCURRENCY + '\nПроданный актив: ' + data_buy['quoteQty'] + ' ' + CURRENCY + '\nЦена на момент покупки: ' + data_buy['price'] + ' ' + CURRENCY + '\nКомиссия: ' + data_buy['commission'] + ' ' + data_buy['commissionAsset'])
    return sum_buy, data_buy

''' TG - СООБЩЕНИЕ О ПРОДАЖЕ '''                                   
def sell_message_success(ASSET, sum_buy, CRYPTOCURRENCY, CURRENCY, data_buy):
    data_sell = history(ASSET)[-1]
    sum_sell = data_sell['quoteQty']
    message('Продажа \n\nРынок: ' + data_sell['symbol'] + '\nКупленный актив: ' + data_sell['quoteQty'] + ' ' + CURRENCY + '\nПроданный актив: ' + data_sell['qty'] + ' ' + CRYPTOCURRENCY + '\nЦена на момент продажи: ' + data_sell['price'] + ' ' + CURRENCY + '\nКомиссия: ' + data_sell['commission'] + ' ' + data_sell['commissionAsset'])

    profit = float(sum_sell) - float(sum_buy)
    real_profit = profit - (float(data_sell['commission']) * priceBNB) - (float(data_buy['commission']) * priceBNB)
    real_profit_str = '{:0.0{}f}'.format(real_profit, 8)    
    message('Прибыль: ' + real_profit_str)        
    return sum_sell, data_sell, profit

''' ИНФОРМАЦИЯ О МОНЕТЕ '''
def asset_info(ASSET, CURRENCY, CRYPTOCURRENCY, minPriceCount, minQtyCount, tickSize, stepSize, QUANTITY, logger):
    # Запрос у биржи инфы про монету
    symbol_info = client.get_symbol_info(ASSET)
    logger.info(symbol_info)
    logger.info('')
    
    # Названия фиата и крипты 
    CURRENCY = symbol_info['quoteAsset']
    logger.info('Фиат: ' + CURRENCY)
    CRYPTOCURRENCY = symbol_info['baseAsset']
    logger.info('Монета: ' + CRYPTOCURRENCY)
    
    # Минимальная цена + сколько знаков после запятой               
    minPrice = symbol_info['filters'][0]['minPrice']
    logger.info('Минимальная цена: ' + minPrice)
    a, b = str(minPrice).split('.')
    c, d = str(b).split('1')
    minPriceCount = len(c)+1
    logger.info('В цене - знаков после запятой: ' + str(minPriceCount))
    
    # Минимальное количество монеты в сделке + сколько знаков после запятой
    minQty = symbol_info['filters'][2]['minQty']
    logger.info('Минимальное количество монеты в сделке : ' + minPrice)
    if float(minQty) < 1.0:
        a, b = str(minQty).split('.')
        c, d = str(b).split('1')
        minQtyCount = len(c)+1
    else:
        minQtyCount = 0
    logger.info('В количестве монеты - знаков после запятой: ' + str(minQtyCount))

    # Шаг цены
    tickSizeSTR = symbol_info['filters'][0]['tickSize']
    tickSize = float(symbol_info['filters'][0]['tickSize'])
    logger.info('Шаг цены: ' + tickSizeSTR)
    
    # Шаг количества монеты
    stepSizeSTR = symbol_info['filters'][2]['stepSize']
    stepSize = float(symbol_info['filters'][2]['stepSize']) 
    logger.info('Шаг количества монеты: ' + stepSizeSTR)

    # Текущая цена для примера ордера
    price_test = price(ASSET, minPriceCount)

    # Объем 1 сделки (в крипте)                         
    if minQtyCount == 0:
        QUANTITY = int(ORDER_VALUE / price_test)
        quantity = str(QUANTITY)
    else:
        quantity = str(ORDER_VALUE / price_test)
        a, b = quantity.split('.')
        quantity = a + '.' + b[:minQtyCount]
        QUANTITY = float(quantity)

    # Пример ордера для проверки
    logger.info('------------------------')
    logger.info('!!! Пример ордера для проверки !!!')
    logger.info('Цена: ' + str(price_test) + ' ' + CURRENCY + ' за 1 шт. ' + CRYPTOCURRENCY)
    logger.info(price_test)
    logger.info('Количество: ' + quantity + ' ' + CRYPTOCURRENCY)
    logger.info('Всего: ' + str(ORDER_VALUE) + ' ' + CURRENCY)
    logger.info('------------------------')
    logger.info('')
    return ASSET, CURRENCY, CRYPTOCURRENCY, minPriceCount, minQtyCount, tickSize, stepSize, QUANTITY
        
''' ПРОВЕРКА СПРЕДА и прочих условий для входа '''
def check_spread(ASSET, tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price, priceBuy, BUY_now, SELL_now, QUANTITY, volume_order_limit, logger):
    global spred_GUI
    
    start_time = time.time()
    
    now = datetime.now()
    current_time = now.strftime("%D:%H:%M:%S")
    
    isSpread = False

    bids_volume = 0.0
    asks_volume = 0.0
    volume_percent = 0.0

    depth_time = time.time()
    
    try:
        DEPTH = depth(ASSET, volume_order_limit)        
        if NEED_ORDER_BOOK == True:
            logger.info(DEPTH)
    except Exception as e:
        print('Ошибка запрос глубины: ' + str(e))
        logger.info('Ошибка запрос глубины: ' + str(e))
        print('нужна пауза')
        logger.info('нужна пауза')                                        
        playsound(files_path + MUSIC_PAUSE)
        time.sleep(TIME_P)
        if global_stop == True:
            return isSpread, bid
        isSpread, bid = check_spread(
                ASSET, tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price, priceBuy, BUY_now, SELL_now, QUANTITY, volume_order_limit, logger)
        return isSpread, bid
        
    logger.info('depth time')
    logger.info("--- %s seconds ---" % (time.time() - depth_time))

    try:        
        ask = float(DEPTH['asks'][0][0])   
        logger.info('нижний ордер на продажу: ' + DEPTH['asks'][0][0])
    except Exception as e:
            logger.info('Ошибка: ' + str(e))
            
    try:
        bid = float(DEPTH['bids'][0][0])   
        logger.info('верхний ордер на покупку: ' + DEPTH['bids'][0][0])
    except Exception as e:
            logger.info('Ошибка: ' + str(e))
            
    spread = ask * 100 / bid - 100    
    logger.info('спред в процентах: ' + str(spread) + ' %')

    spr_to_gui = '{:0.0{}f}'.format(spread, 4)
  
    spread_total = 0
    modify_bid = bid
    
    while True:
        modify_bid = modify_bid + tickSize
        if modify_bid >= ask:                                                       
            break
        else:
            spread_total +=1
            
    logger.info('спред в сатоши: ' + str(spread_total) + ' (должно быть >= 2 для нормальной торговли)')

    try:
        asks = DEPTH['asks']
        for x in asks:
            asks_volume = asks_volume + float(x[1])
        logger.info('объем продаж в стакане (20 ордеров): ' + str(asks_volume))
    except Exception as e:
            logger.info('Ошибка: ' + str(e))
    
    try:
        bids = DEPTH['bids']       
        if NEED_ORDER_BOOK == True:
            logger.info('BIDS')
            logger.info(bids_volume)
            for x in bids:
                logger.info(float(x[1]))
                bids_volume = bids_volume + float(x[1])
        else:
            for x in bids:
                bids_volume = bids_volume + float(x[1])                
        logger.info('объем покупок в стакане: ' + str(bids_volume))        
    except Exception as e:
            logger.info('Ошибка: ' + str(e))

    try:        
        volume_percent = (bids_volume - asks_volume) / (asks_volume / 100)
        logger.info('разница между объемами: ' + str(volume_percent) + ' %')
    except Exception as e:
            logger.info('Ошибка: ' + str(e))
    
    if (spread >= GROW_PERCENT) and (spread_total >= 2):
        if bids_volume > asks_volume:
            logger.info('                                      ' + current_time + ' - ' + spr_to_gui + ' - OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK OK')
            logger.info("--- %s seconds ---" % (time.time() - start_time))
            isSpread = True
            spred_GUI[ASSET] = spr_to_gui
        else:
            logger.info('                                      ' + current_time + ' - ' + spr_to_gui + ' - спред есть, но цена падает')
            logger.info("--- %s seconds ---" % (time.time() - start_time))
            spred_GUI[ASSET] = spr_to_gui + ' - D'
    else:
        if (spread >= GROW_PERCENT) and (spread_total < 2):
            logger.info('                                      ' + current_time + ' - ' + spr_to_gui + ' - no')
            logger.info("--- %s seconds ---" % (time.time() - start_time))
            spred_GUI[ASSET] = spr_to_gui + ' - S'
        else:    
            logger.info('                                      ' + current_time + ' - ' + spr_to_gui + ' - no')
            logger.info("--- %s seconds ---" % (time.time() - start_time))
            spred_GUI[ASSET] = spr_to_gui        
    return isSpread, bid 

''' ЦИКЛ ПОКУПКИ '''
def buy(ASSET, tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID,
        price, priceBuy, BUY_now, SELL_now, QUANTITY, volume_order_limit, minPriceCount, sum_buy, data_buy, logger, stepSize, minQtyCount, CRYPTOCURRENCY, CURRENCY):
    global spred_GUI, buy_ord_count, zav_pok

    if global_stop == True:
        return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY

    time.sleep(TIME)
    
    isSpread, bid = check_spread(
        ASSET, tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price, priceBuy, BUY_now, SELL_now, QUANTITY, volume_order_limit, logger)
    
    if global_stop == True:
        return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY
    
    if isSpread == True:
        logger.info('bid + tickSize')
        logger.info(bid)
        logger.info(tickSize)
        BT = bid + tickSize
        logger.info(BT)
        logger.info('пробуем купить')        
        price = normalized(BT, minPriceCount, logger)        
        try:
            current_order, QUANTITY = order_limit_buy(price, ASSET, QUANTITY, stepSize, logger, minQtyCount)
        except Exception as e:
            print(str(e))
            logger.info(str(e))
            print('Ошибка при покупке buy!')
            logger.info('Ошибка при покупке buy!')
            return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY               
        if not current_order == None:
            current_order_ID = current_order['orderId']
            buy_ord_count +=1
        else:
            print('ЦИКЛ ПОКУПКИ - ошибка')
            logger.info('ЦИКЛ ПОКУПКИ - ошибка')
            logger.info(QUANTITY)
            exit()
    else:
        return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY

    spred_GUI[ASSET] = 'BUY'
    
    while True:
        time.sleep(TIME)
        try:
            current_order_info = order_info(current_order_ID, ASSET)
        except Exception as e:
            print(str(e))
            logger.info(str(e))
            print('нужна пауза')
            logger.info('нужна пауза')                                       
            playsound(files_path + MUSIC_PAUSE)
            time.sleep(TIME_P)
            if global_stop == True:
                zav_pok+=1
                return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY
            continue                                                                                      
        if current_order_info['status'] == 'FILLED':                                                    
            logger.info('КУПИЛИ')
            print('BUY - ' + str(ASSET) + '\n')            
            sum_buy, data_buy = buy_message_success(ASSET, CRYPTOCURRENCY, CURRENCY)
            priceBuy = price
            BUY_now = False
            SELL_now = True
            return sum_buy, priceBuy, BUY_now, SELL_now, data_buy, QUANTITY
        elif current_order_info['status'] == 'PARTIALLY_FILLED':                             
            spred_GUI[ASSET] = 'PART BUY'
            if global_stop == True:
                zav_pok+=1
                return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY
        else:
            isSpread, bid  = check_spread(
                ASSET, tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price, priceBuy, BUY_now, SELL_now, QUANTITY, volume_order_limit, logger)
            if global_stop == True:
                logger.info('пробую отменить, тк global_stop')
                try:
                    cancel_order(ASSET, current_order_ID)
                    spred_GUI[ASSET] = 'CANCEL'
                    logger.info('CANCEL')
                    buy_ord_count -=1
                    return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY                   
                except Exception as e:
                    print('Ошибка: ' + str(e))
                    print('Нельзя отменять ордер, вероятно он уже исполнился')
                    logger.info('Нельзя отменять ордер, вероятно он уже исполнился - global_stop')
                    spred_GUI[ASSET] = 'BUY'
                    print('BUY - ' + str(ASSET) + '\n')                    
                    sum_buy, data_buy = buy_message_success(ASSET, CRYPTOCURRENCY, CURRENCY)
                    priceBuy = price
                    BUY_now = False
                    SELL_now = True
                    return sum_buy, priceBuy, BUY_now, SELL_now, data_buy, QUANTITY
            if isSpread == False:
                try:
                    cancel_order(ASSET, current_order_ID)
                    spred_GUI[ASSET] = 'CANCEL'
                    logger.info('CANCEL')
                    buy_ord_count -=1
                    return 0.0, 0.0, BUY_now, SELL_now, [], QUANTITY                   
                except Exception as e:
                    print('Ошибка: ' + str(e))
                    print('Нельзя отменять ордер, вероятно он уже исполнился - isSpread')
                    logger.info('Нельзя отменять ордер, вероятно он уже исполнился - isSpread')
                    spred_GUI[ASSET] = 'BUY'
                    print('BUY - ' + str(ASSET) + '\n')
                    sum_buy, data_buy = buy_message_success(ASSET, CRYPTOCURRENCY, CURRENCY)
                    priceBuy = price
                    BUY_now = False
                    SELL_now = True
                    return sum_buy, priceBuy, BUY_now, SELL_now, data_buy, QUANTITY
            else:
                spred_GUI[ASSET] = 'BUY'

''' ЦИКЛ ПРОДАЖИ '''
def sell(tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price, BUY_now, SELL_now,
         QUANTITY, priceBuy, minPriceCount, ASSET, profit, sum_buy, sum_sell, data_sell, data_buy, logger, CRYPTOCURRENCY, CURRENCY):
    global spred_GUI, deal_count, deal_zavis, sell_ord_count, nesmog_sell
    
    logger.info('начали продажу')
    
    price = normalized((float(priceBuy) * (100 + GROW_PERCENT) / 100), minPriceCount, logger)                      

    try:
        current_order = order_limit_sell(price, ASSET, QUANTITY, logger)
    except Exception as e:
        print(str(e))
        logger.info(str(e))
        print('Ошибка при покупке sell!')
        logger.info('Ошибка при покупке sell!')
        if global_stop == True:
            nesmog_sell+=1
            return 0, price, BUY_now, SELL_now, []                                                        
        profit, price, BUY_now, SELL_now, data_sell = sell(
                tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price,
                BUY_now, SELL_now, QUANTITY, priceBuy, minPriceCount, ASSET, profit, sum_buy, sum_sell, data_sell, data_buy, logger, CRYPTOCURRENCY, CURRENCY)
        return profit, price, BUY_now, SELL_now, data_sell                     
                
    if not current_order == None:
        current_order_ID = current_order['orderId']
        sell_ord_count+=1
        deal_zavis+=1
    else:
        print('сделка меньше чем 10$')
        exit()

    spred_GUI[ASSET] = 'SELL'
    
    while True:
        if global_stop == True:
            return 0, price, BUY_now, SELL_now, [] 
        time.sleep(TIME)
        try:
            current_order_info = order_info(current_order_ID, ASSET)
        except Exception as e:
            print(str(e))
            logger.info(str(e))
            print('нужна пауза')
            logger.info('нужна пауза')                                      
            playsound(files_path + MUSIC_PAUSE)
            time.sleep(TIME_P)
            continue                                                                   
        if current_order_info['status'] == 'FILLED':
            print('SELL - ' + str(ASSET) + '\n')            
            deal_count+=1
            deal_zavis-=1
            sum_sell, data_sell, profit = sell_message_success(ASSET, sum_buy, CRYPTOCURRENCY, CURRENCY, data_buy)
            BUY_now = True
            SELL_now = False
            return profit, price, BUY_now, SELL_now, data_sell        

''' ИСТОРИЯ СДЕЛОК '''
def history(symbol):
    history = client.get_my_trades(symbol=symbol)
    return history

''' ЗАПРОСИТЬ ЦЕНУ У БИРЖИ '''
def price(symbol, minPriceCount):
    price = client.get_symbol_ticker(symbol=symbol)['price']
    a, b = price.split('.')
    normPrice = a + '.' + b[:minPriceCount]
    return float(normPrice)

''' ЗАПРОСИТЬ ЦЕНУ BNB У БИРЖИ '''
def priceBNB():
    priceBNB = client.get_symbol_ticker(symbol='BNBBTC')['price']
    return float(priceBNB)

''' ПРИВЕСТИ ЦЕНУ К НОРМАЛЬНОМУ ФОРМАТУ '''
def normalized(badPrice, minPriceCount, logger):
    price_str = '{:0.0{}f}'.format(badPrice, minPriceCount)
    logger.info('ПРИВЕСТИ ЦЕНУ К НОРМАЛЬНОМУ ФОРМАТУ')
    logger.info(price_str)
    return price_str                                  

''' ОРДЕР ПОКУПКА '''
def order_limit_buy(PRICE, ASSET, QUANTITY, stepSize, logger, minQtyCount): 
    global spred_GUI, personal_work
    
    f_price = float(PRICE)
    
    if QUANTITY * f_price > ORDER_VALUE:
        try:
            order = client.order_limit_buy(
            symbol = ASSET,
            quantity = QUANTITY,
            price = PRICE)
        except Exception as e:
            logger.info('внутри order_limit_buy')
            logger.info(str(e))
            logger.info(PRICE)
            if str(e) == 'APIError(code=-1111): Precision is over the maximum defined for this asset.':
                print('ошибка в количестве знаков после запятой')
                logger.info('ошибка в количестве знаков после запятой')
                exit()
            elif str(e) == 'APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server\'s time.':
                print('ошибка c синхронизацией времени в windows - ' + ASSET)
                logger.info('ошибка c синхронизацией времени в windows')
                personal_work[ASSET] = False               
            elif 'Max retries exceeded with url' in str(e):
                print('нужна пауза')
                logger.info('нужна пауза')                                        
                playsound(files_path + MUSIC_PAUSE)
                time.sleep(TIME_P)
    else:
        logger.info(PRICE)
        logger.info(ORDER_VALUE)
        logger.info('сделка меньше чем 10$, пересчет QUANTITY')        
        while QUANTITY * f_price <= ORDER_VALUE:
            QUANTITY = QUANTITY + stepSize
            logger.info(QUANTITY)
        if minQtyCount == 0:
            quant = int(QUANTITY)               
            QUANTITY = quant
        else:
            quant = round(QUANTITY, minQtyCount)
            QUANTITY = quant           
        logger.info(QUANTITY)        
        try:
            order = client.order_limit_buy(
            symbol = ASSET,
            quantity = QUANTITY,
            price = PRICE)
        except Exception as e:
            logger.info('внутри order_limit_buy после пересчета QUANTITY')
            logger.info(str(e))
            logger.info(PRICE)
            if str(e) == 'APIError(code=-1111): Precision is over the maximum defined for this asset.':
                print('ошибка в количестве знаков после запятой - ' + ASSET)
                logger.info('ошибка в количестве знаков после запятой')
                exit()
            if str(e) == 'APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server\'s time.':
                print('ошибка c временем в windows - ' + ASSET)
                logger.info('ошибка c временем в windows')
                personal_work[ASSET] = False                
            if 'Max retries exceeded with url' in str(e):
                print('нужна пауза')
                logger.info('нужна пауза')                                          
                playsound(files_path + MUSIC_PAUSE)
                time.sleep(TIME_P)            
    return order, QUANTITY

''' ОРДЕР ПРОДАЖА '''
def order_limit_sell(PRICE, ASSET, QUANTITY, logger):
    global spred_GUI
    
    logger.info('ордер на продажу')
    
    f_price = float(PRICE)
    
    logger.info(PRICE)
    logger.info(f_price)
    logger.info(QUANTITY)
    
    if QUANTITY * f_price > ORDER_VALUE:
        try:
            order = client.order_limit_sell(
            symbol = ASSET,
            quantity = QUANTITY,
            price = PRICE)
        except Exception as e:
            if str(e) == 'APIError(code=-1111): Precision is over the maximum defined for this asset.':
                print('ошибка в количестве знаков после запятой - ' + ASSET)
                logger.info('ошибка в количестве знаков после запятой')
                playsound(files_path + MUSIC_PAUSE)
                exit()                                                         
            if 'Max retries exceeded with url' in str(e):
                print('нужна пауза')
                logger.info('нужна пауза')                                         
                playsound(files_path + MUSIC_PAUSE)
                time.sleep(TIME_P)
    else:
        try:
            logger.info('ошибка с числом QUANTITY')
            order = client.order_limit_sell(
            symbol = ASSET,
            quantity = QUANTITY,
            price = PRICE)
        except Exception as e:
            if str(e) == 'APIError(code=-1111): Precision is over the maximum defined for this asset.':
                print('ошибка в количестве знаков после запятой - ' + ASSET)
                logger.info('ошибка в количестве знаков после запятой')
                playsound(files_path + MUSIC_PAUSE)
                exit()                                                          
            if 'Max retries exceeded with url' in str(e):
                print('нужна пауза')
                logger.info('нужна пауза')                                        
                playsound(files_path + MUSIC_PAUSE)
                time.sleep(TIME_P)
    return order

''' СТАТУС ОРДЕРА '''
def order_info(current_order_ID, ASSET):
    order_info = client.get_order(
    symbol = ASSET,
    orderId = current_order_ID)
    return order_info

''' ОТМЕНА ОРДЕРА '''
def cancel_order(symbol, orderId):
    result = client.cancel_order(
    symbol=symbol,
    orderId=orderId)

''' СТАКАН '''
def depth(symbol, limit):
    depth = client.get_order_book(
    symbol=symbol,
    limit=limit)
    return depth

''' ОДИН ПОТОК '''
class MyThread(Thread):
    
    ## Инициализация потока ##
    def __init__(self, name, client):
        Thread.__init__(self)
        self.name = name
        self.client = client
        
    ## Запуск потока ##
    def run(self):
        ASSET = self.name
        client = self.client

        CURRENCY = ''
        CRYPTOCURRENCY = ''
        QUANTITY = 0.0
        current_order_ID = ''
        minPriceCount = 0
        minQtyCount = 0
        priceNormalized = 0.0
        # Сколько ордеров берем при анализе объемов                                                    
        volume_order_limit = 100
        bids_volume = 0.0
        asks_volume = 0.0
        BUY_now = True
        SELL_now = False
        tickSize = 0.0
        stepSize = 0.0
        isSpread = False
        # Верхний ордер покупки
        bid = 0.0
        # Нижний ордер продажи
        ask = 0.0
        # Спред в процентах (должно быть >= GROW_PERCENT)
        spread = 0.0
        # Спред в сатоши (должно быть >= 2)
        spread_total = 0
        # Разница в объемах (если положительная, то покупок больше чем продаж)
        volume_percent = 0.0
        price = 0.0
        priceBuy = ''                                
        data_buy = []
        data_sell = []
        sum_buy = 0.0
        sum_sell = 0.0
        profit = 0.0
        commissionBTC_BUY = 0.0
        commissionBTC_SELL = 0.0   
        # Логи                                      
        logger = logging.getLogger(ASSET)
        logger.setLevel(logging.INFO)        
        
        fh = logging.FileHandler(ASSET + ".log", mode='w')
     
        formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s')
        fh.setFormatter(formatter)
        
        logger.addHandler(fh)
        
        ASSET, CURRENCY, CRYPTOCURRENCY, minPriceCount, minQtyCount, tickSize, stepSize, QUANTITY = asset_info(
            ASSET, CURRENCY, CRYPTOCURRENCY, minPriceCount, minQtyCount, tickSize, stepSize, QUANTITY, logger)

        while True:    
            if BUY_now == True:             
                sum_buy, priceBuy, BUY_now, SELL_now, data_buy, QUANTITY = buy(
                    ASSET, tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price, priceBuy,
                    BUY_now, SELL_now, QUANTITY, volume_order_limit, minPriceCount, sum_buy, data_buy, logger, stepSize, minQtyCount, CRYPTOCURRENCY, CURRENCY)
            if SELL_now == True:
                profit, price, BUY_now, SELL_now, data_sell = sell(
                    tickSize, isSpread, bid, ask, spread, spread_total, bids_volume, asks_volume, current_order_ID, price,
                    BUY_now, SELL_now, QUANTITY, priceBuy, minPriceCount, ASSET, profit, sum_buy, sum_sell, data_sell, data_buy, logger, CRYPTOCURRENCY, CURRENCY)
                if global_stop == True:
                    break
                playsound(files_path + "zvuk-monety.mp3")                      

                logger.info('priceBNB')
                logger.info(priceBNB)
                
                RESULT['Монета'].append(ASSET)

                RESULT['Цена BUY'].append(priceBuy)
                RESULT['Количество'].append(QUANTITY)
                RESULT['Сумма в $'].append(data_buy['quoteQty'])
                RESULT['Комиссия'].append(data_buy['commission'])
                
                commissionBTC_BUY = float(data_buy['commission']) * priceBNB
                commissionBTC_BUY_str = '{:0.0{}f}'.format(commissionBTC_BUY, 8)
                logger.info('commissionBTC_BUY')
                logger.info(commissionBTC_BUY)
                logger.info(commissionBTC_BUY_str)

                RESULT['Комиссия BTC'].append(commissionBTC_BUY_str) 
                
                RESULT['space'].append(' ')
                
                RESULT['Цена SELL'].append(price)
                RESULT['Количество S'].append(QUANTITY)
                RESULT['Сумма в $ S'].append(data_sell['quoteQty'])
                RESULT['Комиссия S'].append(data_sell['commission'])

                commissionBTC_SELL = float(data_sell['commission']) * priceBNB
                commissionBTC_SELL_str = '{:0.0{}f}'.format(commissionBTC_SELL, 8)
                logger.info('commissionBTC_SELL')
                logger.info(commissionBTC_SELL)
                logger.info(commissionBTC_SELL_str)

                RESULT['Комиссия S BTC'].append(commissionBTC_SELL_str) 

                RESULT['пробел'].append(' ')

                profit_str = '{:0.0{}f}'.format(profit, 8)

                RESULT['Прибыль'].append(profit_str)           
                
                FIN = profit - commissionBTC_BUY - commissionBTC_SELL
                FIN_str = '{:0.0{}f}'.format(FIN, 8)

                RESULT['FIN'].append(FIN_str)
     
                df = pd.DataFrame(RESULT)
                df.to_excel(files_path + 'scalp.xlsx')
                
                logger.info("ШАЛОСТЬ УДАЛАСЬ - " + ASSET)

                print('При ставке ' + str(ORDER_VALUE) + ' было выполнено сделок: ' + str(deal_count))
                print('Зависло: ' + str(deal_zavis) + '\n')
            
            if (global_work == True) or (global_stop == True):                          
                spred_GUI[ASSET] = 'x'
                break
            if personal_work[ASSET] == False:             
                spred_GUI[ASSET] = 'PAUSE'  
                while personal_work[ASSET] == False:      
                    time.sleep(TIME)
                    if (global_work == True) or (global_stop == True):                          
                        break
                    
''' ЗАПУСК '''
# Цена BNB для пересчета комиссий
priceBNB = priceBNB()

# Подготовить табличку excel
RESULT = {'Монета': [], 'Цена BUY': [], 'Количество': [], 'Сумма в $': [], 'Комиссия': [], 'Комиссия BTC': [], 'space': [],
          'Цена SELL': [], 'Количество S': [], 'Сумма в $ S': [], 'Комиссия S': [], 'Комиссия S BTC': [], 'пробел': [], 'Прибыль': [], 'FIN': []}

# Снять с паузы каждую пару
for i in ASSETS:
    personal_work[i] = True

# Основной лог, куда пишем количество сделок
logger = logging.getLogger('0main')
logger.setLevel(logging.INFO)        
fh = logging.FileHandler("0main.log")
formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
    
''' GUI '''
def prescript():
    global spred_GUI
    
    root = Tk()
    root.title("Скальпер")
    root.geometry('700x500')
    root.attributes("-alpha", 0.9)

    ## Управление флагами ##
    def global_stop():
        global global_stop
        if python_lang00.get():
            global_stop = True           
        else:
            global_stop = False
        print('global_stop')
        
    def yes_or_no1():
        global personal_work
        if python_lang.get():
            lbl1['text'] = 'yes'
            personal_work[ASSETS[0]] = True            
        else:
            lbl1['text'] = 'no'
            personal_work[ASSETS[0]] = False
            
    def yes_or_no2():
        global personal_work
        if python_lang2.get():
            lbl2['text'] = 'yes'
            personal_work[ASSETS[1]] = True            
        else:
            lbl2['text'] = 'no'
            personal_work[ASSETS[1]] = False
            
    def yes_or_no3():
        global personal_work
        if python_lang3.get():
            lbl3['text'] = 'yes'
            personal_work[ASSETS[2]] = True            
        else:
            lbl3['text'] = 'no'
            personal_work[ASSETS[2]] = False

    def yes_or_no4():
        global personal_work
        if python_lang4.get():
            lbl4['text'] = 'yes'
            personal_work[ASSETS[3]] = True           
        else:
            lbl4['text'] = 'no'
            personal_work[ASSETS[3]] = False

    def yes_or_no5():
        global personal_work
        if python_lang5.get():
            lbl5['text'] = 'yes'
            personal_work[ASSETS[4]] = True            
        else:
            lbl5['text'] = 'no'
            personal_work[ASSETS[4]] = False

    def yes_or_no6():
        global personal_work
        if python_lang6.get():
            lbl6['text'] = 'yes'
            personal_work[ASSETS[5]] = True            
        else:
            lbl6['text'] = 'no'
            personal_work[ASSETS[5]] = False

    def yes_or_no7():
        global personal_work
        if python_lang7.get():
            lbl7['text'] = 'yes'
            personal_work[ASSETS[6]] = True            
        else:
            lbl7['text'] = 'no'
            personal_work[ASSETS[6]] = False

    def yes_or_no8():
        global personal_work
        if python_lang8.get():
            lbl8['text'] = 'yes'
            personal_work[ASSETS[7]] = True            
        else:
            lbl8['text'] = 'no'
            personal_work[ASSETS[7]] = False

    def yes_or_no9():
        global personal_work
        if python_lang9.get():
            lbl9['text'] = 'yes'
            personal_work[ASSETS[8]] = True            
        else:
            lbl9['text'] = 'no'
            personal_work[ASSETS[8]] = False

    def yes_or_no10():
        global personal_work
        if python_lang10.get():
            lbl10['text'] = 'yes'
            personal_work[ASSETS[9]] = True           
        else:
            lbl10['text'] = 'no'
            personal_work[ASSETS[9]] = False

    def yes_or_no11():
        global personal_work
        if python_lang11.get():
            lbl11['text'] = 'yes'
            personal_work[ASSETS[10]] = True            
        else:
            lbl11['text'] = 'no'
            personal_work[ASSETS[10]] = False
            
    def yes_or_no12():
        global personal_work
        if python_lang12.get():
            lbl12['text'] = 'yes'
            personal_work[ASSETS[11]] = True            
        else:
            lbl12['text'] = 'no'
            personal_work[ASSETS[11]] = False
            
    def yes_or_no13():
        global personal_work
        if python_lang13.get():
            lbl13['text'] = 'yes'
            personal_work[ASSETS[12]] = True            
        else:
            lbl13['text'] = 'no'
            personal_work[ASSETS[12]] = False

    def yes_or_no14():
        global personal_work
        if python_lang14.get():
            lbl14['text'] = 'yes'
            personal_work[ASSETS[13]] = True            
        else:
            lbl14['text'] = 'no'
            personal_work[ASSETS[13]] = False

    def yes_or_no15():
        global personal_work
        if python_lang15.get():
            lbl15['text'] = 'yes'
            personal_work[ASSETS[14]] = True           
        else:
            lbl15['text'] = 'no'
            personal_work[ASSETS[14]] = False

    def yes_or_no16():
        global personal_work
        if python_lang16.get():
            lbl16['text'] = 'yes'
            personal_work[ASSETS[15]] = True            
        else:
            lbl16['text'] = 'no'
            personal_work[ASSETS[15]] = False

    def yes_or_no17():
        global personal_work
        if python_lang17.get():
            lbl17['text'] = 'yes'
            personal_work[ASSETS[16]] = True           
        else:
            lbl17['text'] = 'no'
            personal_work[ASSETS[16]] = False

    def yes_or_no18():
        global personal_work
        if python_lang18.get():
            lbl18['text'] = 'yes'
            personal_work[ASSETS[17]] = True            
        else:
            lbl18['text'] = 'no'
            personal_work[ASSETS[17]] = False

    def yes_or_no19():
        global personal_work
        if python_lang19.get():
            lbl19['text'] = 'yes'
            personal_work[ASSETS[18]] = True            
        else:
            lbl19['text'] = 'no'
            personal_work[ASSETS[18]] = False

    def yes_or_no20():
        global personal_work
        if python_lang20.get():
            lbl20['text'] = 'yes'
            personal_work[ASSETS[19]] = True            
        else:
            lbl20['text'] = 'no'
            personal_work[ASSETS[19]] = False
            
    ## Обновление спреда ##
    def tick1():
        lbl1.after(200, tick1)
        try:
            lbl1['text'] = spred_GUI[ASSETS[0]]
            if spred_GUI[ASSETS[0]] == 'BUY':
                lbl1['bg'] = 'green'
            elif spred_GUI[ASSETS[0]] == 'SELL':
                lbl1['bg'] = 'red'
            elif spred_GUI[ASSETS[0]] == 'CANCEL':
                lbl1['bg'] = 'yellow' 
            elif spred_GUI[ASSETS[0]] == 'PART BUY':
                lbl1['bg'] = 'blue'
            else:
                lbl1['bg'] = 'white'
        except Exception as e:
            lbl1['text'] = 'x'

    def tick2():
        lbl2.after(200, tick2)
        try:
            lbl2['text'] = spred_GUI[ASSETS[1]]
            if spred_GUI[ASSETS[1]] == 'BUY':
                lbl2['bg'] = 'green'
            elif spred_GUI[ASSETS[1]] == 'SELL':
                lbl2['bg'] = 'red'
            elif spred_GUI[ASSETS[1]] == 'CANCEL':
                lbl2['bg'] = 'yellow'
            elif spred_GUI[ASSETS[1]] == 'PART BUY':
                lbl2['bg'] = 'blue'                
            else:
                lbl2['bg'] = 'white'
        except Exception as e:
            lbl2['text'] = 'x'

    def tick3():
        lbl3.after(200, tick3)
        try:
            lbl3['text'] = spred_GUI[ASSETS[2]]
            if spred_GUI[ASSETS[2]] == 'BUY':
                lbl3['bg'] = 'green'
            elif spred_GUI[ASSETS[2]] == 'SELL':
                lbl3['bg'] = 'red'
            elif spred_GUI[ASSETS[2]] == 'CANCEL':
                lbl3['bg'] = 'yellow'
            elif spred_GUI[ASSETS[2]] == 'PART BUY':
                lbl3['bg'] = 'blue'
            else:
                lbl3['bg'] = 'white'
        except Exception as e:
            lbl3['text'] = 'x'

    def tick4():
        lbl4.after(200, tick4)
        try:
            lbl4['text'] = spred_GUI[ASSETS[3]]
            if spred_GUI[ASSETS[3]] == 'BUY':
                lbl4['bg'] = 'green'
            elif spred_GUI[ASSETS[3]] == 'SELL':
                lbl4['bg'] = 'red'
            elif spred_GUI[ASSETS[3]] == 'CANCEL':
                lbl4['bg'] = 'yellow'
            elif spred_GUI[ASSETS[3]] == 'PART BUY':
                lbl4['bg'] = 'blue'                
            else:
                lbl4['bg'] = 'white'
        except Exception as e:
            lbl4['text'] = 'x'

    def tick5():
        lbl5.after(200, tick5)
        try:
            lbl5['text'] = spred_GUI[ASSETS[4]]
            if spred_GUI[ASSETS[4]] == 'BUY':
                lbl5['bg'] = 'green'
            elif spred_GUI[ASSETS[4]] == 'SELL':
                lbl5['bg'] = 'red'
            elif spred_GUI[ASSETS[4]] == 'CANCEL':
                lbl5['bg'] = 'yellow'
            elif spred_GUI[ASSETS[4]] == 'PART BUY':
                lbl5['bg'] = 'blue'                
            else:
                lbl5['bg'] = 'white'
        except Exception as e:
            lbl5['text'] = 'x'

    def tick6():
        lbl6.after(200, tick6)
        try:
            lbl6['text'] = spred_GUI[ASSETS[5]]
            if spred_GUI[ASSETS[5]] == 'BUY':
                lbl6['bg'] = 'green'
            elif spred_GUI[ASSETS[5]] == 'SELL':
                lbl6['bg'] = 'red'
            elif spred_GUI[ASSETS[5]] == 'CANCEL':
                lbl6['bg'] = 'yellow'
            elif spred_GUI[ASSETS[5]] == 'PART BUY':
                lbl6['bg'] = 'blue'                
            else:
                lbl6['bg'] = 'white'
        except Exception as e:
            lbl6['text'] = 'x'

    def tick7():
        lbl7.after(200, tick7)
        try:
            lbl7['text'] = spred_GUI[ASSETS[6]]
            if spred_GUI[ASSETS[6]] == 'BUY':
                lbl7['bg'] = 'green'
            elif spred_GUI[ASSETS[6]] == 'SELL':
                lbl7['bg'] = 'red'
            elif spred_GUI[ASSETS[6]] == 'CANCEL':
                lbl7['bg'] = 'yellow'
            elif spred_GUI[ASSETS[6]] == 'PART BUY':
                lbl7['bg'] = 'blue'                
            else:
                lbl7['bg'] = 'white'
        except Exception as e:
            lbl7['text'] = 'x'

    def tick8():
        lbl8.after(200, tick8)
        try:
            lbl8['text'] = spred_GUI[ASSETS[7]]
            if spred_GUI[ASSETS[7]] == 'BUY':
                lbl8['bg'] = 'green'
            elif spred_GUI[ASSETS[7]] == 'SELL':
                lbl8['bg'] = 'red'
            elif spred_GUI[ASSETS[7]] == 'CANCEL':
                lbl8['bg'] = 'yellow'
            elif spred_GUI[ASSETS[7]] == 'PART BUY':
                lbl8['bg'] = 'blue'                
            else:
                lbl8['bg'] = 'white'
        except Exception as e:
            lbl8['text'] = 'x'

    def tick9():
        lbl9.after(200, tick9)
        try:
            lbl9['text'] = spred_GUI[ASSETS[8]]
            if spred_GUI[ASSETS[8]] == 'BUY':
                lbl9['bg'] = 'green'
            elif spred_GUI[ASSETS[8]] == 'SELL':
                lbl9['bg'] = 'red'
            elif spred_GUI[ASSETS[8]] == 'CANCEL':
                lbl9['bg'] = 'yellow'
            elif spred_GUI[ASSETS[8]] == 'PART BUY':
                lbl9['bg'] = 'blue'                
            else:
                lbl9['bg'] = 'white'
        except Exception as e:
            lbl9['text'] = 'x'

    def tick10():
        lbl10.after(200, tick10)
        try:
            lbl10['text'] = spred_GUI[ASSETS[9]]
            if spred_GUI[ASSETS[9]] == 'BUY':
                lbl10['bg'] = 'green'
            elif spred_GUI[ASSETS[9]] == 'SELL':
                lbl10['bg'] = 'red'
            elif spred_GUI[ASSETS[9]] == 'CANCEL':
                lbl10['bg'] = 'yellow'
            elif spred_GUI[ASSETS[9]] == 'PART BUY':
                lbl10['bg'] = 'blue'                
            else:
                lbl10['bg'] = 'white'
        except Exception as e:
            lbl10['text'] = 'x'
            
    def tick11():
        lbl11.after(200, tick11)
        try:
            lbl11['text'] = spred_GUI[ASSETS[10]]
            if spred_GUI[ASSETS[10]] == 'BUY':
                lbl11['bg'] = 'green'
            elif spred_GUI[ASSETS[10]] == 'SELL':
                lbl11['bg'] = 'red'
            elif spred_GUI[ASSETS[10]] == 'CANCEL':
                lbl11['bg'] = 'yellow' 
            elif spred_GUI[ASSETS[10]] == 'PART BUY':
                lbl11['bg'] = 'blue'
            else:
                lbl11['bg'] = 'white'
        except Exception as e:
            lbl11['text'] = 'x'

    def tick12():
        lbl12.after(200, tick12)
        try:
            lbl12['text'] = spred_GUI[ASSETS[11]]
            if spred_GUI[ASSETS[11]] == 'BUY':
                lbl12['bg'] = 'green'
            elif spred_GUI[ASSETS[11]] == 'SELL':
                lbl12['bg'] = 'red'
            elif spred_GUI[ASSETS[11]] == 'CANCEL':
                lbl12['bg'] = 'yellow'
            elif spred_GUI[ASSETS[11]] == 'PART BUY':
                lbl12['bg'] = 'blue'                
            else:
                lbl12['bg'] = 'white'
        except Exception as e:
            lbl12['text'] = 'x'

    def tick13():
        lbl13.after(200, tick13)
        try:
            lbl13['text'] = spred_GUI[ASSETS[12]]
            if spred_GUI[ASSETS[12]] == 'BUY':
                lbl13['bg'] = 'green'
            elif spred_GUI[ASSETS[12]] == 'SELL':
                lbl13['bg'] = 'red'
            elif spred_GUI[ASSETS[12]] == 'CANCEL':
                lbl13['bg'] = 'yellow'
            elif spred_GUI[ASSETS[12]] == 'PART BUY':
                lbl13['bg'] = 'blue'
            else:
                lbl13['bg'] = 'white'
        except Exception as e:
            lbl13['text'] = 'x'

    def tick14():
        lbl14.after(200, tick14)
        try:
            lbl14['text'] = spred_GUI[ASSETS[13]]
            if spred_GUI[ASSETS[13]] == 'BUY':
                lbl14['bg'] = 'green'
            elif spred_GUI[ASSETS[13]] == 'SELL':
                lbl14['bg'] = 'red'
            elif spred_GUI[ASSETS[13]] == 'CANCEL':
                lbl14['bg'] = 'yellow'
            elif spred_GUI[ASSETS[13]] == 'PART BUY':
                lbl14['bg'] = 'blue'                
            else:
                lbl14['bg'] = 'white'
        except Exception as e:
            lbl14['text'] = 'x'

    def tick15():
        lbl15.after(200, tick15)
        try:
            lbl15['text'] = spred_GUI[ASSETS[14]]
            if spred_GUI[ASSETS[14]] == 'BUY':
                lbl15['bg'] = 'green'
            elif spred_GUI[ASSETS[14]] == 'SELL':
                lbl15['bg'] = 'red'
            elif spred_GUI[ASSETS[14]] == 'CANCEL':
                lbl15['bg'] = 'yellow'
            elif spred_GUI[ASSETS[14]] == 'PART BUY':
                lbl15['bg'] = 'blue'                
            else:
                lbl15['bg'] = 'white'
        except Exception as e:
            lbl15['text'] = 'x'

    def tick16():
        lbl16.after(200, tick16)
        try:
            lbl16['text'] = spred_GUI[ASSETS[15]]
            if spred_GUI[ASSETS[15]] == 'BUY':
                lbl16['bg'] = 'green'
            elif spred_GUI[ASSETS[15]] == 'SELL':
                lbl16['bg'] = 'red'
            elif spred_GUI[ASSETS[15]] == 'CANCEL':
                lbl16['bg'] = 'yellow'
            elif spred_GUI[ASSETS[15]] == 'PART BUY':
                lbl16['bg'] = 'blue'                
            else:
                lbl16['bg'] = 'white'
        except Exception as e:
            lbl16['text'] = 'x'

    def tick17():
        lbl17.after(200, tick17)
        try:
            lbl17['text'] = spred_GUI[ASSETS[16]]
            if spred_GUI[ASSETS[16]] == 'BUY':
                lbl17['bg'] = 'green'
            elif spred_GUI[ASSETS[16]] == 'SELL':
                lbl17['bg'] = 'red'
            elif spred_GUI[ASSETS[16]] == 'CANCEL':
                lbl17['bg'] = 'yellow'
            elif spred_GUI[ASSETS[16]] == 'PART BUY':
                lbl17['bg'] = 'blue'                
            else:
                lbl17['bg'] = 'white'
        except Exception as e:
            lbl17['text'] = 'x'

    def tick18():
        lbl18.after(200, tick18)
        try:
            lbl18['text'] = spred_GUI[ASSETS[17]]
            if spred_GUI[ASSETS[17]] == 'BUY':
                lbl18['bg'] = 'green'
            elif spred_GUI[ASSETS[17]] == 'SELL':
                lbl18['bg'] = 'red'
            elif spred_GUI[ASSETS[17]] == 'CANCEL':
                lbl18['bg'] = 'yellow'
            elif spred_GUI[ASSETS[17]] == 'PART BUY':
                lbl18['bg'] = 'blue'                
            else:
                lbl18['bg'] = 'white'
        except Exception as e:
            lbl18['text'] = 'x'

    def tick19():
        lbl19.after(200, tick19)
        try:
            lbl19['text'] = spred_GUI[ASSETS[18]]
            if spred_GUI[ASSETS[18]] == 'BUY':
                lbl19['bg'] = 'green'
            elif spred_GUI[ASSETS[18]] == 'SELL':
                lbl19['bg'] = 'red'
            elif spred_GUI[ASSETS[18]] == 'CANCEL':
                lbl19['bg'] = 'yellow'
            elif spred_GUI[ASSETS[18]] == 'PART BUY':
                lbl19['bg'] = 'blue'                
            else:
                lbl19['bg'] = 'white'
        except Exception as e:
            lbl19['text'] = 'x'

    def tick20():
        lbl20.after(200, tick20)
        try:
            lbl20['text'] = spred_GUI[ASSETS[19]]
            if spred_GUI[ASSETS[19]] == 'BUY':
                lbl20['bg'] = 'green'
            elif spred_GUI[ASSETS[19]] == 'SELL':
                lbl20['bg'] = 'red'
            elif spred_GUI[ASSETS[19]] == 'CANCEL':
                lbl20['bg'] = 'yellow'
            elif spred_GUI[ASSETS[19]] == 'PART BUY':
                lbl20['bg'] = 'blue'                
            else:
                lbl20['bg'] = 'white'
        except Exception as e:
            lbl20['text'] = 'x'

    ## Создать элементы GUI ##
    python_lang00 = BooleanVar() 
    python_lang00.set(False)
    python_checkbutton00 = Checkbutton(text='ВЫКЛЮЧИТЬ', variable=python_lang00, onvalue=True, offvalue=False, padx=15, pady=10, command=global_stop)
    python_checkbutton00.grid(row=0, column=3)

    try:
        python_lang = BooleanVar() 
        python_lang.set(True)
        python_checkbutton = Checkbutton(text=ASSETS[0], variable=python_lang, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no1)
        python_checkbutton.grid(row=1, column=1)
        lbl1 = Label(text='0.0', bg='white', width=15) 
        lbl1.grid(row=1, column=2)
    except Exception as e:
        print('не рисуем - 1')
 
    try:
        python_lang2 = BooleanVar() 
        python_lang2.set(True)
        python_checkbutton2 = Checkbutton(text=ASSETS[1], variable=python_lang2, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no2)
        python_checkbutton2.grid(row=2, column=1)
        lbl2 = Label(text='0.0', bg='white', width=15) 
        lbl2.grid(row=2, column=2)
    except Exception as e:
        print('не рисуем - 2')

    try:
        python_lang3 = BooleanVar() 
        python_lang3.set(True)
        python_checkbutton3 = Checkbutton(text=ASSETS[2], variable=python_lang3, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no3)
        python_checkbutton3.grid(row=3, column=1)
        lbl3 = Label(text='0.0', bg='white', width=15) 
        lbl3.grid(row=3, column=2)
    except Exception as e:
        print('не рисуем - 3')

    try:
        python_lang4 = BooleanVar() 
        python_lang4.set(True)
        python_checkbutton4 = Checkbutton(text=ASSETS[3], variable=python_lang4, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no4)
        python_checkbutton4.grid(row=4, column=1)
        lbl4 = Label(text='0.0', bg='white', width=15) 
        lbl4.grid(row=4, column=2)
    except Exception as e:
        print('не рисуем - 4')

    try:
        python_lang5 = BooleanVar() 
        python_lang5.set(True)
        python_checkbutton5 = Checkbutton(text=ASSETS[4], variable=python_lang5, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no5)
        python_checkbutton5.grid(row=5, column=1)
        lbl5 = Label(text='0.0', bg='white', width=15) 
        lbl5.grid(row=5, column=2)
    except Exception as e:
        print('не рисуем - 5')
   
    try:
        python_lang6 = BooleanVar() 
        python_lang6.set(True)
        python_checkbutton6 = Checkbutton(text=ASSETS[5], variable=python_lang6, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no6)
        python_checkbutton6.grid(row=6, column=1)
        lbl6 = Label(text='0.0', bg='white', width=15) 
        lbl6.grid(row=6, column=2)
    except Exception as e:
        print('не рисуем - 6')

    try:         
        python_lang7 = BooleanVar() 
        python_lang7.set(True)
        python_checkbutton7 = Checkbutton(text=ASSETS[6], variable=python_lang7, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no7)
        python_checkbutton7.grid(row=7, column=1)
        lbl7 = Label(text='0.0', bg='white', width=15) 
        lbl7.grid(row=7, column=2)
    except Exception as e:
        print('не рисуем - 7')

    try:
        python_lang8 = BooleanVar() 
        python_lang8.set(True)
        python_checkbutton8 = Checkbutton(text=ASSETS[7], variable=python_lang8, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no8)
        python_checkbutton8.grid(row=8, column=1)
        lbl8 = Label(text='0.0', bg='white', width=15) 
        lbl8.grid(row=8, column=2)
    except Exception as e:
        print('не рисуем - 8')

    try:
        python_lang9 = BooleanVar() 
        python_lang9.set(True)
        python_checkbutton9 = Checkbutton(text=ASSETS[8], variable=python_lang9, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no9)
        python_checkbutton9.grid(row=9, column=1)
        lbl9 = Label(text='0.0', bg='white', width=15) 
        lbl9.grid(row=9, column=2)
    except Exception as e:
        print('не рисуем - 9')

    try:
        python_lang10 = BooleanVar() 
        python_lang10.set(True)
        python_checkbutton10 = Checkbutton(text=ASSETS[9], variable=python_lang10, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no10)
        python_checkbutton10.grid(row=10, column=1)
        lbl10 = Label(text='0.0', bg='white', width=15) 
        lbl10.grid(row=10, column=2)
    except Exception as e:
        print('не рисуем - 10')

    try:
        python_lang11 = BooleanVar() 
        python_lang11.set(True)
        python_checkbutton11 = Checkbutton(text=ASSETS[10], variable=python_lang11, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no11)
        python_checkbutton11.grid(row=1, column=3)
        lbl11 = Label(text='0.0', bg='white', width=15) 
        lbl11.grid(row=1, column=4)
    except Exception as e:
        print('не рисуем - 11')
   
    try:
        python_lang12 = BooleanVar() 
        python_lang12.set(True)
        python_checkbutton12 = Checkbutton(text=ASSETS[11], variable=python_lang12, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no12)
        python_checkbutton12.grid(row=2, column=3)
        lbl12 = Label(text='0.0', bg='white', width=15) 
        lbl12.grid(row=2, column=4)
    except Exception as e:
        print('не рисуем - 12')

    try:
        python_lang13 = BooleanVar() 
        python_lang13.set(True)
        python_checkbutton13 = Checkbutton(text=ASSETS[12], variable=python_lang13, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no13)
        python_checkbutton13.grid(row=3, column=3)
        lbl13 = Label(text='0.0', bg='white', width=15) 
        lbl13.grid(row=3, column=4)
    except Exception as e:
        print('не рисуем - 13')

    try:
        python_lang14 = BooleanVar() 
        python_lang14.set(True)
        python_checkbutton14 = Checkbutton(text=ASSETS[13], variable=python_lang14, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no14)
        python_checkbutton14.grid(row=4, column=3)
        lbl14 = Label(text='0.0', bg='white', width=15) 
        lbl14.grid(row=4, column=4)
    except Exception as e:
        print('не рисуем - 14')

    try:
        python_lang15 = BooleanVar() 
        python_lang15.set(True)
        python_checkbutton15 = Checkbutton(text=ASSETS[14], variable=python_lang15, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no15)
        python_checkbutton15.grid(row=5, column=3)
        lbl15 = Label(text='0.0', bg='white', width=15) 
        lbl15.grid(row=5, column=4)
    except Exception as e:
        print('не рисуем - 15')
   
    try:
        python_lang16 = BooleanVar() 
        python_lang16.set(True)
        python_checkbutton16 = Checkbutton(text=ASSETS[15], variable=python_lang16, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no16)
        python_checkbutton16.grid(row=6, column=3)
        lbl16 = Label(text='0.0', bg='white', width=15) 
        lbl16.grid(row=6, column=4)
    except Exception as e:
        print('не рисуем - 16')

    try:         
        python_lang17 = BooleanVar() 
        python_lang17.set(True)
        python_checkbutton17 = Checkbutton(text=ASSETS[16], variable=python_lang17, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no17)
        python_checkbutton17.grid(row=7, column=3)
        lbl17 = Label(text='0.0', bg='white', width=15) 
        lbl17.grid(row=7, column=4)
    except Exception as e:
        print('не рисуем - 17')

    try:
        python_lang18 = BooleanVar() 
        python_lang18.set(True)
        python_checkbutton18 = Checkbutton(text=ASSETS[17], variable=python_lang18, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no18)
        python_checkbutton18.grid(row=8, column=3)
        lbl18 = Label(text='0.0', bg='white', width=15) 
        lbl18.grid(row=8, column=4)
    except Exception as e:
        print('не рисуем - 18')
        
    try:
        python_lang19 = BooleanVar() 
        python_lang19.set(True)
        python_checkbutton19 = Checkbutton(text=ASSETS[18], variable=python_lang19, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no19)
        python_checkbutton19.grid(row=9, column=3)
        lbl19 = Label(text='0.0', bg='white', width=15) 
        lbl19.grid(row=9, column=4)
    except Exception as e:
        print('не рисуем - 19')

    try:
        python_lang20 = BooleanVar() 
        python_lang20.set(True)
        python_checkbutton20 = Checkbutton(text=ASSETS[19], variable=python_lang20, onvalue=True, offvalue=False, padx=15, pady=10, command=yes_or_no20)
        python_checkbutton20.grid(row=10, column=3)
        lbl20 = Label(text='0.0', bg='white', width=15) 
        lbl20.grid(row=10, column=4)
    except Exception as e:
        print('не рисуем - 20')
        
    ## Запускаем обновление спреда в GUI ##
        time.sleep(TIME)        
    try:
        lbl1.after_idle(tick1)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl2.after_idle(tick2)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl3.after_idle(tick3)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl4.after_idle(tick4)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl5.after_idle(tick5)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl6.after_idle(tick6)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl7.after_idle(tick7)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl8.after_idle(tick8)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl9.after_idle(tick9)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl10.after_idle(tick10)
    except Exception as e:
        print('не обновляем спред')
    
    try:
        lbl11.after_idle(tick11)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl12.after_idle(tick12)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl13.after_idle(tick13)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl14.after_idle(tick14)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl15.after_idle(tick15)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl16.after_idle(tick16)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl17.after_idle(tick17)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl18.after_idle(tick18)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl19.after_idle(tick19)
    except Exception as e:
        print('не обновляем спред')
        
    try:
        lbl20.after_idle(tick20)
    except Exception as e:
        print('не обновляем спред')
    
    root.mainloop()

thread1 = Thread(target=prescript, args=())
thread1.start()

''' СОЗДАЕМ ГРУППУ ПОТОКОВ '''
def create_threads():
    try:
        my_thread_1 = MyThread(ASSETS[0], client)    
        my_thread_1.start()
    except Exception as e:
        print('поток пустой - 1')

    try:
        my_thread_2 = MyThread(ASSETS[1], client)  
        my_thread_2.start()
    except Exception as e:
        print('поток пустой - 2')

    try:
        my_thread_3 = MyThread(ASSETS[2], client)  
        my_thread_3.start()
    except Exception as e:
        print('поток пустой - 3')

    try:    
        my_thread_4 = MyThread(ASSETS[3], client)  
        my_thread_4.start()
    except Exception as e:
        print('поток пустой - 4')

    try:    
        my_thread_5 = MyThread(ASSETS[4], client)  
        my_thread_5.start()
    except Exception as e:
        print('поток пустой - 5')

    try:    
        my_thread_6 = MyThread(ASSETS[5], client)  
        my_thread_6.start()
    except Exception as e:
        print('поток пустой - 6')

    try:    
        my_thread_7 = MyThread(ASSETS[6], client)  
        my_thread_7.start()
    except Exception as e:
        print('поток пустой - 7')

    try:     
        my_thread_8 = MyThread(ASSETS[7], client)  
        my_thread_8.start()
    except Exception as e:
        print('поток пустой - 8')

    try:     
        my_thread_9 = MyThread(ASSETS[8], client)  
        my_thread_9.start()
    except Exception as e:
        print('поток пустой - 9')

    try:     
        my_thread_10 = MyThread(ASSETS[9], client)  
        my_thread_10.start()
    except Exception as e:
        print('поток пустой - 10')

    try:
        my_thread_11 = MyThread(ASSETS[10], client)    
        my_thread_11.start()
    except Exception as e:
        print('поток пустой - 11')

    try:
        my_thread_12 = MyThread(ASSETS[11], client)  
        my_thread_12.start()
    except Exception as e:
        print('поток пустой - 12')

    try:
        my_thread_13 = MyThread(ASSETS[12], client)  
        my_thread_13.start()
    except Exception as e:
        print('поток пустой - 13')

    try:    
        my_thread_14 = MyThread(ASSETS[13], client)  
        my_thread_14.start()
    except Exception as e:
        print('поток пустой - 14')

    try:    
        my_thread_15 = MyThread(ASSETS[14], client)  
        my_thread_15.start()
    except Exception as e:
        print('поток пустой - 15')

    try:    
        my_thread_16 = MyThread(ASSETS[15], client)  
        my_thread_16.start()
    except Exception as e:
        print('поток пустой - 16')

    try:    
        my_thread_17 = MyThread(ASSETS[16], client)  
        my_thread_17.start()
    except Exception as e:
        print('поток пустой - 17')

    try:     
        my_thread_18 = MyThread(ASSETS[17], client)  
        my_thread_18.start()
    except Exception as e:
        print('поток пустой - 18')

    try:     
        my_thread_19 = MyThread(ASSETS[18], client)  
        my_thread_19.start()
    except Exception as e:
        print('поток пустой - 19')

    try:     
        my_thread_20 = MyThread(ASSETS[19], client)  
        my_thread_20.start()
    except Exception as e:
        print('поток пустой - 20')        

    try:    
        my_thread_1.join()
        my_thread_2.join()
        my_thread_3.join()
        my_thread_4.join()
        my_thread_5.join()
        my_thread_6.join()
        my_thread_7.join()
        my_thread_8.join()
        my_thread_9.join()
        my_thread_10.join()
        my_thread_11.join()
        my_thread_12.join()
        my_thread_13.join()
        my_thread_14.join()
        my_thread_15.join()
        my_thread_16.join()
        my_thread_17.join()
        my_thread_18.join()
        my_thread_19.join()
        my_thread_20.join()        
    except Exception as e:
        print(str(e))
        print('закрыл потоки, но работали не все потоки, поэтому поймали Exception')

    logger.info('Всего ордеров buy: ' + str(buy_ord_count))
    logger.info('Всего ордеров sell: ' + str(sell_ord_count)) 
    logger.info('Не смог buy: ' + str(zav_pok)) 
    logger.info('Не смог sell: ' + str(nesmog_sell))
    logger.info('При ставке ' + str(ORDER_VALUE) + ' было выполнено сделок: ' + str(deal_count))
    logger.info('Зависло sell: ' + str(deal_zavis) + '\n')

    print('Всего ордеров buy: ' + str(buy_ord_count))
    print('Всего ордеров sell: ' + str(sell_ord_count)) 
    print('Не смог buy: ' + str(zav_pok)) 
    print('Не смог sell: ' + str(nesmog_sell))
    print('При ставке ' + str(ORDER_VALUE) + ' было выполнено сделок: ' + str(deal_count))
    print('Зависло sell: ' + str(deal_zavis) + '\n')

    message('Всего ордеров buy: ' + str(buy_ord_count) + '\n' + 'Всего ордеров sell: ' + str(sell_ord_count) + '\n' + 'Не смог buy: ' + str(zav_pok) + '\n' + 'Не смог sell: ' + str(nesmog_sell) + '\n' + 'При ставке ' + str(ORDER_VALUE) + ' было выполнено сделок: ' + str(deal_count) + '\n' + 'Зависло sell: ' + str(deal_zavis) + '\n' + '#LevBinance')
    
    print('\nГОТОВО')  
 
if __name__ == "__main__":
    create_threads()

