from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr 
from Google import Create_Service
import base64

SEND_TO_ALL = False
SEND_TO_NEW_LIST = True

subject = 'Welcome to SenateTrades!'

send_file = '..\\res\\html\\emails\\welcome.html'

recipients_path = '..\\res\\mail_info\\mailing_list.txt'
new_path = '..\\res\\mail_info\\mailing_new.txt'

CLIENT_SECRET_FILE = '..\\res\\gmail\\senatetrades_gmailKeys.json'
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
send_email = 'senatetrades@gmail.com'

with open(send_file, 'r') as f:
    content = f.read()

# get list of emails from text file in data folder 
recipients = []
if SEND_TO_ALL:
    with open(recipients_path) as f:
        lines = f.readlines()
    for l in lines:
        recipients.append(l.strip())
elif SEND_TO_NEW_LIST:
    with open(new_path) as f:
        lines = f.readlines()
    for l in lines:
        recipients.append(l.strip())
else:
    recipients = [send_email]

recipients = ', '.join(recipients)
print(recipients)

message = MIMEMultipart('alternative')
message['Subject'] = subject
message['From'] = formataddr(('SenateTrades', send_email))
message['to'] = send_email
message['Bcc'] = recipients

content = MIMEText(content, 'html')

message.attach(content)

raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode()
message = service.users().messages().send(userId='me', body={'raw':raw_string}).execute()