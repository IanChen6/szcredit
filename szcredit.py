# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     
   Description :
   Author :       ianchen
   date：          
-------------------------------------------------
   Change Activity:
                   2017/01/02:
-------------------------------------------------
"""
import base64
import json
import pymssql
from lxml import etree
import requests

from get_db import get_db
from log_ging.log_01 import *
import time
import redis
from get_db import job_finish


class szcredit(object):
    def __init__(self, cn, sID, batchid, companyid, customerid):
        self.headers = {'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Host': 'www.szcredit.org.cn',
                        'Cookie': 'UM_distinctid=160a1f738438cb-047baf52e99fc4-e323462-232800-160a1f73844679; ASP.NET_SessionId=4bxqhcptbvetxqintxwgshll',
                        'Origin': 'https://www.szcredit.org.cn',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Referer': 'https://www.szcredit.org.cn/web/gspt/newGSPTList.aspx?keyword=%u534E%u88D4&codeR=28',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36',
                        'X-Requested-With': 'XMLHttpRequest',
                        }
        self.batchid = batchid
        self.cn = cn
        self.sID = sID
        self.companyid = companyid
        self.customerid = customerid
        self.query = [cn, sID]
        self.host, self.port, self.db = get_db(companyid)

    def insert_db(self, sql, params):
        conn = pymssql.connect(host=self.host, port=self.port, user='Python', password='pl,okmPL<OKM',
                               database=self.db, charset='utf8')
        cur = conn.cursor()
        if not cur:
            raise Exception("数据库连接失败")
        # cur.callproc('[dbo].[Python_Serivce_DSTaxApplyShenZhen_Add]', (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))
        len(params)
        cur.callproc(sql, params)
        conn.commit()
        cur.close()

    def login(self):
        session = requests.session()
        yzm_url = 'https://www.szcredit.org.cn/web/WebPages/Member/CheckCode.aspx?'
        yzm = session.get(url=yzm_url, headers=self.headers)

        for q in self.query:
            # 处理验证码
            with open("yzm.jpg", "wb") as f:
                f.write(yzm.content)
                f.close()
            with open('yzm.jpg', 'rb') as f:
                base64_data = str(base64.b64encode(f.read()))
                base64_data = "data:image/jpg;base64," + base64_data[2:-1]
                post_data = {"a": 2, "b": base64_data}
                post_data = json.dumps({"a": 2, "b": base64_data})
                res = session.post(url="http://39.108.112.203:8002/mycode.ashx", data=post_data)
                # print(res.text)
                f.close()
            postdata = {'action': 'GetEntList',
                        'keyword': q,
                        'type': 'query',
                        'ckfull': 'false',
                        'yzmResult': res.text
                        }
            resp1 = session.post(url='https://www.szcredit.org.cn/web/AJax/Ajax.ashx', headers=self.headers,
                                 data=postdata)
            resp = resp1.json()
            result = resp['resultlist']
            if resp1 is not None and resp1.status_code == 200 and result:
                result_dict = result[0]
                print(result_dict["RecordID"])  # 获取ID
                detai_url = 'https://www.szcredit.org.cn/web/gspt/newGSPTDetail3.aspx?ID={}'.format(
                    result_dict["RecordID"])
                detail = session.get(url=detai_url, headers=self.headers, timeout=30)
                detail.encoding = 'gbk'
                root = etree.HTML(detail.text)  # 将request.content 转化为 Element
                self.parse(root)
            return

    def parse(self, root):
        title = root.xpath('//*[@id="Table31"]//li[@class="current"]')
        t_list = []
        for t in title:
            tt = t.xpath(".//a[1]/text()")
            print(tt[0])
            t_list.append(tt[0])

        tb_list = []
        tb = root.xpath('//*[@id="Table31"]//table')  # 抓取table31
        for i in tb:
            data_json = []
            tb_detail = i.xpath(".//tr")
            for j in tb_detail:
                t = j.xpath('./td//text()')
                data_json.append(t)
                # data_json[t[0]]=t[1]
            # data_json=json.dumps(data_json,ensure_ascii=False)
            # print(data_json)
            tb_list.append(data_json)

        data_dict = {}
        for i in range(len(t_list)):
            data_dict[t_list[i]] = tb_list[i]
        print(data_dict)

        if "登记备案信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["登记备案信息"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["登记备案信息"] = d1
            # dm = {}
            # dm["登记备案信息"] = d1
            # print(dm)

        if "股东登记信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["股东登记信息"]
            d2 = {}
            for i in get_data[1:]:
                d3 = {}
                d3['出资额'] = i[4]
                d3['出资比例'] = i[5]
                d2[i[0]] = d3
            d1['股东名称'] = d2
            data_dict["股东登记信息"] = d1
            dm = {}
            dm["股东登记信息"] = d1
            print(dm)

        if "成员登记信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["成员登记信息"]
            for i in get_data[1:]:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["成员登记信息"] = d1
            # dm = {}
            # dm["成员登记信息"] = d1
            # print(dm)

        if "税务登记信息(国税)" in data_dict.keys():
            d1 = {}
            get_data = data_dict["税务登记信息(国税)"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["税务登记信息(国税)"] = d1
            # dm = {}
            # dm["税务登记信息(国税)"] = d1
            # print(dm)

        if "税务登记信息(地税)" in data_dict.keys():
            d1 = {}
            get_data = data_dict["税务登记信息(地税)"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["税务登记信息(地税)"] = d1
            # dm = {}
            # dm["税务登记信息(地税)"] = d1
            # print(dm)

        if "机构代码信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["机构代码信息"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["机构代码信息"] = d1
            # dm = {}
            # dm["机构代码信息"] = d1
            # print(dm)

        if "印章备案信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["印章备案信息"]
            d2 = {}
            for i in get_data[1:]:
                d3 = {}
                d3['印章编码'] = i[1]
                d3['审批日期'] = i[2]
                d3['备案日期'] = i[3]
                d3['备案情况'] = i[4]
                d3['详情'] = i[5]
                d2[i[0]] = d3
            d1['印章名称'] = d2
            data_dict["印章备案信息"] = d1
            # dm = {}
            # dm["印章备案信息"] = d1
            # print(dm)

        if "企业参保信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["企业参保信息"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["企业参保信息"] = d1
            # dm = {}
            # dm["企业参保信息"] = d1
            # print(dm)

        if "海关企业基本登记信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["海关企业基本登记信息"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["海关企业基本登记信息"] = d1
            # dm = {}
            # dm["海关企业基本登记信息"] = d1
            # print(dm)

        if "高新技术企业认定信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["高新技术企业认定信息"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["高新技术企业认定信息"] = d1
            # dm = {}
            # dm["高新技术企业认定信息"] = d1
            # print(dm)

        if "对外贸易经营者备案登记资料" in data_dict.keys():
            d1 = {}
            get_data = data_dict["对外贸易经营者备案登记资料"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["对外贸易经营者备案登记资料"] = d1
            # dm = {}
            # dm["对外贸易经营者备案登记资料"] = d1
            # print(dm)

        if "住房公积金缴存数据表" in data_dict.keys():
            d1 = {}
            get_data = data_dict["住房公积金缴存数据表"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["住房公积金缴存数据表"] = d1
            # dm = {}
            # dm["住房公积金缴存数据表"] = d1
            # print(dm)

        if "电子商务认证企业信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["电子商务认证企业信息"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["电子商务认证企业信息"] = d1
            # dm = {}
            # dm["电子商务认证企业信息"] = d1
            # print(dm)

        if "电子商务认证企业网站信息" in data_dict.keys():
            d1 = {}
            get_data = data_dict["电子商务认证企业网站信息"]
            for i in get_data:
                try:
                    d1[i[0]] = i[1]
                except:
                    d1[i[0]] = ""
            data_dict["电子商务认证企业网站信息"] = d1
            # dm = {}
            # dm["电子商务认证企业网站信息"] = d1
            # print(dm)

        if "企业年报信息" in data_dict.keys():
            get_data = data_dict["企业年报信息"]
            d2 = {}
            for i in range(int(len(get_data) / 2)):
                d3 = {}
                d3['报送年度'] = get_data[i * 2][1]
                d3['发布日期'] = get_data[i * 2 + 1][1]
                d2[i + 1] = d3
            data_dict["企业年报信息"] = d1
            # dm = {}
            # dm["企业年报信息"] = d2
            # print(dm)

        # 企业变更信息
        try:
            title = root.xpath('//*[@id="Table123"]//li[@class="current"]')
            t_list = []
            for t in title:
                tt = t.xpath("./text()")
                print(tt[0])
                t_list.append(tt[0])

            tb_list = []
            tb = root.xpath('//*[@id="Table123"]//table')  # 抓取table31

            for i in tb:
                data_json = []
                tb_detail = i.xpath(".//tr")
                for j in tb_detail:
                    t = j.xpath('./td//text()')
                    data_json.append(t)
                    # data_json[t[0]]=t[1]
                # data_json=json.dumps(data_json,ensure_ascii=False)
                # print(data_json)
                tb_list.append(data_json)

            for i in range(len(t_list)):
                data_dict[t_list[i]] = tb_list[i]


            if "企业变更信息" in data_dict.keys():
                d1 = {}
                get_data = data_dict["企业变更信息"]
                d2 = {}

                for i in get_data[1:]:
                    d2['变更日期'] = i[1]
                    d2['变更事项'] = i[2]
                    d1[i[0]] = d2
                data_dict["企业变更信息"] = d1
        except:
            print("No exist")

        print(data_dict)
        logger.info(data_dict)
        infojson = json.dumps(data_dict, ensure_ascii=False)
        params = (
            self.batchid, self.companyid, self.customerid, self.cn, self.sID, infojson
        )
        self.insert_db("[dbo].[Python_Serivce_WXWebShenZhen_Add]", params)

redis_cli = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
def run_test(cn, sID, batchid, companyid, customerid):
    print("++++++++++++++++++++++++++++++++++++")
    print('jobs[ts_id=%s] running....' % batchid)
    time.sleep(5)
    logger = create_logger()
    try:
        credit = szcredit(cn=cn, sID=sID, batchid=batchid, companyid=companyid,
                          customerid=customerid)
        credit.login()
        job_finish(sd["6"], sd["7"], sd["8"], sd["3"], sd["4"], sd["5"], '1', '成功爬取')
        logger.info("深圳企业信用网信息抓取完成")
    except Exception as e:
        logger.error(e)
        job_finish(sd["6"], sd["7"], sd["8"], sd["3"], sd["4"], sd["5"], '-1', 'error')
    print('jobs[ts_id=%s] done' % batchid)
    result = True
    return result


while True:
    # ss=redis_cli.lindex("list",0)
    ss = redis_cli.lpop("sz_credit_list")
    if ss is not None:
        # print(redis_cli.lpop("list"))
        sd = json.loads(ss)
        run_test(sd["1"], sd["2"], sd["3"], sd["4"], sd["5"])
    else:
        time.sleep(20)
        print("no task waited")
