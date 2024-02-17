from this import d
from selenium import webdriver
import datetime
import time
import pandas as pd 
from re import sub
from selenium.webdriver.common.by import By
import boto3
import numpy as np

account = ['710055289@qq.com', 'qq710055289@icloud.com', 'mengrj12138@gmail.com']
password = 'Rogerm12138!'

""" Enter website """
driver = webdriver.Chrome(executable_path='/Users/Roger/Downloads/chromedriver')
url = 'http://www.facebook.com'    
driver.get(url)
""" Enter id and password """
driver.find_element('xpath', '//*[@id="email"]').click()
driver.find_element(By.ID, "email").send_keys(account[0])
driver.find_element('xpath', '//*[@id="pass"]').click()
driver.find_element(By.ID, "pass").send_keys(password)
time.sleep(5)
url_1 = 'https://www.facebook.com/marketplace/category/vehicles?topLevelVehicleType=car_truck&exact=false'
driver.get(url_1)

""" Upload and download """
s3 = boto3.resource("s3")
def upload(Filename, Key, Bucket = "twttr12138"): #Key is filename, Filename should be dir!@#$@$!
    s3 = boto3.client("s3")
    s3.upload_file(
        Filename = Filename,
        Bucket = 'twttr12138',
        Key=Key
    )

""" Collect data and upload to AWS """
def collect_data(xpath, date, ele_value = 'kbiprv82'):
    df = pd.DataFrame(columns = ['Collection_date', 'Price', 'Title', 'Location', 'Mileage', 'Path', 'Cover_picture'])

    today = date

    l = list()
    lis = driver.find_elements(By.CLASS_NAME, value=ele_value)
    for i in lis:
        l.append(i.text)

    index = 1
    for i in l:
        seperated = i.split("\n")        
        try:
            path = driver.find_element('xpath', '//*[@id="' + xpath + '"]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div[5]/div/div[2]/div[' + str(index) + ']/div/div/span/div/div/a').get_attribute('href')
            cover_pic = driver.find_element('xpath', '//*[@id="' + xpath + '"]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div[5]/div/div[2]/div[' + str(index) + ']/div/div/span/div/div/a/div/div[1]/div/div/div/div/div/img').get_attribute('src')
        except:
            index += 1
            try:
                path = driver.find_element('xpath', '//*[@id="' + xpath + '"]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div[5]/div/div[2]/div[' + str(index) + ']/div/div/span/div/div/a').get_attribute('href')
                cover_pic = driver.find_element('xpath', '//*[@id="' + xpath + '"]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div[5]/div/div[2]/div[' + str(index) + ']/div/div/span/div/div/a/div/div[1]/div/div/div/div/div/img').get_attribute('src')
            except:
                index += 1
                path = driver.find_element('xpath', '//*[@id="' + xpath + '"]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div[5]/div/div[2]/div[' + str(index) + ']/div/div/span/div/div/a').get_attribute('href')
                cover_pic = driver.find_element('xpath', '//*[@id="' + xpath + '"]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div[5]/div/div[2]/div[' + str(index) + ']/div/div/span/div/div/a/div/div[1]/div/div/div/div/div/img').get_attribute('src')             

        if seperated[1][0] == '$':
            del seperated[1]

        if seperated[0] == 'Free': 
            seperated[0] = '$0'

        if len(seperated) >= 4:
            df = df.append({'Collection_date':today, 
                            'Price': float(sub(r'[^\d.]', '', seperated[0])), 
                            'Title': seperated[1], 
                            'Location': seperated[2], 
                            'Mileage': seperated[3],
                            'Path': path,
                            'Cover_picture': cover_pic},
                            ignore_index=True)
        elif len(seperated) == 3:
            seperated.append('null')
            df = df.append({'Collection_date':today, 
                            'Price': float(sub(r'[^\d.]', '', seperated[0])), 
                            'Title': seperated[1], 
                            'Location': seperated[2], 
                            'Mileage': seperated[3],
                            'Path': path,
                            'Cover_picture': cover_pic},
                            ignore_index=True)    
        elif len(seperated) == 2:
            seperated.append('null')
            seperated.append('null')
            df = df.append({'Collection_date':today, 
                            'Price': float(sub(r'[^\d.]', '', seperated[0])), 
                            'Title': seperated[1], 
                            'Location': seperated[2], 
                            'Mileage': seperated[3],
                            'Path': path,
                            'Cover_picture': cover_pic},
                            ignore_index=True)
        else:
            pass

        index += 1
        print(f'num {index} is all set')
    
    file_name  = 'facebook_vehicles_'+today+'.csv'
    dir_ = '/Users/Roger/facebook_vehicles_'+today+'.csv'
    df.to_csv(dir_, index=False)

    upload(
    Filename = dir_,
    Key=file_name
    ) 

def collect_detail(date):
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName('fb').getOrCreate()
    
    dir_ = 'facebook_vehicles_'+date+'.csv'

    df = spark.read.csv('/Users/Roger/'+dir_, header=True, inferSchema=True)
    path = df.select('Path')
    path = path.collect()

    des = list()
    for i in range(len(path)):
        try:
            url = path[i][0]
            driver.get(url)
            l = list()
            text = driver.find_elements(By.CLASS_NAME, value='n851cfcs')    
            for j in text:
                l.append(j.text)
            l = ' '.join(l)
            des.append(l.strip())
            print(f'{round((i+1)*100 / len(path), 1)}% is done')
        except:
            des.append('null')
            print(f'some error with number {i+1}')
            pass

    pd_df = df.toPandas()
    pd_df['Description'] = [i for i in des]
    pd_df.to_csv('/Users/Roger/facebook_vehicles_'+date+'_moreinfo.csv', index = False)

    upload(
        '/Users/Roger/facebook_vehicles_'+date+'_moreinfo.csv',
        'facebook_vehicles_'+date+'_moreinfo.csv'
    )
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
def get_everything(d, path):
    try:
        collect_data(date=str(d), xpath = path)
    except:
        raise 'first step is wrong'

    try:
        collect_detail(date=str(d))
    except:
        raise 'second step is wrong'

    s3.Object("twttr12138", 'facebook_vehicles_'+str(d)+'.csv').delete()

""" Run it! """
d = datetime.date.today()
get_everything(d, "mount_0_0_qF")