#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio, os, uuid
from sign import get_signed_service_url
from coroweb import get, post
from models import App, AppDeviceRecord, Account
from iPhoneMap import get_iphone_name

def get_current_time():
    return int(time.time() * 1000)

@get('/api/saveApp')
async def api_save_app_info(*, name, size):
    app = App(name = name, size = size, status = 1, add_time = get_current_time())

    await app.save()

    return dict(app = app)

@get('/api/updateApp')
async def api_update_app_info(*, app_id, app_name):
    app = await App.find(app_id)
    app.name = app_name
    await app.update()

    return dict(app = app)

@get('/api/allApp')
async def api_get_all_app():
    apps = await App.findAll()
    total_install_count = 0
    for app in apps:
        recordCount = await AppDeviceRecord.findNumber('count(id)', where="app_id = '" + app.id + "'")
        app.installed_count = recordCount
        total_install_count = total_install_count + recordCount

    apps = sorted(apps, reverse=True, key=lambda a: a.installed_count)
    index = 1
    for app in apps:
        app.index = index
        index = index + 1

    download_url_prefix = 'https://www.kmjskj888.com/manager/app.html?id='
    manager_url = 'https://www.kmjskj888.com/manager/deviceRecord.html'
    return dict(status = 0, download_url_prefix = download_url_prefix, manager_url = manager_url, total_install_count = total_install_count, total_count = len(apps), apps = apps)

@get('/api/allAccount')
async def api_get_all_account():
    accounts = await Account.findAll()
    for a in accounts:
        a.password = '******'

    accounts = sorted(accounts, reverse=True, key=lambda a: a.surplus_count)
    index = 1
    for account in accounts:
        account.index = index
        index = index + 1

    return dict(status = 0, total_count = len(accounts), accounts = accounts)

@get('/api/saveAccount')
async def api_save_account_info(*, account, password, count):
    account = Account(account = account, password = password, surplus_count = count, add_time = get_current_time())

    await account.save()

    return dict(account = account)

@get('/api/appInfo')
async def api_get_app_info(*, id):
    app = await App.find(id)
    app.icon_path = 'https://www.kmjskj888.com/images/icon_' + id + '.png'
    if app.slide_images != None:
        images = ['https://www.kmjskj888.com/images/' + app.slide_images]
    else:
        images = ['http://www.kmjskj888.com/resource/image/slide_1.png', 'http://www.kmjskj888.com/resource/image/slide_2.png']
    extendedInfos = [{'title' : '开发商', 'value' : app.developer},
                     {'title' : '大小', 'value' : str(app.size) + 'MB'},
                     {'title' : '类别', 'value' : '工具'},
                     {'title' : '兼容性', 'value' : '需要iOS 9.0 或更高版本'},
                     {'title' : '语言', 'value' : '简体中文'},
                     {'title' : '年龄分级', 'value' : '4+'},
                     {'title' : '版权', 'value' : app.name}]
    udid_url = 'https://www.kmjskj888.com/configs/' + app.id + '.mobileconfig'
    jump_url = 'https://www.dibaqu.com/embedded.mobileprovision'
    return dict(appInfo = app, images = images, extendedInfos = extendedInfos, udid_url = udid_url, jump_url = jump_url)

def parse_udid(xmlString):
    xml_decode_str = xmlString.decode('utf-8', errors='ignore')
    str = xml_decode_str[xml_decode_str.index('<key>UDID</key>'): xml_decode_str.index('</plist>') + 8]
    str = str.replace('\n', '')
    str = str.replace('\t', '')
    udid = str[len('<key>UDID</key><string>'): str.index('</string>')]

    str = xml_decode_str[xml_decode_str.index('<key>PRODUCT</key>'): xml_decode_str.index('</plist>') + 8]
    str = str.replace('\n', '')
    str = str.replace('\t', '')
    models = str[len('<key>PRODUCT</key><string>'): str.index('</string>')]

    return (udid, models)

@post('/api/parseUdid/{appid}')
async def api_parser_udid(appid, request):
    reader = request.content
    xmlString = await reader.read()
    udid = ''
    models = ''
    if xmlString:
        results = parse_udid(xmlString)
        udid = results[0]
        models = results[1]

    location = 'https://www.kmjskj888.com/manager/app.html?id=' + appid + '&udid=' + udid + '&models=' + models

    return dict(Location = location)

@post('/api/registerUdid')
async def api_register_udid(*, appid, udid, models):
    service_url = await get_signed_service_url(appid, udid, models)

    error_string = ''
    if service_url == '':
        error_string = '该App下载数量已满'

    return dict(service_url = service_url, error_string = error_string)

@get('/api/appDeviceRecord')
async def api_get_app_device_record(*, app_id):
    allRecords = await AppDeviceRecord.findAll()
    records = []

    for r in allRecords:
        if r.app_id == app_id:
            if r.add_time is None:
                r.add_time = 0
            records.append(r)

    records = sorted(records, reverse = True, key = lambda a: a.add_time)

    index = 1
    for r in records:
        r.index = index
        r.models = get_iphone_name(r.models)

        timeArray = time.localtime(r.add_time / 1000 + 12 * 60 * 60)
        r.add_time = time.strftime("%Y.%m.%d %H:%M:%S", timeArray)

        index = index + 1

    return dict(status = 0, total = len(records), data = records)
