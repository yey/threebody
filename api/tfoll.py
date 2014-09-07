#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

from base import *
from config.constant import * 
from config import accounts

import requests
import json
import logging
import md5
import urllib
import time

class TfollTrade(BaseTrade):

    def __init__(self, settings):
        BaseTrade.__init__(self, settings)
        self._token = md5.md5(self._partner + self._secret_key).hexdigest()
    
    #return {"oa":"004","uv":"1","result":{???},"error":””}
    def _get_api(self, prefix, params):
        oa_map = {
            '000' : '连接频率过大',
            '001' : '不存在该OpenApi用户',
            '002' : '公钥私钥不匹配',
            '003' : '对应用户不存在',
            '004' : '用户存在',
            'None' : 'None'
        }
        uv_map = {
            '0' : '没有通过',
            '1' : '通过',
            'None' : 'None'
        }

        params.update({
            'public_key' : self._partner,
            'token' : self._token
        })
        url = '%s?%s' % (prefix, urllib.urlencode(params))
        resp = requests.get(url, **HTTP_ARGS).json()

        error = resp.get('error', None)
        if resp.get('uv', None) != '1' or resp.get('oa', None) != '004':
            raise Exception("Failed to get %s, resp[%s]]" % (prefix, resp))
        if  error != '000' and error != '' and error != None:
            raise Exception("Failed to get %s, resp[%s]]" % (prefix, resp))


        return resp['result']

    def trade(self, type, rate, amount, symbol) : 
        buy_error_map = {
            '000' : '购买成功',
            '111' : '购买失败',
            '001' : '购买数量为空',
            '002' : '购买价为空',
            '003' : '购买数量小于0',
            '004' : '购买价小于0',
            '005' : '账户余额不足,请充值',
            '006' : '账户余额不足,请充值',
            '201' : '平仓',
            '202' : '爆仓'
        }
        sell_error_map = {
            '000' : '出售成功',
            '111' : '出售失败',
            '001' : '出售数量为空',
            '002' : '出售价为空',
            '003' : '出售数量小于0',
            '004' : '出售价小于0',
            '005' : '账户RMB余额不足,请充值',
            '006' : '账户BTC余额不足,请充值',
            '007' : '账户LTC余额不足,请充值',
            '008' : '账户CTC余额不足,请充值',
            '201' : '平仓',
            '202' : '爆仓'
        }
        try:
            prefix = self._api_host + '/openapi/trade/%s.html' % type
            self._get_api(prefix, {
                '%s_price' % type : rate,
                '%s_quantity' % type : amount,
                'type' : (symbol == 'btc_cny') and '1' or '2'
            })
        except Exception as e:
            raise TradeFailedException('tfoll trade fail, price[%s], amount[%s], symbol[%s], type[%s], errorinfo[%s]' % \
                    (rate, amount, symbol, type, e))

    def user_info(self):
        info = {
            "funds": {
                "freezed": {
                },
                "free": {
                }
            }
        }
        try:
            prefix = self._api_host + '/openapi/user_info/user_info.html'
            resp = self._get_api(prefix, {})
            trade_info = resp['trade']
            info['funds']['free']['cny'] = trade_info['has_CNY']
            info['funds']['free']['ltc'] = trade_info['has_LTC']
            info['funds']['free']['btc'] = trade_info['has_BTC']
            info['funds']['freezed']['cny'] = trade_info['use_CNY']
            info['funds']['freezed']['ltc'] = trade_info['use_LTC']
            info['funds']['freezed']['btc'] = trade_info['use_BTC']
            return info
        except Exception as e:
            raise UserInfoFailedException('Get tfoll userinfo fail: %s' % e)


    def depth(self, symbol):
        symbol = symbol == 'btc_cny' and 1 or 2
        url = self._api_host + "/api/depth/depth.html?type=%s" % symbol
        try:
            resp = requests.get(url, **HTTP_ARGS).json()
            res = {
                'buy' : resp['bids'][0],
                'sell' : resp['asks'][0]
            }
            return res
        except Exception as e:
            raise DepthFailedException('tfoll get depth failed [%s]' % e)

if __name__ == "__main__":
    tfoll = TfollTrade(accounts.tfoll)
    pre = int(time.time())
    while True:
        cur = int(time.time())
        print '----------------------%s----------------------' % (cur - pre)
        print tfoll.depth('ltc_cny')
        print tfoll.user_info()
        pre = cur
    #print tfoll.trade(type='sell', rate=40, amount=10, symbol='ltc_cny')

