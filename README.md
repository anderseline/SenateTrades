# Welcome to SenateTrades!

<p>The goal of this program is to find small, under the radar companies whose equity has recently been disclosed as being purchased by US senators.</p>

[This python file](/main/ScrapeTradesToday.py) tracks market trading activity of US senators, and discerns which of these trades are of most interest. The script scrapes the [SEC EDGAR Insider Trading Disclosures List](https://sec.report/Senate-Stock-Disclosures) and searches for trades which have been filed on the current day (note that this includes a lag between the actual trading date, and the later filing date). The script then determines if the traded asset was purchased, and if the asset was an equity. If so, the equity market cap and trade size are measured to classify the trade as important, in which case an alert is sent via email, and over [twitter](https://twitter.com/Senate_Trades). All equity purchases of over $100,000, regardless of market cap, are important. Trades of medium cap firms (market cap between $2B and $10B) which value of at least $50,000 are important, and all small cap equities traded are important. This logic stems from the idea that a senator trading a very small bank, manufacturer, or other firm is significantly more interesting than trading a larger firm - think Google or Goldman Sachs. 

In addition, I also feed the equity information to [Google News](https://news.google.com/topstories?hl=en-US&gl=US&ceid=US:en), retrieve the top 3 most recent/relevant articles, and include these in the email alert. The ticker in the body header also contains a link to the equity's [Yahoo Finance](https://finance.yahoo.com/) description page. Here's an example of an alert email:

![](/res/repo_pics/sample_alert.JPG)

And a tweet:

![](/res/repo_pics/sample_tweet.JPG)

The program is run via a [batch file](/tools/run_trades.bat) at market close (4:00PM EST) to keep me updated on any potential trades that may be worth researching more. I made this as a side project while studying at Lehigh University, and I hope you find it interesting!

<b> If you are interested in being added to the email list, or have any other questions, please email:
ders.mailbot@gmail.com

Or, follow along on [twitter](https://twitter.com/Senate_Trades)
</b>

Credit to Jie Jenn for his [Gmail API Helper Script](https://learndataanalysis.org/how-to-use-gmail-api-to-send-an-email-in-python/), specifically his [Google.py](/main/Google.py) file.

![](/res/repo_pics/git_logo.JPG)