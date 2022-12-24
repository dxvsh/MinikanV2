import os, time, pdfkit
from celery import Celery
from celery.schedules import crontab
from flask_app.models import User, List, Card
from flask_app.helper_funcs import make_pdf
from redmail import EmailSender
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# load variables from .env
load_dotenv('./flask_app/.env')
username = os.environ.get('USER_EMAIL') #sender's email address
password = os.environ.get('PASSWORD') #sender's password
host = os.environ.get('HOST')
port = os.environ.get('PORT')
timezone = os.environ.get('TIMEZONE') 

# instantiating EmailSender, this will be used to send emails 
email = EmailSender(
    host=host,
    port=port,
    username=username,
    password=password
)

# creating a celery instance, specifying the broker and the results backend as redis
cel = Celery('tasks', broker='redis://localhost', backend='redis://localhost')

cel.conf.timezone = timezone #fetch the timezone from the environment variable
cel.conf.enable_utc = False

@cel.task
def generate_csv(username):
    # generate a csv file containing all the data about user's lists and cards
    usr_obj = User.query.filter_by(username=username).first()
    f = open('./flask_app/exported_content.csv', 'w')
    f.write('List ID, List Title, Card ID, Card Title, Card Content, Card Status, Card Deadline\n')
    for lst in usr_obj.lists:
        for card in lst.cards:
            f.write(f'{lst.list_id},"{lst.list_title}",{card.card_id},"{card.card_title}","{card.card_content}",{card.status},{card.deadline}\n')
    f.close()
    return "CSV Generated"

@cel.task
def generate_list_csv(list_id):
    # generate a csv file containing data only about the given list and its cards
    list_obj = List.query.get(list_id)
    f = open('./flask_app/exported_content.csv', 'w')
    f.write('List ID, List Title, Card ID, Card Title, Card Content, Card Status, Card Deadline\n')
    for card in list_obj.cards:
            f.write(f'{list_obj.list_id},"{list_obj.list_title}",{card.card_id},"{card.card_title}","{card.card_content}",{card.status},{card.deadline}\n')
    f.close()
    return "List CSV Generated"

def has_pending_cards(user):
    # return true if a user object has pending cards, false otherwise
    current_date = datetime.today().date()
    for lst in user.lists:
        for card in lst.cards:
            if card.status == "Pending" and current_date < card.deadline:
                # a card is considered pending if its status is pending and if current date is less than deadline date
                return True
    return False

def pending_users():
    # return a list of user emails that have pending tasks in their dashboard.
    users = User.query.all()
    emails = [] # this list holds emails of any user that has pending tasks
    for user in users:
        if has_pending_cards(user):
            emails.append(user.email)
    return emails

@cel.task
def periodic_email_reminder():
    user_emails = pending_users()
    if len(user_emails) != 0:
        email.send(
            subject="Minikan : Periodic Reminder",
            sender="Minikan" + "<" + email.username + ">",
            receivers=user_emails, # send mail to all these guys
            text=f"This is a scheduled periodic reminder to help you keep track of your tasks. As of {time.asctime()}, you have pending tasks remaining!",
        )
        print(f"Reminder emails were sent successfully to the following users : {user_emails}")
    else:
        print("None of the users have pending tasks. No emails to be sent!")

def send_pdf(username):
    user = User.query.filter_by(username=username).first()
    make_pdf(username)
    email.send(
        subject="Minikan : Monthly Stats Report",
        sender="Minikan" + "<" + email.username + ">",
        receivers=[user.email], # send the email to this particular user.
        text=f"Hi {username}! Your monthly stats report is here!",
        attachments={
            f"{username}_report.pdf" : Path(f'./flask_app/user_reports/{username}_report.pdf')
        }
    )
    print(f"The pdf report was successfully sent to {user.email}!")

@cel.task
def send_monthly_reports():
    users = User.query.all()
    for user in users:
        if len(user.lists) > 0: # Only send reports for users that have > 0 lists
            send_pdf(user.username)
            time.sleep(10) # add a slight delay between emails, so as not to trigger any spam mechanisms or going over the sending limits

@cel.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls the function periodic_email_reminder every 60 seconds.
    sender.add_periodic_task(60.0, periodic_email_reminder.s(), name='send every minute')

    # send the periodic emails everyday at 5PM 
    # sender.add_periodic_task(
    #     crontab(hour=17, minute=0),
    #     periodic_email_reminder.s(),
    #     name = 'send everyday at 5:00PM'
    # )

    sender.add_periodic_task(300.0, send_monthly_reports.s(), name='send every 5 minutes')

    # send the monthly reports at the start of every month
    # sender.add_periodic_task(
    #     crontab(hour=0, minute=0, day_of_month=1),
    #     send_monthly_reports.s(),
    #     name = 'send at the start of the month'
    # )