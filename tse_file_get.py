#-*- coding: utf8 -*-
import sys, os
import time
import datetime
#import socket
#import struct
#import requests
import ast
import json
import base64
import configparser
import urllib3
import threading

#path = "C:\\Python34\\mysite\\get_tse\\"
path = ""
#程式執行時間序log
def write_screen_log(object):
    write_log_path = get_ini_str("INIT","LOG_PATH")
    if not os.path.isdir(write_log_path):
        os.mkdir(write_log_path)
    f = open(write_log_path+str(datetime.datetime.now())[0:10].replace('-','')+"_log.txt","a+", encoding = 'utf8')

    f.write(str(object) + "\n")
    f.close()
def write_log_txt(object):
    write_log_path = get_ini_str("INIT","LOG_PATH")
    if not os.path.isdir(write_log_path):
        os.mkdir(write_log_path)
    f = open(write_log_path+"tse"+str(datetime.datetime.now())[0:10].replace('-','')+"_log.txt","a+", encoding = 'utf8')

    f.write("\n["+str(datetime.datetime.now())[0:19]+"]"+str(object))
    f.close()
#讀取tse file 資訊清單
def read_act_log_txt():
    lines = []
    try:
        delete_BOM_general("daily_log\\tse_act_log.txt")
        fr = open("daily_log\\tse_act_log.txt","r+")
        lines = fr.read().splitlines()
        fr.close()
    except:
        pass
    return lines
#讀取tse txt Schedule_Time資訊清單
def read_Schedule_Time_txt():
    lines = []
    dict = {}
    try:
        delete_BOM_general(workfile)
        fr = open(workfile,"r+")
        lines = fr.read().splitlines()
        fr.close()

        #重新整理, 遇到[Schedule_Time當key, 其餘append
        list = []
        key_str = ""
        for item in lines:
            if "[Schedule_Time" in item:
                if key_str == "":#第一個key_str
                    key_str = item
                else:
                    dict.update({key_str:list})
                    list = []
                    key_str = item
            else:
                if item == "":
                    pass
                else:
                    list.append(item)
        dict.update({key_str:list})
    except:
        pass
    return dict
#儲存tse file 資訊清單
def write_act_log_txt(list_of_object):
    f = open("daily_log\\tse_act_log.txt","w+", encoding = 'utf8')
    for object in list_of_object:
        f.write(str(object)+"\n")
    f.close()
#儲存tse file 下載後含資料的檔案
def write_tse_file(dict,filename_):
    write_tse_file_path = get_ini_str("INIT","DOWNLOAD_PATH")
    if not os.path.isdir(write_tse_file_path):
        os.mkdir(write_tse_file_path)
    f = open(write_tse_file_path+filename_, 'wb+')
    decoded_result = base64.b64decode(dict['content'])
    f.write(decoded_result)
    f.close()
# 取出 ini 中的設定
def get_ini_str(section, key):
    config_ = configparser.ConfigParser()
    delete_BOM_general(path+"GET_TSE.ini")
    config_.read(path+"GET_TSE.ini")
    return config_.get(section, key)
def key_exist_in_object(key_,object):
    if key_ in object:
        return object[key_]
    else:
        return ''
def delete_BOM_general(filepath_):
    frb = open(filepath_,mode='rb')
    content = frb.read()
    frb.close()
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
        f_no_bom = open(filepath_, 'wb+')
        f_no_bom.write(content)
        f_no_bom.close()
# 發url (post)
def send_post_request(url_from_ini,Schedule_dict,check_list,init_date):
    data_dic = {}
    data_dic.update({"account":get_ini_str("INIT","USER_ID")})
    data_dic.update({"password":get_ini_str("INIT","USER_PWD")})
    #url_from_ini="https://eshop.twse.com.tw/api/v1.0/file/getFiles"
    #s = requests.Session()
    #s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
    http = urllib3.PoolManager()
    urllib3.disable_warnings()
    try:
        #r = s.post(url_from_ini,data=data_dic)
        r = http.request(
            'POST',
            url_from_ini,
            fields = data_dic,
            headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36' }
            )
    except:
        write_log_txt('==== send_post_request 1 error ===='+str(sys.exc_info()))
        #sys.exit()

    list = json.loads(r.data.decode('utf8'))#最新的tse file 清單內容
    last_time_list = read_act_log_txt()#上次的tse file 清單內容
    write_log_txt("send_post_request list size="+str(len(list))+", last_time_list size="+str(len(last_time_list)))

    for i in range(len(list)):
        dict = {}
        #比對檔案 dataDate dateTime length本身有沒有更新
        #write_log_txt(list[i])
        temp_item = list[i]

        tf=searching_for_download(last_time_list, Schedule_dict, check_list, temp_item, init_date)
        if tf:#有更新才下載
            print(str(datetime.datetime.now())[0:10].replace('-','')+ " " + temp_item['file']['name']+' download size='+temp_item['file']['length'])
            write_screen_log(temp_item['file']['name']+' download size='+temp_item['file']['length'])
            write_log_txt(temp_item['file']['name']+' download size='+temp_item['file']['length'])
            try:
                data_dic.update({"fileName":temp_item['file']['name']})
                #r = s.post(url_from_ini,data=data_dic)
                r = http.request('POST', url_from_ini, fields = data_dic,
                        headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
                        }
                    )
                #解json base64
                dict = json.loads(r.data.decode('utf8'))#轉成dict才能用
                write_tse_file(dict,temp_item['file']['name'])
            except:
                write_log_txt('==== send_post_request 2 error ===='+str(sys.exc_info()))
        else:#沒更新只寫log
            write_log_txt(temp_item['file']['name']+' unchange')

    write_act_log_txt(list)
    write_log_txt('==== send_post_request tick complete ====')
    #sys.exit()

def searching_for_download(last_time_list, Schedule_dict, check_list, new_item, init_date):
    flag = False
    sys_exit = False
    count = 0
    #檢查是否符合Schedule_Time
    nowtime = str(datetime.datetime.now())[11:16]# 13:23
    for item in Schedule_dict:
        Schedule_Time = item.replace(']','').split('=')[1]
        if nowtime > Schedule_Time and len(Schedule_dict[item])>0:#時間沒超過Schedule_Time不處理
            check_list.extend(Schedule_dict[item]) #['BTLOUR', 'BWOFFU', 'TWFSTU', 'HBOURU', 'TWT53U', 'TWT58U', 'TWT95U', 'BFI82U', 'TWT67U', 'TWT62U', 'TWT69U', 'TWT61U', 'BFI34U', 'BWTMPUD', 'TWT64U', 'BFIBGU', 'TWT68U', 'TWTA6U', 'TWTA5U', 'BFIBYU', 'TWTA7U', 'BFZ08U', 'TWTAAU', 'BFIBXU', 'TWTA8U', 'TWTA9U', 'TWTABU', 'TWHFAU1', 'TWTADU', 'BFIDMU.CSV', 'BFIDMU.XLS', 'BFIDOU.CSV', 'BFIDOU.XLS', 'BFIDQU.CSV', 'BFIDQU.XLS', '']
            Schedule_dict.update({item:[]})#extend進去check_list只會發生一次( 13:30的塞完, 剩下18:30跟 20:30 )
        elif len(Schedule_dict[item]) == 0:
            count = count+1

    if count == len(Schedule_dict) and len(check_list) == 0:#Schedule_dict裡面沒有任何待抓的檔案了 且 check_list size = 0, 結束程式
        sys.exit()

    #print("["+str(datetime.datetime.now())+"] len(Schedule_dict)"+str(len(Schedule_dict))+", Schedule count="+str(count)+", check_list size="+str(len(check_list)))
    write_log_txt("len(Schedule_dict)"+str(len(Schedule_dict))+", Schedule done count="+str(count)+", check_list size="+str(len(check_list)))
    
    force_get_list = ast.literal_eval(get_ini_str("FILE","force_get"))#執行到一半的時候偷改ini也可
    if new_item['file']['name'] in force_get_list:#強制下載
        new_item.update({'status':'ForceGet'})
        flag = True
        return flag
        
    if len(last_time_list) == 0 and new_item['file']['name'] in check_list:#初次執行
        if new_item['file']['dataDate'] == init_date:#當日檔案 下載
            flag = True
            new_item.update({'status':'Download First Run'})
            check_list.remove(new_item['file']['name'])#確定下載了就從check_list裡面移掉
        else:#非當日檔案不下載
            new_item.update({'status':'OutOfDate'})
        return flag

    for item_str in last_time_list:
        item = ast.literal_eval(item_str)
        if item['file']['name'] == new_item['file']['name']:#新舊檔案名對到
            if new_item['file']['name'] in check_list:#檔案名出現在check_list內
                if new_item['file']['dataDate'] == init_date:#當日檔案 下載
                    new_item.update({'status':'Download'})
                    check_list.remove(new_item['file']['name'])#確定下載了就從check_list裡面移掉
                    flag = True
                else:#非當日檔案不下載
                    new_item.update({'status':'OutOfDate'})
            else:#在檔案名沒有出現在check_list之前, 要讓他保持在沒變的狀態
                new_item = item
                if key_exist_in_object('status',new_item) == "":#不要重複更新狀態
                    new_item.update({'status':'UnChange'})
            #if item['file']['dataDate'] == new_item['file']['dataDate'] and item['file']['dateTime'] == new_item['file']['dateTime'] and item['file']['length'] == new_item['file']['length'] and new_item['file']['dataDate'] == init_date:
            last_time_list.remove(item_str)#越找越少
            break
    #write_log_txt('==== last_time_list remove ===='+new_item['file']['name'])
    return flag

def run_with_interval():
    #執行的當日時間要在初始化的時候記下來
    init_date = str(datetime.datetime.now())[0:10].replace('-','')
    #初始化只讀取一次Schedule_dict
    Schedule_dict = read_Schedule_Time_txt()
    check_list = []
    while True:
        print(str(datetime.datetime.now())[11:19].replace(':','')+" ==== run_with_interval ====")
        write_screen_log(str(datetime.datetime.now())[11:19].replace(':','')+" ==== run_with_interval ====")
        write_log_txt("==== run_with_interval ====")
        send_post_request(get_ini_str("INIT","URL"),Schedule_dict,check_list,init_date)
        time.sleep(int(get_ini_str("INIT","Tick_Interval")))

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("tse_file_get workfile")
        sys.exit()
        
    workfile = sys.argv[1]
    print("Version 1.0", workfile)
    write_screen_log("Version 1.0 " + workfile)
           
    if not os.path.isdir("daily_log"):
        os.mkdir("daily_log")
    threading.Thread(target=run_with_interval ,args = ()).start()
    
    #send_post_request(get_ini_str("INIT","URL"))