import smtplib


def send_email(subject, msg, receiver):
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login("smart.hive.vb@gmail.com", "dinoaiezza")
        message = 'Subject: {}\n\n{}'.format(subject.format(), msg)
        server.sendmail("smart.hive.vb@gmail.com", receiver, message)
        server.quit()
        print("Success: Email sent!")
    except:
        print("Email failed to send.")
