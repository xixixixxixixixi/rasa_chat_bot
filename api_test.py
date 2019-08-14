# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 17:10:27 2019

@author: lyh
"""

from iexfinance.stocks import Stock


def get_book(ID):
    appl = Stock(ID,token = "pk_05a3d93860d54ae4a2c0f9a01ed362d5")
    x=appl.get_book()
    return x


def get_historical_prices(ID):
    appl = Stock(ID,token = "pk_05a3d93860d54ae4a2c0f9a01ed362d5")
    x=appl.get_historical_prices()
    return x

def get_previous_day_prices(ID):
    appl = Stock(ID,token = "pk_05a3d93860d54ae4a2c0f9a01ed362d5")
    x=appl.get_previous_day_prices()
    return x
'''
x=get_previous_day_prices("SINA")
print (x)
'''