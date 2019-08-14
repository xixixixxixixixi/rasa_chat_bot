# -*- coding: utf-8 -*-


import string
import re
import random
import intent_extract
import api_test
import t2s
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InputFile

from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer,Interpreter,Metadata
from rasa_nlu import config

"""
总体思路为：
程序的整体逻辑上分为登录前和登录后两个部分，用到的主要工具有spacy，rasa_nlu，和telegram，在登录前，可以和机器人进行一些闲聊等不涉及股票数据上的交流，
闲聊通过固定套路和意图识别并回复的方式来实现，这部分没有涉及多轮查询。
在登录完成后，用户可以通过多轮查询来查询自己所需要的信息，由于本项目查询的信息都是基于特定股票的，
因此对于对股票不熟悉的用户，可以首先让机器人给自己推荐一些股票，这部分的推荐是通过意图识别，抽取查询的实体，然后
查询本地数据库来实现的。
在得知了自己想查询的股票后，用户可以通过多轮查询数据，由于这部分的查询都偏向格式化，因此意图识别和实体抽取可以整合为一个部分，
通过keyword的方式直接抽取
其中对于历史价格，由于文本的回复方式比较抽象，因此处理json串生成表格通过文件方式发送给用户。
"""



#训练数据
interpreter=Interpreter.load('D:\Chat_robot\default\model_20190811-205136')
print('ok')


#设置一系列初始状态
INIT=0
AUTHED=1
CHECK=2
HP=3
OP=4

#设置登录检验位
checked=0

params, suggestions, excluded = {}, [], []

#存储目前操作的相关股票和数据
stockname=''
item=''
date=''

reply=[]
state = INIT
pending = None

#发送表格位
sheet_flag=0

# 查询操作中的状态转换，多轮查询
policy_rules = {
    (INIT, "stock_search"): (INIT, "please enter your password?", AUTHED),
    (INIT, "location"): (INIT, "please enter your password first.", AUTHED),
    
    (INIT, "number"): (AUTHED, "perfect, welcome back!", None),
    
    (AUTHED, "stock_search"): (CHECK, "What kind of stock do you want to check?", None),
    (AUTHED, "location"): (CHECK, "What kind of stock do you want to check?", None),
    
    
    (CHECK, "hprice"): (CHECK, "In which kind of format do you prefer the result to be shown? Sheet or text?", HP),
    (CHECK, "form"): (HP, "Order received.I'm working on your request. It might cost a few second.", None),
    (HP, "hprice"): (CHECK, None, None),
    
    
    (CHECK, "close"): (CHECK, "Please enter the date that you want to check.", OP),
    (CHECK, "volume"): (CHECK, "Please enter the date that you want to check.", OP),
    (CHECK, "open"): (CHECK, "Please enter the date that you want to check.", OP),
    (CHECK, "number"): (OP, "Order received.I'm working on your request. It might cost a few second.", None),
    (OP, "open"): (CHECK, None, None),
    (OP, "close"): (CHECK, None, None),
    (OP, "volume"): (CHECK, None, None)
}

#固定套路回复
rules = {'I wanna (.*)': ['What would it mean if you got {0}', 
                         'Why do you want {0}', 
                         "What's stopping you from getting {0}"], 
         'do you remember (.*)': ['Did you think I would forget {0}', 
                                  "Why haven't you been able to forget {0}", 
                                 ], 
         'do you think (.*)': ['if {0}? Absolutely.'], 
         'if (.*)': ["Do you really think it's likely that {0}", 
                     'Do you wish that {0}', 
                     'What do you think about {0}', 
                     'Really--if {0}'],
         'Im (.*)': ["hello {0}"
                     ],
         'my name is (.*)': ["hello {0}"
                 ]
         }

#在telegram界面中回复
def reply_to_user(response):
    global reply
    #print("BOT : {}".format(response))
    reply.append(response)

#除查询或者推荐操作外的所有闲聊回复
def chitchat_response(message,interpreter):
    # Call match_rule()
    global params, suggestions, excluded
    response, phrase = match_rule(rules, message)
    
    # Return none is response is "default"
    if response == "default":
        response=intent_extract.keyrespond(message,interpreter)
        return response
    if '{0}' in response:
        # Replace the pronouns of phrase
        phrase = replace_pronouns(phrase)
        # Calculate the response
        response = response.format(phrase)
        return response
    #如果固定套路不生效，则抽取消息的意图，通过意图来给予闲聊回复
    response,params, suggestions, excluded=intent_extract.intent_response(message, params, suggestions, excluded,interpreter)
    return response

#匹配聊天的固定套路
def match_rule(rules, message):
    for pattern, responses in rules.items():
        match = re.search(pattern, message)
        if match is not None:
            response = random.choice(responses)
            var = match.group(1) if '{0}' in response else None
            return response, var
    return "default", None

#变换人称
def replace_pronouns(message):

    message = message.lower()
    if ' me ' in message:
        return re.sub('me', 'you', message)
    if ' i ' in message:
        return re.sub('i', 'you', message)
    elif ' my ' in message:
        return re.sub('my', 'your', message)
    elif ' your ' in message:
        return re.sub('your', 'my', message)
    elif ' you ' in message:
        return re.sub('you', 'me', message)

    return message

#查询过程中的带有状态转换和遗留任务的多轮查询
def policy_response(state, pending, message,interpreter):
    global checked
    global params, suggestions, excluded
    global stockname
    global CHECK
    new_state, response, pending_state = policy_rules[(state, intent_extract.match_intent(message,interpreter))]
    if(response is not None):
        reply_to_user(response)
    if pending is not None:
        new_state, response, pending_state = policy_rules[pending]
        if(response is not None):
            reply_to_user(response)
    if pending_state is not None:
        pending = (pending_state, intent_extract.match_intent(message,interpreter))
    if(new_state==CHECK) :
        checked=1
    return new_state, pending

#判断有没有选定想操作的股票名字
def stock_choosed():
    global stockname
    if (stockname == ''):
        response = "you have to choose a stock first."
        reply_to_user(response)
        return 0
    return 1


#处理消息得到应答
def send_message(state, pending, message,interpreter):
    global checked
    global params, suggestions, excluded
    global stockname
    global CHECK,date,item
    global sheet_flag
    
    intent=intent_extract.match_intent(message,interpreter)#提取现阶段操作的意图
    
    response = chitchat_response(message,interpreter)#首先判断是否为闲聊消息
    if response is not None:
            reply_to_user(response)
            return state, None

    #若不是闲聊型，则要先登录
    if(checked==0):
        new_state,pending=policy_response(state, pending, message,interpreter)#登录的状态转换多轮查询
        return new_state,pending
    #完成登录后
    else:
        if('search' in intent) or('location' in intent)or('affirm' in intent)or('deny' in intent):#如果内容中涉及地理位置或者搜索意图，则推荐一些股票
            response,params, suggestions, excluded=intent_extract.intent_response(message, params, suggestions, excluded,interpreter)
            reply_to_user(response)
            return state, None
        elif('sp_stock'in intent):#已登录的情况下，可随时更换自己想查询的特定股票
            stockname=intent_extract.ent_ex(message,interpreter)
            response="I see, you'd like to check this one. And?"
            reply_to_user(response)
            return state,None
        elif('hprice'in intent)or("form" in intent):#查询特定股票的历史价格记录
            if(stock_choosed()==0):#判断该查询操作中有没有选定特定的股票
                return state, None
            else:
                new_state,pending=policy_response(state, pending, message,interpreter)#若选择了，则按照规定的多轮查询步骤来进行查询
                if(intent=="form"):
                    if("text" in message):
                       response=str(api_test.get_historical_prices(stockname))
                       reply_to_user(response)
                    elif("sheet" in message):
                        t2s.text2sheet(api_test.get_historical_prices(stockname))
                        sheet_flag=1
                    else:#输入了意料之外的信息会报错
                        response="input error!"
                        reply_to_user(response)
                return new_state,pending
        elif('open'in intent)or('close'in intent)or('volume'in intent)or("number" in intent):#查询特定股票的开盘价，关盘价，市值等
            if (stock_choosed() == 0):#判断该查询操作中有没有选定特定的股票
                return state, None
            else:
                new_state,pending=policy_response(state, pending, message,interpreter)#若选择了，则按照规定的多轮查询步骤来进行查询
                if(intent!='number'):
                    item=intent
                else:
                    date=t2s.date_extract(message)[0]#从输入的字符串中中抽取出日期信息
                if(item!='' and date!=''):#判断查询条件是否都已经符合
                    t2s.text2sheet(api_test.get_historical_prices(stockname))#处理获得的报文并制作成excel表
                    response=t2s.checksheet(date,item)#从excel表中查询需要得到信息
                    if(response is not None):#查询完毕后释放输入缓存
                        reply_to_user(response)
                        item=''
                        date=''
                    else:#若表中查询失败，则回复查询不到对应信息
                        response="I can't find what you want"
                        reply_to_user(response)
                return new_state,pending      
        elif('logout'in intent):#退出登录
            response,params,suggestions,excluded=intent_extract.intent_response(message, params, suggestions, excluded,interpreter)
            reply_to_user(response)
            stockname=''
            item=''
            date=''
            checked=0
            return 0,None
"""
以下部分为telegram的对应部分
由于涉及的变量耦合较多，修改起来比较麻烦，暂时将这两部分封装在一起
"""

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

#测试机器人是否启动
def start(update, context):
    update.message.reply_text('Hi!')

def help(update, context):
    update.message.reply_text('Help!')

#处理用户发送的信息并给予回复
def echo(update, context):
    global state,pending,interpreter,reply,sheet_flag
    state, pending = send_message(state, pending, update.message.text, interpreter)
    for i in range(len(reply)):
        update.message.reply_text(reply[i])
    if(sheet_flag==1):
        with open("data.xlsx", 'rb') as f:
            inf = InputFile(f, filename="data.xlsx")
            update.message.reply_document(inf)
        sheet_flag=0
    reply=[]

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():

    #初始化相应信息
    updater = Updater("953533105:AAEhjjc9ym74-n1gRgSTIwg8n3J5Vqdr-RY", use_context=True)
    dp = updater.dispatcher

    #简单的控制台指令
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    #对于发送的信息通过echo函数来进行回复（名字叫做echo，功能不只是echo）
    dp.add_handler(MessageHandler(Filters.text, echo))

    # 记录错误
    dp.add_error_handler(error)

    # 启动机器人
    updater.start_polling()

    #阻塞进程直至keyboard interrupt
    updater.idle()

if __name__ == '__main__':
    main()

"""
测试样例：
    " hey ",
    "my name is Liyanhao",
    "do you remember when I last came here",
    "what can you do"
    "show me some stocks in us",
    "1234",
    "some stock in us",
    "no it doesn't work for me",
    "do you think humans should be worried about AI",
    "do you remember your last birthday",
    "age",
    "some stock in china",
    "some stock in us",
    "open price",
    "SINA",
    "open price",
    "2019-07-15",
    "I want to check the history price",
    "text",
    "about volume",
    "2019-08-07",
    "logout"
"""