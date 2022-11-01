import re 

def getTicker(t):
    try:
        return re.findall('\[(.*?)\]', t)[0]
    except IndexError:
        return ''

def getLastname(senator):
    lastname = senator
    if ',' in senator:
        lastname = senator.split(',')[0]
    ind = len(lastname.split(' '))
    lastname = lastname.split(' ')[ind-1]
    return lastname

def generatePostFiles(formatted_trades, base_path):
    for t in formatted_trades:
        # get all necessary variables to reference in post 
        trade_date = t['Trade Date']
        file_date = t['File Date']
        senator = t['Senator'].split('(')[0][:-1] # remove party information and take off space after name
        partyAbbr = t['Senator'].split('(')[1][0] # R or D
        if partyAbbr == 'R':
            party = 'Republican'
        else:
            party = 'Democratic'
        equity = t['Equity']
        ticker = getTicker(equity)
        value = t['Trade Value']
        mkt_cap = t['Market Cap']
        sect = t['Sector']
        ind = t['Industry']
        y_link = t['Yahoo!']
        try:
            title1 = t['Title 1']
            url1 = t['URL1']
        except:
            title1 = None
            url1 = None 
        try:
            title2 = t['Title 2']
            url2 = t['URL2']
        except:
            title2 = None
            url2 = None 
        try:
            title3 = t['Title 3']
            url3 = t['URL3']
        except:
            title3 = None
            url3 = None 
        lastname = getLastname(senator)
        contact = t['Contact URL']

        # create as text file for now (attempt to use mdutils later?)
        title = t['File Date'] + '-' + ticker + '-' + lastname + '.txt'
        path = base_path + '\\' + title
        # create each line in the file (ending each with '\n')
        lines = []
        lines.append('---\nlayout: post\n')
        lines.append('title: ' + equity + '\n')
        lines.append('subtitle: Senator - ' + senator + '\n')
        lines.append('gh-repo: anderseline/senatetrades.io\n')
        tags = ('tags: [' + ticker + ', ' + senator + ', ' 
        + party + ', ' + sect + ', ' + ind + ', ' + mkt_cap + ']\n')
        # method for remove ascii characters which are unrenderable (handling depends on where they appear)
        tags_enc = tags.encode('ascii', 'replace')
        tags_dec = tags_enc.decode()
        tags_dec = tags_dec.replace("?", ", ")
        lines.append(tags_dec)
        lines.append('comments: true\n')
        lines.append('---\n\n')
        lines.append('# New Trade: [' + ticker + '](' + y_link + ') #\n')
        lines.append('<b>Trade Date: </b>' + trade_date + '<br>\n')
        lines.append('<b>File Date: </b>' + file_date + '<br>\n')
        lines.append('<b>Senator: </b>' + t['Senator'] + '<br>\n')
        lines.append('<b>Equity: </b>' + equity + '<br>\n')
        lines.append('<b>Trade Value: </b>' + value + '<br>\n')
        lines.append('<b>Market Cap: </b>' + mkt_cap + '<br>\n')
        sect_ind = ('<b>Sector: </b>' + sect + ' <i>(' + ind + ')</i><br>\n')
        sect_ind_enc = sect_ind.encode('ascii', 'replace')
        sect_ind_dec = sect_ind_enc.decode()
        sect_ind_dec = sect_ind_dec.replace('?', ' ')
        lines.append(sect_ind_dec)
        if title1 != None:
            lines.append('<b>Recent Articles:</b>\n')
            title_url = ('- [' + title1 + '](' + url1 + ')\n')
            title_url = title_url.replace('|', '')
            title_url_enc = title_url.encode('ascii', 'ignore')
            title_url_dec = title_url_enc.decode()
            lines.append(title_url_dec)
        if title2 != None:
            title_url = ('- [' + title2 + '](' + url2 + ')\n')
            title_url = title_url.replace('|', '')
            title_url_enc = title_url.encode('ascii', 'ignore')
            title_url_dec = title_url_enc.decode()
            lines.append(title_url_dec)
        if title3 != None:
            title_url = ('- [' + title3 + '](' + url3 + ')\n')
            title_url = title_url.replace('|', '')
            title_url_enc = title_url.encode('ascii', 'ignore')
            title_url_dec = title_url_enc.decode()
            lines.append(title_url_dec)
        lines.append('\n[Contact Senator ' + lastname + '](' + contact + ')')
        with open(path, 'w') as f:
            f.writelines(lines)