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
from google.oauth2 import service_account
from googleapiclient.discovery import build
from newsapi.newsapi_client import NewsApiClient
import FormatFunctions
from GeneratePostFiles import generatePostFiles

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

def getTicker(t):
    try:
        return re.findall('\[(.*?)\]', t)[0]
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

def getCurrentSP500Price():
    url = 'https://finance.yahoo.com/quote/SPY/'
    r = fetchSession(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    x = soup.find_all(
        'fin-streamer', attrs={
            'data-symbol' : 'SPY',
            'data-field' : 'regularMarketPrice' 
            }
        )
    return float(x[0].text)

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

def parseToMillions(mkt_cap):
    unit = mkt_cap[-1:]
    number = nums_from_string.get_nums(mkt_cap)[0]
    #keep in units of millions
    if unit == 'B':
        number = number * 1000
    elif unit == 'T':
        number = number * 1000000
    return number

def cleanQuery(t):
    trade = t['trade']
    trade =  re.sub(
        '[^0-9a-zA-Z]+', ' ', trade
    )
    return trade.split('Common')[0] + 'Stock'

def getTradesNews(t, key_path):
    with open(key_path) as f:
        key = f.read()
    newsapi = NewsApiClient(api_key=key)
    
    search = cleanQuery(t)
    try:
        articles = newsapi.get_everything(
            q=search, language='en', sort_by='relevancy'
        )['articles'][:3]
    except IndexError:
        return -1
    if len(articles) == 0:
        return -1
    titles_urls = []
    for n in articles:
        titles_urls.append(
            {
                'title' : n['title'],
                'url' : n['url']
            }
        )
    return titles_urls

def getLastname(senator):
    lastname = senator
    if ',' in senator:
        lastname = senator.split(',')[0]
    ind = len(lastname.split(' '))
    lastname = lastname.split(' ')[ind-1]
    return lastname

def getContactInfo(senator):
    lastname = getLastname(senator)
    form_url = 'https://www.senate.gov/senators/senators-contact.htm'
    r = fetchSession(form_url)
    form = r.html.find('form')[3]
    # first row header
    options = form.find('option')[1:]
    foundName = False
    for i in options:
        i = i.html
        lastname_options = i.split('>')[1].split(' ')[0]
        if lastname == lastname_options:
            url = i.split('"')[1].split('"')[0]
            info = {
                'lastname':lastname,
                'url':url
            }
            foundName = True
            break
    if not foundName:
        return {
            'lastname':'',
            'url':''
        }
    url = info['url']
    if url[-1] == '/':
        url += 'contact'
    else:
        url += '/contact'
    try:
        r = fetchSession(url)
        res = r.status_code
        if res != 200:
            url = url.split('/contact')[0]
    except:
        return {
            'lastname':'',
            'url':''
        }
    return {
        'lastname':lastname,
        'url':url
    }

def getPartyState(senator):
    lastname = getLastname(senator)
    party_info = 'https://en.wikipedia.org/wiki/List_of_current_United_States_senators'
    r = fetchSession(party_info)
    table = r.html.find('table')[5]
    senatorRows = table.find('tr')[1:]
    row = 0
    party = ''
    state = ''
    for s in senatorRows:
        names = s.find('th')
        for n in names:
            name = n.text
            if name.split(' ')[-1] == lastname:
                staterow = (len(s.find('td')) == 11)
                if staterow:
                    party = s.find('td')[3].text.split('[')[0].split('\n')[0]
                    state = s.find('td')[0].text
                else:
                    party = s.find('td')[2].text.split('[')[0].split('\n')[0]
                    state = senatorRows[row-1].find('td')[0].text
        row += 1
    return [party, state]

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

def scrapeImportantTrades(today=datetime.today().date(), onlyToday=False, backtest=False, backtestDate='2022-04-01'):
    r = fetchSession('https://sec.report/Senate-Stock-Disclosures')
    # if website is down
    try:
        trades = getTrades(r)
    except IndexError:
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

        # handle case of finding company debt, or rare case of fund having a mkt cap listed instead of an NAV  
        if ('Notes' or 'Matures' or 'Fund') in trade:
            continue
        
        left_table, right_table = getYahooInfo(ticker)
        # invalid ticker given 
        if left_table == -1:
            continue
        # if the ticker is an ETF, not a stock, or an options play
        if not isStock(right_table) or 'Option' in trade:
            continue
        
        sect, ind = getSectorIndustry(ticker)
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
            all_trades.append(trade_dict)

    return all_trades

def formatForEmail(trades_list):
    trades_for_txt = []
    for t in trades_list:
        # change datetime.today().date() to strptime from file date.date()
        trade_date = str(t['trade date']) + ' (' + str((
                datetime.strptime(t['file date'], '%Y-%m-%d').date() - datetime.strptime(
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

        party_state = getPartyState(t['senator'])
        if party_state[0] and party_state[1] != '':
            if party_state[0] == 'Republican':
                senator_info = t['senator'] + ' (R - ' + party_state[1] + ')'
            else:
                senator_info = t['senator'] + ' (D - ' + party_state[1] + ')'
        path = 'res/news/news_key.txt'
        list_of_titles_urls = getTradesNews(t, path)
        contact_info = getContactInfo(t['senator'])
        trades_for_txt.append(
            FormatFunctions.makeEmailDict(
                list_of_titles_urls, t, trade_date, senator_info,
                value_string, mkt_cap_string, contact_info
            )
        )

    return trades_for_txt

def sendEmails(trades, toList, toNewList):

    CLIENT_SECRET_FILE = 'res/gmail/senatetrades_gmailKeys.json'
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    SCOPES = ['https://mail.google.com/']

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    send_email = 'senatetrades@gmail.com'
    recipients = []

    if toList:
        list_path = 'res/mail_info/mailing_list.txt'
        with open(list_path,'r') as f:
            lines = f.readlines()
        for l in lines:
            recipients.append(l.strip())
    elif toNewList:
        list_path = 'res/mail_info/mailing_new.txt'
        with open(list_path,'r') as f:
            lines = f.readlines()
        for l in lines:
            recipients.append(l.strip())
    else:
        recipients = [send_email]

    recipients = ', '.join(recipients)
    for t in reversed(trades):
        html_write_path = 'res/html/alert_formatting/trade_for_html.txt'
        writeTradeToFile(t, html_write_path)

        with open(html_write_path,'r') as f:
            data = f.read()

        if len(data) != 0:
            message = MIMEMultipart('alternative')
            message['Subject'] = 'Trade Alert'
            message['From'] = formataddr(('SenateTrades', send_email))
            message['To'] = send_email
            message['Bcc'] = recipients

            body = MIMEText(data, 'plain')
            if len(t) == 17:
                html_string = FormatFunctions.getHTMLNews3(t)
            elif len(t) == 15:
                html_string = FormatFunctions.getHTMLNews2(t)
            elif len(t) == 13:
                html_string = FormatFunctions.getHTMLNews1(t)
            else:
                html_string = FormatFunctions.getHTMLNoNews(t)

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
        party_state = getPartyState(t['senator'])
        if party_state[0] and party_state[1] != '':
            if party_state[0] == 'Republican':
                senator_info = t['senator'] + ' (R - ' + party_state[1] + ')'
            else:
                senator_info = t['senator'] + ' (D - ' + party_state[1] + ')'
        trades_for_twitter.append(
            {
                'Ticker' : ticker,
                'Senator' : senator_info,
                'Value' : value_string,
                'Trade Date' : t['trade date'],
                'yahoo' : yahoo_link
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
        f.write('\nhttps://docs.google.com/spreadsheets/d/14eg98rZU5Rza-MeUQMQJAaJD90Iz4OwTniB5Pd4vrzE')

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
    for t in reversed(trades_for_twitter):
        writeTradeToFileTwitter(t, write_path)
        with open(write_path, 'r') as f:
            tweet_data = f.read()
        try:
            client.create_tweet(text=tweet_data)
        except tweepy.Forbidden:
            continue
        except tweepy.TwitterServerError:
            break

def getLatestTradecode(r):
    table = r.html.find('table')[0]
    tradecode =  table.find('tr')[2].text.split('\n')[1]
    return tradecode

def addToDashboard(t, row_path):
    SERVICE_ACCOUNT_FILE = 'res/sheets/senatetrades_sheetsKeys.json'
    credentials = service_account.Credentials.from_service_account_file(
        filename=SERVICE_ACCOUNT_FILE
    )
    service_sheets = build('sheets', 'v4', credentials=credentials)

    with open(row_path, 'r') as f:
        row = f.read() # row number of next empty row
    GOOGLE_SHEETS_ID ='1zSpyfOWCuUkW4yzCh-PnHx5Qv_WWFb3AsMnoXUjr8qk'
    worksheet = 'Dashboard!'
    cell_range_insert = 'B{}:I{}'.format(row,row)
    
    ticker = getTicker(t['trade'])
    sector = t['sector']
    senator = t['senator']
    party = getPartyState(t['senator'])[0]
    file_date = t['file date']
    price_at_filing = getOpen(getYahooInfo(ticker)[0])
    current_price = '=IFERROR(GOOGLEFINANCE(B{}),0)'.format(row)
    ret = '=(H{}-G{})/G{}'.format(row,row,row)
    values = (
        (ticker, senator, party, sector, file_date, price_at_filing, current_price, ret),
    )
    value_range_body = {
    'majorDimension' : 'ROWS',
    'values' : values
    }

    service_sheets.spreadsheets().values().update(
    spreadsheetId=GOOGLE_SHEETS_ID,
    valueInputOption='USER_ENTERED',
    range=worksheet + cell_range_insert,
    body=value_range_body
    ).execute()
    row = int(row) + 1
    with open(row_path, 'w') as f:
        f.write(str(row))

def updateSPPrice():
    price = getCurrentSP500Price()
    SERVICE_ACCOUNT_FILE = 'res/sheets/senatetrades_sheetsKeys.json'
    credentials = service_account.Credentials.from_service_account_file(
        filename=SERVICE_ACCOUNT_FILE
    )
    service_sheets = build('sheets', 'v4', credentials=credentials)
    GOOGLE_SHEETS_ID ='1zSpyfOWCuUkW4yzCh-PnHx5Qv_WWFb3AsMnoXUjr8qk'
    worksheet = 'Dashboard!'
    cell_range_insert = 'J2:K2'
    values = (
        (401.72, price),
    )
    value_range_body = {
        'majorDimension' : 'ROWS',
        'values' : values
    }
    service_sheets.spreadsheets().values().update(
    spreadsheetId=GOOGLE_SHEETS_ID,
    valueInputOption='USER_ENTERED',
    range=worksheet + cell_range_insert,
    body=value_range_body
    ).execute()

def main():

    onlyToday = True                     
    toList = True
    toNewList = False
    createPostFiles = True  
    tweet = True
    email = True   
    dashboard = True     
    backtestDate = '2022-10-14'
    twitter_write_path = 'res/twitter/write_for_twitter.txt'
    twitter_keys_path = 'res/twitter/keys.json'
    dashboard_row_path = 'res/sheets/row.txt'
    base_path = 'res/trade_posts'

    updateSPPrice()

    if onlyToday:
        url = 'https://sec.report/Senate-Stock-Disclosures'
        path = 'res/trade_info/last_tradecode.txt'
        with open(path, 'r') as f:
            last_tradecode = f.read()
        current_tradecode = getLatestTradecode(fetchSession(url))
        if current_tradecode == last_tradecode:
            exit()
        with open(path, 'w') as f:
            f.write(current_tradecode)

    trades = scrapeImportantTrades(
        onlyToday=onlyToday, backtest=not onlyToday, backtestDate=backtestDate
    )
    if len(trades) != 0:
        formatted_trades = formatForEmail(trades)
        if createPostFiles:
            generatePostFiles(formatted_trades=formatted_trades, base_path=base_path)
        if tweet:
            tweetTrades(
                trades_list=trades, write_path=twitter_write_path, 
                keys_path= twitter_keys_path
            )
        if email:
            sendEmails(
                trades=formatted_trades, toList=toList, toNewList=toNewList
            )
        if dashboard:
            for t in reversed(trades):
                addToDashboard(t, dashboard_row_path)

if __name__ == '__main__':
    main()