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
#讀取tse file 資訊清單 as JSON fromat
def read_act_log_JSON():
    lines = read_act_log_txt()
    strdata = "["
    for r in lines :
        r = r.replace("'","\"")
        strdata = strdata + r + ","
    strdata = strdata[0:len(strdata)-1]
    strdata  = strdata + "]"
    json_data = json.loads(strdata)
    return json_data
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
        
    backup_main_tse_file_path = get_ini_str("INIT","BACKUP_PATH")
    if not os.path.isdir(backup_main_tse_file_path):
        os.mkdir(backup_main_tse_file_path)
        
    backup_tse_file_path = get_ini_str("INIT","BACKUP_PATH")+"\\"+str(datetime.datetime.now())[0:10].replace('-','')+"\\"
    if not os.path.isdir(backup_tse_file_path):
        os.mkdir(backup_tse_file_path)

    decoded_result = base64.b64decode(dict['content'])
    if filename_ in ("AWSTIU","AWSTIU1","TWTA6U","TWT62U","TWT69U","TWTA5U","AWSTIE","TWTA7U","TWTC6U"):
        fbackup = open(backup_tse_file_path+filename_, 'wb+')
        fbackup.write(decoded_result)
        fbackup.close()
    #20190211 decoded_result要依照檔案作內容解析之後改格式
    #要先轉換再寫檔，避免檔案內容為0影響外部程式判斷
    #print("start convert")
    fix_result = tse_file_content_compress(filename_, decoded_result)
    #print("end convert")
    f = open(write_tse_file_path+filename_, 'wb+')
    f.write(fix_result)
    f.close()
#新資料截取字串後重組成舊資料格式
def tse_file_content_compress(filename_, decoded_result):
    "新資料截取字串後重組成舊資料格式 tse_file_content_compress(str filename_, bytes decoded_result)"
    result_str = b''
    result_str_list = []
    count = 0
    try:
        write_log_txt(filename_ + "compress start ="+str(len(decoded_result)))
        if filename_ in ("AWSTIU","AWSTIU1","TWTA6U","TWT62U","TWT69U","TWTA5U"):
            #180->150
            #decoded_result 180 切一段, string_filter(0,7) +string_filter(7,9)轉舊格式 +string_filter(16,9)轉舊格式+++++...
            # 9(05)V9(04)轉9(04)V99 => 098761234 -> 987612
            while True:
                if len(decoded_result) == 0 or len(decoded_result)<180:
                    write_log_txt(filename_ + "compress data count ="+str(count))
                    break
                try:
                    cut = decoded_result[:180]# 待處理之dataitem
                    if string_filter(cut,0,1) == b'2':
                        result_str_list.append(string_filter(cut,0,7))
                        result_str_list.append(string_filter(cut,8,4)+string_filter(cut,12,2))#開盤價
                        result_str_list.append(string_filter(cut,17,4)+string_filter(cut,21,2))#最高價
                        result_str_list.append(string_filter(cut,26,4)+string_filter(cut,30,2))#最低價
                        result_str_list.append(string_filter(cut,35,4)+string_filter(cut,39,2))#收盤價
                        result_str_list.append(string_filter(cut,43,1))
                        result_str_list.append(string_filter(cut,45,4)+string_filter(cut,49,2))#漲跌價
                        result_str_list.append(string_filter(cut,53,36))
                        result_str_list.append(string_filter(cut,90,4)+string_filter(cut,94,2))#最後揭示買價
                        result_str_list.append(string_filter(cut,99,4)+string_filter(cut,103,2))#最後揭示賣價
                        result_str_list.append(string_filter(cut,107,6)+string_filter(cut,113,2))#本益比或結算價
                        result_str_list.append(string_filter(cut,117,6)+string_filter(cut,123,2))#平均股利或最新履約價
                        result_str_list.append(string_filter(cut,127,33)+b'               ')#135+15 = 150
                    else:#3456789ABCDEFGH
                        result_str_list.append(string_filter(cut,0,150))
                    decoded_result = decoded_result[180:]
                    count = count +1
                    #write_log_txt(string_filter(cut,144,16))
                    #print(string_filter(cut,119,16))
                except:
                    write_log_txt('==== tse_file_content_compress while error ===='+str(sys.exc_info()))
            return result_str.join(result_str_list)
        elif filename_ in ("AWSTIE","TWTA7U"):
            #110->100
            while True:
                if len(decoded_result) == 0:
                    write_log_txt(filename_ + "compress data count ="+str(count))
                    break
                cut = decoded_result[:110]# 待處理之dataitem
                if string_filter(cut,0,1) == b'2':
                    result_str_list.append(string_filter(cut,0,60))#不變
                    result_str_list.append(string_filter(cut,61,5)+string_filter(cut,67,2))#開盤價
                    result_str_list.append(string_filter(cut,71,5)+string_filter(cut,77,2))#最高價
                    result_str_list.append(string_filter(cut,81,5)+string_filter(cut,87,2))#最低價
                    result_str_list.append(string_filter(cut,91,5)+string_filter(cut,97,2))#收盤價
                    result_str_list.append(b'            ')#89+12 = 100
                else:#3456789ABCDEFGH
                    result_str_list.append(string_filter(cut,0,100))
                decoded_result = decoded_result[110:]
                count = count +1
            return result_str.join(result_str_list)
        elif filename_ in ("TWTC6U"):
            while True:
                if len(decoded_result) == 0:
                    write_log_txt(filename_ + "compress data count ="+str(count))
                    break
                cut = decoded_result[:180]# 待處理之dataitem
                if string_filter(cut,0,1) == b'2':
                    result_str_list.append(string_filter(cut,0,7))
                    result_str_list.append(string_filter(cut,8,4)+string_filter(cut,12,2))#開盤價
                    result_str_list.append(string_filter(cut,17,4)+string_filter(cut,21,2))#最高價
                    result_str_list.append(string_filter(cut,26,4)+string_filter(cut,30,2))#最低價
                    result_str_list.append(string_filter(cut,35,4)+string_filter(cut,39,2))#收盤價
                    result_str_list.append(string_filter(cut,43,1))
                    result_str_list.append(string_filter(cut,45,4)+string_filter(cut,49,2))#漲跌價
                    result_str_list.append(string_filter(cut,53,36))
                    result_str_list.append(string_filter(cut,90,4)+string_filter(cut,94,2))#最後揭示買價
                    result_str_list.append(string_filter(cut,99,4)+string_filter(cut,103,2))#最後揭示賣價
                    result_str_list.append(string_filter(cut,107,6)+string_filter(cut,113,2))#本益比或結算價
                    result_str_list.append(string_filter(cut,117,6)+string_filter(cut,123,2))#平均股利或最新履約價
                    result_str_list.append(string_filter(cut,127,33)+b'               ')#135+15 = 150
                else:#3456789ABCDEFGH
                    result_str_list.append(string_filter(cut,0,150))
                decoded_result = decoded_result[180:]
                count = count +1
                #write_log_txt(string_filter(cut,144,16))
                #print(string_filter(cut,119,16))
            return result_str.join(result_str_list)
        else:
            return decoded_result
    except:
        write_log_txt(filename_ + " compress data error at count ="+str(count))
        write_log_txt('==== tse_file_content_compress  error ===='+str(sys.exc_info()))

def string_filter(str_data_, start_index_, cut_length_):
    "依照長度截取字串 string_filter(bytes_str, int, int )"
    return bytes(str_data_[start_index_:start_index_+cut_length_])    
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
def send_post_request(http,url_from_ini,Schedule_dict,check_list,init_date):
    data_dic = {}
    data_dic.update({"account":get_ini_str("INIT","USER_ID")})
    data_dic.update({"password":get_ini_str("INIT","USER_PWD")})
    #url_from_ini="https://eshop.twse.com.tw/api/v1.0/file/getFiles"
    #s = requests.Session()
    #s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'

    try:
        #r = s.post(url_from_ini,data=data_dic)
        r = http.request(
            'POST',
            url_from_ini,
            fields = data_dic,
            headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36' }
            )
        list = json.loads(r.data.decode('utf8'))#最新的tse file 清單內容
    except:
        write_log_txt('==== send_post_request 1 error ===='+str(sys.exc_info()))
        list = read_act_log_JSON()#上次的tse file 清單內容    
        time.sleep(int(get_ini_str("INIT","Tick_Interval"))*2) #多睡一下
        return
        #sys.exit()

    last_time_list = read_act_log_txt()#上次的tse file 清單內容
    write_log_txt("send_post_request list size="+str(len(list))+", last_time_list size="+str(len(last_time_list)))
    try:
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
                data_dic.update({"fileName":temp_item['file']['name']})
                #r = s.post(url_from_ini,data=data_dic)
                r = http.request('POST', url_from_ini, fields = data_dic,
                        headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
                        }
                    )
                #解json base64
                dict = json.loads(r.data.decode('utf8'))#轉成dict才能用
                write_tse_file(dict,temp_item['file']['name'])
            else:#沒更新只寫log
                write_log_txt(temp_item['file']['name']+' unchange')
    except:
        write_log_txt('==== send_post_request 2 error ===='+str(sys.exc_info()))

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
    
    try:
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
    except:  
        write_log_txt('==== searching_for_download error ===='+str(sys.exc_info()))
        flag = False
        
    return flag

def run_with_interval():
    #執行的當日時間要在初始化的時候記下來
    init_date = str(datetime.datetime.now())[0:10].replace('-','')
    #初始化只讀取一次Schedule_dict
    Schedule_dict = read_Schedule_Time_txt()
    check_list = []
    http = urllib3.PoolManager()
    urllib3.disable_warnings()
    while True:
        print(str(datetime.datetime.now())[11:19].replace(':','')+" ==== run_with_interval ====")
        write_screen_log(str(datetime.datetime.now())[11:19].replace(':','')+" ==== run_with_interval ====")
        write_log_txt("==== run_with_interval ====")
        try:
            send_post_request(http,get_ini_str("INIT","URL"),Schedule_dict,check_list,init_date)
        except:  
            write_log_txt('==== run_with_interval error ===='+str(sys.exc_info()))
        time.sleep(int(get_ini_str("INIT","Tick_Interval")))

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("tse_file_get workfile")
        sys.exit()
        
    workfile = sys.argv[1]
    print("Version 1.1c", workfile)
    write_screen_log("Version 1.0 " + workfile)
           
    if not os.path.isdir("daily_log"):
        os.mkdir("daily_log")
    threading.Thread(target=run_with_interval ,args = ()).start()
    
    #send_post_request(get_ini_str("INIT","URL"))