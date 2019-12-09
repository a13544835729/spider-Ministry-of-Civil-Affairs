import pymysql
import requests
from lxml import etree
import re
import random
import time
from hashlib import  md5

class MzbSpider():
    def __init__(self):
        self.url='http://www.mca.gov.cn/article/sj/xzqh/2019/'
        self.headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                   'Chrome/73.0.3683.75 Safari/537.36'}
        self.db=pymysql.connect('127.0.0.1','root','123456','govdb',charset='utf8')
        self.cur=self.db.cursor()
        #创建三个列表
        self.province=[]
        self.city=[]
        self.county=[]


    def get_fake_link(self):
        html=requests.get(url=self.url,headers=self.headers).text
        p=etree.HTML(html)
        # link='http://www.mca.gov.cn/'+p.xpath('//a[@class="artitlelist"]/@href')[0]
        link='http://www.mca.gov.cn/'+p.xpath('//table//tr[2]/td/a/@href')[0]
        # print(link)
        #对link 进行md5加密
        s=md5()
        s.update(link.encode())
        finger=s.hexdigest()
        #查看link是否在request_finger表中
        sql='select finger from request_finger where finger=%s'
        result=self.cur.execute(sql,[finger])
        if not result:
            self.get_real_link(link)
            #将finger 插入
            ins='insert into request_finger values(%s)'
            self.cur.execute(ins,[finger])
            self.db.commit()
        else:
            print('已在表中')

    def get_real_link(self,link):
        html=requests.get(url=link,headers=self.headers).text
        with open('fake_link','w') as f:
            f.write(html)
        # print(html)
        p=re.compile('window.location.href="(.*?)"',re.S)
        real_link=p.findall(html)[0]
        # print()
        self.get_data(real_link)

    def get_data(self,real_link):
        html = requests.get(url=real_link, headers=self.headers).text
        p=etree.HTML(html)
        tr_list=p.xpath('//tr[@height="19"]')
        for tr in tr_list:
            name=tr.xpath('./td[3]/text()')[0].strip()
            code=tr.xpath('./td[2]/text()')[0].strip()
            print(name,code)
            if code[-4:]=='0000':
                self.province.append((name,code))
                if code[:2] in ['11','12','31','50']:
                    cfcode = code[2:] + '0000'
                    self.city.append((name,code,cfcode))
            elif code[-2:]=='00':
                cfcode=code[2:]+'0000'
                self.city.append((name,code,cfcode))
                #永远记录最近的一个市
                # last_city=code
            else:
                if code[:2] in ['11', '12', '31', '50']:
                    xfcode=code[:2]+'0000'
                else:
                    xfcode=code[:4]+'00'
                self.county.append((name,code,xfcode))
        self.insert_sql()

    #保存到数据库
    def insert_sql(self):
        #先清空表
        del1='delete from province'
        del2='delete from city'
        del3='delete from county'
        self.cur.execute(del1)
        self.cur.execute(del2)
        self.cur.execute(del3)
        self.db.commit()
        print(self.province)
        print(self.city )
        print(self.county)
        #插入表
        sql1='insert into province values(%s,%s)'
        sql2='insert into city values(%s,%s,%s)'
        sql3='insert into county values(%s,%s,%s)'
        self.cur.executemany(sql1,self.province)
        self.cur.executemany(sql2,self.city)
        self.cur.executemany(sql3,self.county)
        self.db.commit()



    def run(self):
        self.get_fake_link()


if __name__ == '__main__':
    spider=MzbSpider()
    spider.run()



