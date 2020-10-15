from selenium import webdriver
from collections import Counter
import numpy as np
from datetime import date, timedelta
from dateutil.parser import parse 
import requests
import csv
import re 

def grab_html():
     url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair%3A%22Daily%20Discussion%22&restrict_sr=1&sort=new'
     driver = webdriver.Chrome(executable_path=r"Enter Path Here")
     driver.get(url)
     return driver

def grab_link(driver):
     parent = driver.find_element_by_xpath("//*[contains(@class, '_eYtD2XCVieq6emjKBH3m')]") 
     link = parent.find_element_by_xpath('../..').get_attribute('href')
     stock_link = link.split('/')[-3]
     driver.close() 
     return stock_link

def grab_commentid_list(stock_link):
    html = requests.get(f'https://api.pushshift.io/reddit/submission/comment_ids/{stock_link}')
    if 'json' in html.headers.get('Content-Type'):
        raw_comment_list = html.json()
        return raw_comment_list
    else:
        print('Response content is not in JSON format.')

    
def grab_stocklist():
    print("Grab stock list")
    with open('stocklist.txt', 'r') as w:
        stocks = w.readlines()
        stocks_list = []
        for a in stocks:
            a = a.replace('\n','')
            stocks_list.append(a)
    return stocks_list
def get_comments(comment_list):
     print("get comments")
     html = requests.get(f'https://api.pushshift.io/reddit/comment/search?ids={comment_list}&fields=body&size=1000')
     newcomments = html.json()
     return newcomments

def grab_stock_count(stocks_list,raw_comment_list):
     print("generate stock count")
     cleaned = np.array(raw_comment_list['data'])
     remove_me = slice(0,1000)
     i = 0
     stock_dict = Counter()
     option_dict = Counter()

     while i < len(cleaned):
        print(len(cleaned))
        cleaned = np.delete(cleaned, remove_me)
        new_comments_list = ",".join(cleaned[0:1000])
        newcomments = get_comments(new_comments_list)
        for a in newcomments['data']:
            if '/' in a['body']:
                pos_tsd = re.search(r'[A-Z]{1,5} (\$)?\d{1,5}[cpCP] \d{1,2}/\d{1,2}', a['body'])
                pos_tds = re.search(r'[A-Z]{1,5} \d{1,2}/\d{1,2} (\$)?\d{1,5}[cpCP]', a['body'])
                if pos_tsd:
                    option_dict[pos_tsd.group(0)]+=1
                elif pos_tds:
                    option_dict[pos_tds.group(0)]+=1
            comment = set(a['body'].split(" "))
            for line in stocks_list:
                ticker = line.strip()
                ticker = re.split('[,|]', ticker)
                if ticker[0] in comment:
                    stock_dict[ticker[0]]+=1
     stock = dict(stock_dict)
     option = dict(option_dict)
     return stock, option

if __name__ == "__main__":
    driver = grab_html()
    stock_link = grab_link(driver)
    raw_comment_list = grab_commentid_list(stock_link)
    stocks_list = grab_stocklist()
    stocks, options = grab_stock_count(stocks_list, raw_comment_list)
    
    sorted_stocks = sorted(stocks.items(), key=lambda x: x[1], reverse=True)
    sorted_options = sorted(options.items(), key=lambda x: x[1], reverse=True)

    with open('stocks.csv','w') as w:
        writer = csv.writer(w, lineterminator='\n')
        writer.writerow(['Stock ',' Number of Mentions'])
        for key in sorted_stocks:
            writer.writerow([key[0], key[1]])
    with open('options.csv','w') as w:
        writer = csv.writer(w, lineterminator='\n')
        writer.writerow(['Option ',' Number of Mentions'])
        for key in sorted_options:
            writer.writerow([key[0], key[1]])