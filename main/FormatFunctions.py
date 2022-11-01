import re 

def getTicker(t):
    try:
        return re.findall('\[(.*?)\]', t)[0]
    except IndexError:
        return ''

def makeEmailDict(list_of_titles_urls, t, trade_date, senator_info, value_string, mkt_cap_string, contact_list):
    if list_of_titles_urls == -1:
        return (
            {
                'Trade Date' : trade_date,
                'File Date' : t['file date'],
                'Senator' : senator_info,
                'Equity' : t['trade'],
                'Trade Value' : value_string,
                'Market Cap' : mkt_cap_string,
                'Sector' : t['sector'],
                'Industry' : t['industry'],
                'Yahoo!' : t['yahoo finance'],
                'Lastname' : contact_list['lastname'],
                'Contact URL' : contact_list['url']
            }
        )
    elif len(list_of_titles_urls) == 1:
        return (
           {
                'Trade Date' : trade_date,
                'File Date' : t['file date'],
                'Senator' : senator_info,
                'Equity' : t['trade'],
                'Trade Value' : value_string,
                'Market Cap' : mkt_cap_string,
                'Sector' : t['sector'],
                'Industry' : t['industry'],
                'Yahoo!' : t['yahoo finance'],
                'Lastname' : contact_list['lastname'],
                'Contact URL' : contact_list['url'],
                'Title 1' : list_of_titles_urls[0]['title'], 
                'URL1' : list_of_titles_urls[0]['url']
           }
        )
    elif len(list_of_titles_urls) == 2:
        return (
           {
                'Trade Date' : trade_date,
                'File Date' : t['file date'],
                'Senator' : senator_info,
                'Equity' : t['trade'],
                'Trade Value' : value_string,
                'Market Cap' : mkt_cap_string,
                'Sector' : t['sector'],
                'Industry' : t['industry'],
                'Yahoo!' : t['yahoo finance'],
                'Lastname' : contact_list['lastname'],
                'Contact URL' : contact_list['url'],
                'Title 1' : list_of_titles_urls[0]['title'], 
                'Title 2' : list_of_titles_urls[1]['title'],  
                'URL1' : list_of_titles_urls[0]['url'],
                'URL2' : list_of_titles_urls[1]['url']
           }
        )
    else:
        return (
           {
                'Trade Date' : trade_date,
                'File Date' : t['file date'],
                'Senator' : senator_info,
                'Equity' : t['trade'],
                'Trade Value' : value_string,
                'Market Cap' : mkt_cap_string,
                'Sector' : t['sector'],
                'Industry' : t['industry'],
                'Yahoo!' : t['yahoo finance'],
                'Lastname' : contact_list['lastname'],
                'Contact URL' : contact_list['url'],
                'Title 1' : list_of_titles_urls[0]['title'], 
                'Title 2' : list_of_titles_urls[1]['title'],  
                'Title 3' : list_of_titles_urls[2]['title'], 
                'URL1' : list_of_titles_urls[0]['url'],
                'URL2' : list_of_titles_urls[1]['url'],
                'URL3' : list_of_titles_urls[2]['url']
           }
        )

def getHTMLNews3(t):
    path = '..\\res\\html\\alert_formatting\\format3.html'
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
                contact_url = t['Contact URL'],
                lastname = t['Lastname'],
                news_url1 = t['URL1'],
                news_title1 = t['Title 1'],
                news_url2 = t['URL2'],
                news_title2 = t['Title 2'],
                news_url3 = t['URL3'],
                news_title3 = t['Title 3']
            )

def getHTMLNews2(t):
    path = '..\\res\\html\\alert_formatting\\format2.html'
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
                contact_url = t['Contact URL'],
                lastname = t['Lastname'],
                news_url1 = t['URL1'],
                news_title1 = t['Title 1'],
                news_url2 = t['URL2'],
                news_title2 = t['Title 2']
            )

def getHTMLNews1(t):
    path = '..\\res\\html\\alert_formatting\\format1.html'
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
                contact_url = t['Contact URL'],
                lastname = t['Lastname'],
                news_url1 = t['URL1'],
                news_title1 = t['Title 1']
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
                ind  = t['Industry'],
                contact_url = t['Contact URL'],
                lastname = t['Lastname']
            )