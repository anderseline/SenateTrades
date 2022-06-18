# current version in batch file
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import re 
import nums_from_string
import json
from email.utils import formataddr 
import tweepy
from Google import Create_Service
import base64

def fetchSession(url):
    session = HTMLSession()
    r = session.get(url)
    return r

def getTrades(r):
    table = r.html.find('table')[0]
    rows = table.find('tr')
    return rows[1:]

def value_to_ints(value):
    bad_chars = [
        ',','$','-'
    ]
    for c in bad_chars:
        value = value.replace(c,'')
    low, high = [
        int(x) for x in (value.split('  ', 1))
    ]
    return [low,high]

def getTicker(trade_):
    try:
        return re.findall('\[(.*?)\]', trade_)[0]
    except IndexError:
        return ''

def getYahooInfo(ticker):
    url = 'https://finance.yahoo.com/quote/{}'.format(ticker)
    r = fetchSession(url)
    # handle invalid ticker
    tables = r.html.find('table')
    if len(tables) == 1:
        return -1,-1
    
    left_table = tables[0]
    right_table = tables[1]
    left_rows = left_table.find('td')
    right_rows = right_table.find('td')
    left_items = []
    left_values = []
    right_items = []
    right_values = []
    
    i = 0
    for l,r in zip(left_rows, right_rows):
        # evens = item headers
        if i % 2 == 0:
            left_items.append(l.text)
            right_items.append(r.text)
        # odds = values in table
        else:
            left_values.append(l.text)
            right_values.append(r.text)
        i += 1
    return (
        dict(
            zip(left_items, left_values)
        ),
        dict(
            zip(right_items, right_values)
        )
    )

def isStock(right_table):
    return [*right_table][0] == 'Market Cap'

def getMktCap(right_table):
    return right_table['Market Cap']

def getOpen(left_table):
    return left_table['Open']

def getSectorIndustry(ticker):
    url = 'https://finance.yahoo.com/quote/{}/profile?p={}'.format(ticker, ticker)
    r = fetchSession(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        sect_ind = (
            (
                soup.find_all('p', attrs={'class' : 'D(ib) Va(t)'})
            )[0].text.strip()
        )
    # bad ticker was given 
    except IndexError:
        return ''
    sector = re.search('\xa0(.*)Industry', sect_ind).group(1)
    industry = re.search('Industry:\xa0(.*)Full', sect_ind).group(1)
    return sector, industry

def parseToMillions(value_string):
    unit = value_string[-1:]
    number = nums_from_string.get_nums(value_string)[0]
    #keep in units of millions
    if unit == 'B':
        number = number * 1000
    elif unit == 'T':
        number = number * 1000000
    return number

def cleanNewsURLQuery(trade):
    return (
        'https://news.google.com/search?q={}&hl=en-US&gl=US&ceid=US%3Aen'.format(
            trade.replace(' ', '%20').replace(',', '').replace('[','%5B').replace(']','%5D')
            )
        )

def getArticles(news_url):
    r = fetchSession(news_url)
    page = r.html.find('main')
    conatiner = page[0].find('c-wiz')
    body = conatiner[0].find('div')[0]
    article_shells = body.find('div')[1:]
    articles = []
    for i in range(0,len(article_shells),11):
        articles.append(article_shells[i])
        if len(articles) == 3:
            break
    all_articles = []
    for a in articles:
        try:
            super_title = a.find('h3')[0]
        # if no articles could be found (len(supertitle) = 0)
        except IndexError:
            return -1
        link_html = super_title.find('a')
        title = super_title.text
        link = (
            str(link_html[0]).split("href='.")[1]
        ).split("'")[0]
        link = 'https://news.google.com{}'.format(link)
        all_articles.append(
            {
                'title' : title,
                'url' : link
            }
        )
    return all_articles

def writeTradeToFile(trade, path):
    with open(path, 'w') as f:
        for (key,item) in trade.items():
            if key == 'Yahoo!':
                f.write(
                    '%s\n' % (
                    item
                    )
                )
            else:
                f.write(
                    '%s : %s\n' % (
                    key,item
                    )
                )
        f.write('\n')

def getHTMLNews(t):
    path = '..\\res\\html\\alert_formatting\\format.html'
    return open(path).read().format(
                quote_link = t['Yahoo!'],
                ticker = getTicker(t['Equity']),
                trade_date = t['Trade Date'],
                file_date = t['File Date'],
                senator = t['Senator'],
                trade = t['Equity'],
                value = t['Trade Value'],
                mkt_cap = t['Market Cap'],
                sect = t['Sector'],
                ind  = t['Industry'],
                news_url1 = t['URL1'],
                news_title1 = t['Title 1'],
                news_url2 = t['URL2'],
                news_title2 = t['Title 2'],
                news_url3 = t['URL3'],
                news_title3 = t['Title 3']
            )

def getHTMLNoNews(t):
    path = '..\\res\\html\\alert_formatting\\format_no_news.html'
    return open(path).read().format(
                quote_link = t['Yahoo!'],
                ticker = getTicker(t['Equity']),
                trade_date = t['Trade Date'],
                file_date = t['File Date'],
                senator = t['Senator'],
                trade = t['Equity'],
                value = t['Trade Value'],
                mkt_cap = t['Market Cap'],
                sect = t['Sector'],
                ind  = t['Industry']
            )

def scrapeImportantTrades(today=datetime.today().date(), onlyToday=False, backtest=False, backtestDate='2022-04-01'):
    r = fetchSession('https://sec.report/Senate-Stock-Disclosures')
    # if website is down
    try:
        trades = getTrades(r)
    except IndexError:
        print('website may be down. quitting.')
        sys.exit(1)

    n = len(trades)
    all_trades = []
    dt_backtest = datetime.strptime(backtestDate, '%Y-%m-%d').date()

    for i in range(0,n,2):
        imp_trade = False
        l1_elements = trades[i].find('td')
        l2_elements = trades[i+1].find('td')[:-1]

        # make sure trade happened today before doing anything 
        file_date, trade_date = l1_elements[0].text.split('\n')
        if file_date != str(today) and onlyToday:
            break

        if backtest:
            file_dt = datetime.strptime(file_date, '%Y-%m-%d').date()
            days = file_dt - dt_backtest
            if days < timedelta(days=0):
                break

        # ensure trade is a purchase, otherwise contniue to next trade
        trade_type = l2_elements[0].text.split('\n', 1)[0]
        if trade_type != 'Purchase':
            continue

        trade = l1_elements[1].text
        senator = l1_elements[2].text
        senator = senator.split(' [')[0]
        value = value_to_ints(l2_elements[1].text)
        
        ticker = getTicker(trade)
        # if no ticker is found, not an equity trade
        if ticker == '':
            continue

        # handle case of finding company debt 
        if ('Notes' or 'Matures') in trade:
            continue
        
        left_table, right_table = getYahooInfo(ticker)
        # invalid ticker given 
        if left_table == -1:
            continue
        # if the ticker is an ETF, not a stock, or an options play
        if not isStock(right_table) or 'Option' in trade:
            continue

        sect, ind = getSectorIndustry(ticker)
        open_price = getOpen(left_table)
        mkt_cap = getMktCap(right_table)
        try:
            mkt_cap = parseToMillions(mkt_cap)
        except IndexError:
            continue
        small_mktCap = mkt_cap < 2000 and mkt_cap > 0
        medium_mktCap = mkt_cap >= 2000 and mkt_cap <= 10000
        large_mktCap = mkt_cap > 10000
        # any small caps, medium purchase medium caps, large purchase large cap
        if small_mktCap:
            imp_trade = True
            cap_string = 'small'
        elif medium_mktCap and value[0] >= 50000:
            imp_trade = True
            cap_string = 'medium'
        elif large_mktCap and value[0] >= 100000:
            imp_trade = True
            cap_string = 'large'

        if imp_trade:
            url = 'https://finance.yahoo.com/quote/{}/'.format(ticker)
            trade_dict = {
                'trade date' : trade_date,
                'file date' : file_date,
                'senator' : senator,
                'trade' : trade,
                'trade type' : trade_type,
                'value' : value,
                'mkt cap' : cap_string,
                'sector' : sect,
                'industry' : ind,
                'yahoo finance' : url
            }
            # add ticker and trade date to master list for tracking
            path = '..\\res\\trade_info\\master_list_of_trades.txt'
            with open(path, 'a') as f:
                f.write('%s\t%s\t%s\n' % (
                    ticker, open_price, file_date
                ))
            all_trades.append(trade_dict)

    # print all trades from today to .json file
    dump_path = '..\\test\\daily_trades.json'
    with open(dump_path,'w') as f:
        f.write(
            json.dumps(obj=all_trades, indent=4)
            )
    return all_trades

def formatForEmail(trades_list):
    trades_for_txt = []
    for t in trades_list:
        trade_date = str(t['trade date']) + ' (' + str((
                datetime.today().date() - datetime.strptime(
                    t['trade date'], '%Y-%m-%d'
                ).date()
            )).split(',')[0] + ' ago)'

        value_string = '$' + (
            "{:,}".format(t['value'][0])
        ) + ' to $' + (
            "{:,}".format(t['value'][1])
        )

        if t['mkt cap'] == 'small':
            mkt_cap_string = 'Small Cap (Under $2B)'
        elif t['mkt cap'] == 'medium':
            mkt_cap_string = 'Medium Cap ($2B to $10B)'
        else:
            mkt_cap_string = 'Large Cap (Over $10B)'

        list_of_titles_urls = getArticles(
            cleanNewsURLQuery(t['trade'])
        )

        if len(list_of_titles_urls) == 3:
            trades_for_txt.append(
                {
                    'Trade Date' : trade_date,
                    'File Date' : t['file date'],
                    'Senator' : t['senator'],
                    'Equity' : t['trade'],
                    'Trade Value' : value_string,
                    'Market Cap' : mkt_cap_string,
                    'Sector' : t['sector'],
                    'Industry' : t['industry'],
                    'Yahoo!' : t['yahoo finance'],
                    'Title 1' : list_of_titles_urls[0]['title'], 
                    'Title 2' : list_of_titles_urls[1]['title'],  
                    'Title 3' : list_of_titles_urls[2]['title'], 
                    'URL1' : list_of_titles_urls[0]['url'],
                    'URL2' : list_of_titles_urls[1]['url'],
                    'URL3' : list_of_titles_urls[2]['url']
                }
            )
        else:
            trades_for_txt.append(
                {
                    'Trade Date' : trade_date,
                    'File Date' : t['file date'],
                    'Senator' : t['senator'],
                    'Equity' : t['trade'],
                    'Trade Value' : value_string,
                    'Market Cap' : mkt_cap_string,
                    'Sector' : t['sector'],
                    'Industry' : t['industry'],
                    'Yahoo!' : t['yahoo finance']
                }
            )

    return trades_for_txt

def sendEmails(trades, toList, testList):

    CLIENT_SECRET_FILE = '..\\res\\gmail\\client_published.json'
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    SCOPES = ['https://mail.google.com/']

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    send_email = 'ders.mailbot@gmail.com'
    recipients = []
    # code to send trades to list of recipient emails 
    if toList:
        list_path = '..\\res\\mail_info\\mailing_list.txt'
        with open(list_path,'r') as f:
            lines = f.readlines()
        for l in lines:
            recipients.append(l.strip())
    elif testList:
        list_path = '..\\res\\mail_info\\mailing_list_test.txt'
        with open(list_path,'r') as f:
            lines = f.readlines()
        for l in lines:
            recipients.append(l.strip())
    else:
        recipients = [send_email]

    recipients = ', '.join(recipients)
    for t in trades:
        html_write_path = '..\\res\\html\\alert_formatting\\trade_for_html.txt'
        writeTradeToFile(t, html_write_path)

        with open(html_write_path,'r') as f:
            data = f.read()
        # if the length of the string from the file is not 0, then there was a 
        # (major) trade executed today
        if len(data) != 0:
            message = MIMEMultipart('alternative')
            message['Subject'] = 'Trade Alert'
            message['From'] = formataddr(('SenateTrades', send_email))
            message['To'] = send_email
            message['Bcc'] = recipients

            body = MIMEText(data, 'plain')
            if len(t) == 15:
                html_string = getHTMLNews(t)
            # no news bullets 
            else:
                html_string = getHTMLNoNews(t)

            formatting = MIMEText(html_string, 'html')

            message.attach(body)
            message.attach(formatting)
            raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode()
            message = service.users().messages().send(userId='me', body={'raw':raw_string}).execute()

def formatForTwitter(trades_list):
    trades_for_twitter = []
    for t in trades_list:
        value_string = '$' + (
            "{:,}".format(t['value'][0])
        ) + ' to $' + (
            "{:,}".format(t['value'][1])
        )
        ticker = getTicker(t['trade'])
        yahoo_link = 'https://finance.yahoo.com/quote/{}'.format(ticker)
        trades_for_twitter.append(
            {
                'Ticker' : ticker,
                'Senator' : t['senator'],
                'Value' : value_string,
                'yahoo' : yahoo_link,
            }
        )
    return trades_for_twitter

def writeTradeToFileTwitter(trade, path):
    with open(path, 'w') as f:
        for (key,item) in trade.items():
            if key == 'yahoo':
                f.write(
                    '%s' % (item)
                )
                continue
            f.write(
                '%s : %s\n' % (
                key,item
                )
            )

def tweetTrades(trades_list, write_path, keys_path):
    trades_for_twitter = formatForTwitter(trades_list)
    with open(keys_path) as f:
        keys = json.load(f)
    client = tweepy.Client(
        bearer_token=keys['bearer_token'],
        consumer_key=keys['api_key'],
        consumer_secret=keys['api_key_secret'],
        access_token=keys['access_token'],
        access_token_secret=keys['access_token_secret']
    )
    for t in trades_for_twitter:
        writeTradeToFileTwitter(t, write_path)
        with open(write_path, 'r') as f:
            tweet_data = f.read()
        client.create_tweet(text=tweet_data)

def main():

    onlyToday = True
    backtest = False
    toList = True
    testList = False
    backtestDate = '2022-06-13'
    twitter_write_path = '..\\res\\twitter\\write_for_twitter.txt'
    twitter_keys_path = '..\\res\\twitter\\keys.json'

    trades = scrapeImportantTrades(onlyToday=onlyToday, backtest=backtest, backtestDate=backtestDate)
    trades_for_mail = formatForEmail(trades)
    sendEmails(
        trades=trades_for_mail, toList=toList, testList=testList
    )
    tweetTrades(
        trades_list=trades, write_path=twitter_write_path, 
        keys_path= twitter_keys_path
    )

if __name__ == '__main__':
    main()