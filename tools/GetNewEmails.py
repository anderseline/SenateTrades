import pandas as pd 

# run from Senate_Trades directory
# writes any emails in the emails.csv file that are not in the mailing_list to the new list, and to the end of the mailing list 
# download emails.csv into mail_info folder, and run this program to add all new names to mailing lists

def main():
    emails_path = 'res/mail_info/emails.csv'
    new_path = 'res/mail_info/mailing_new.txt'
    existing_path = 'res/mail_info/mailing_list.txt'
    emails = pd.read_csv(emails_path)
    try:
        emails = list(emails['Email Address'])
    except:
        emails = list(emails['Username'])

    # remove duplicates 
    emails = [*set(emails)]
    existing = []
    with open(existing_path, 'r') as f:
        lines = f.readlines()
        for l in lines:
            existing.append(l.strip())
    # overwrites existing data
    with open(new_path, 'w') as f:
        for i in emails:
            if i not in existing:
                f.write(i + '\n')
    # appends onto existing data
    with open(existing_path, 'a') as f:
        for i in emails:
            if i not in existing:
                f.write(i + '\n')

if __name__ == '__main__':
    main()