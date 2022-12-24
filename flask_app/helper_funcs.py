from flask_app import app
from flask_app.models import User, List, Card
import matplotlib.pyplot as plt
import os, pdfkit, time
from datetime import datetime
from jinja2 import FileSystemLoader, Environment

# set up jinja for rendering the pdf template
templateLoader = FileSystemLoader(searchpath="./flask_app/templates")
templateEnv = Environment(loader=templateLoader)
TEMPLATE_FILE = "pdfstats.html"
template = templateEnv.get_template("pdfstats.html") #gets the "pdfstats.html" file from the templates folder

def make_plot(list_id):
    #make a pie chart using the data from this list
    list_obj = List.query.get(list_id)
    total_cards = len(list_obj.cards)
    if total_cards != 0:
        completed_cards = len(Card.query.filter_by(list_id=list_id, status='Completed').all()) #fetches all the 'Completed' cards lying inside this list
        pending_cards = 0
        current_date = datetime.today().date()
        deadlines_missed = 0
        for card in list_obj.cards:
            if card.status == "Pending" and current_date < card.deadline:
                # a card is considered pending if its status is pending and if current date is less than deadline date
                pending_cards += 1
            elif card.status == "Pending" and current_date > card.deadline:
                # a card is considered 'missed' if its status is pending and if current date is past the deadline date
                deadlines_missed += 1
        
        # Data to plot
        my_data = [completed_cards, pending_cards, deadlines_missed]
        my_labels = 'Completed', 'Pending', 'Deadlines Missed'
        fig, ax = plt.subplots(figsize=(3.5,3.5))
        fig.set_facecolor('#f8f8ff') # set the background color of the pie chart
        colors = ['yellowgreen', 'gold', 'coral'] # colors to be used for the pies

        # Plot the chart
        plt.pie(my_data, colors=colors) #to show percentages use: autopct='%1.1f%%'
        plt.legend(labels=my_labels, loc='upper right')
        plt.axis('equal')
        #each image is of the form "list_{list_id}.jpeg", eg: list_1.jpeg. Each image corresponds to stats about that particular list.
        plt.savefig(f"flask_app/static/images/list_{list_id}.jpeg", dpi=300)
        plt.close()
        # return some quick stats and info in json
        return {"list_id" : list_id, "list_title" : list_obj.list_title, "total_cards" : total_cards, 
                "completed_cards" : completed_cards, "pending_cards" : pending_cards, "deadlines_missed" : deadlines_missed}
        # return "Charts generated successfully."
    else: 
        # the case when the list is empty, doesn't have any cards.
        return {"list_id" : list_id, "list_title" : list_obj.list_title, "total_cards" : 0, 
            "completed_cards" : 0, "pending_cards" : 0, "deadlines_missed" : 0,
            "error" : "List is empty. Can't generate meaningful stats."}

def get_stats(username):
    # get the details/stats of all the lists of this user 
    user = User.query.filter_by(username=username).first()
    list_stats = []
    for lst in user.lists:
        #make_plot() generates a pie chart for this list and also returns
        #a dictionary containing the stats for this list
        data = make_plot(lst.list_id)
        list_stats.append(data)
    return list_stats # this list contains the stats for all the lists in the user's dashboard.

def make_pdf(username):
    # makes a pdf report for this user
    list_stats = get_stats(username)
    rendered = template.render(username=username, lists=list_stats, cwd_path=os.getcwd(), creation_time=time.asctime())
    # make a pdf from this template, apply the given css file and save it to the required location
    pdfkit.from_string(rendered, f"./flask_app/user_reports/{username}_report.pdf", css="./flask_app/static/style.css", options={"enable-local-file-access" : ""})