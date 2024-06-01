from tkinter import *
import os
import threading
from datetime import timedelta
import time
import yaml
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

stream = open('credentials.yaml', 'r')    # 'document.yaml' contains a single YAML document.
yamlObject = yaml.safe_load(stream)

uri = "mongodb+srv://leocrabe225:" + yamlObject['password'] + "@timeallocator.xiz3fxq.mongodb.net/?retryWrites=true&w=majority&appName=TimeAllocator"
client = MongoClient(uri, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["main"]

collection = db['main']

class Job:
	def __init__(self, button, label, name_label, time):
		self.button = button
		self.label = label
		self.name_label = name_label
		self.time = time
		self.last_save = time
		self.session_time = 0
		self.state = False

	def update_label(self):
		if (self.state):
			self.label.configure(text = timedelta(seconds=self.time // (3600 * WORK_DAY_LENGHT) * 86400 + self.time % (3600 * WORK_DAY_LENGHT)))


def update_job(job_name, seconds_worked, creation):
	if (creation):
		collection.insert_one({
			"jobName":job_name,
			"seconds":seconds_worked
		})
	else :
		collection.update_one({"jobName":job_name}, {
			'$set': {"seconds":seconds_worked}
		})

def activate_job(job_name):
	global job_dict, ongoing_jobs
	job = job_dict[job_name]
	if (not job.state):
		if (job_name != "Session"):
			if (ongoing_jobs == 0 ):
				activate_job("Session")
			ongoing_jobs += 1
		
		job.state = True
		if (job_name != "Session"):
			job.button.configure(text = "Deactivate job")
		job.session_time = 0
		job.start_time = time.time()
		t1 = threading.Timer(1.0, lambda: job_time_routine(job_name))
		t1.daemon = True
		t1.start()
	else:
		if (job_name != "Session"):
			ongoing_jobs -= 1
			if (ongoing_jobs == 0):
				activate_job("Session")
			job.button.configure(text = "Activate job")
		job.state = False
        

def read_jobs():
	global job_dict, window

	for job in collection.find({}):
		job_name = job['jobName']
		time_worked = int(job['seconds'])
		button_activate_job = Button(window, text="Activate job", command= lambda par=job_name: activate_job(par))
		button_activate_job.place(x=0, y=50 + 50 * len(job_dict) + SESSION_OFFSET, anchor=NW)
		label_job_time = Label(window, text=timedelta(seconds=time_worked // (3600 * WORK_DAY_LENGHT) * 86400 + time_worked % (3600 * WORK_DAY_LENGHT)), bg='#505050')
		label_job_time.place(x=85, y=50 + 50 * len(job_dict) + SESSION_OFFSET, anchor=NW)
		label_job_name = Label(window, text=job_name, bg='#505050')
		label_job_name.place(x=190, y=50 + 50 * len(job_dict) + SESSION_OFFSET, anchor=NW)

		job_dict[job_name] = Job(button_activate_job, label_job_time, label_job_name, time_worked)

def create_job():
	global entry_create_job, job_dict, window

	job_name = entry_create_job.get()
	if (not os.path.exists(SAVE_FOLDER + job_name)):
		entry_create_job.delete(0, END)
		update_job(job_name, 0, True)

		button_activate_job = Button(window, text="Activate job", command= lambda par=job_name: activate_job(par))
		button_activate_job.place(x=0, y=50 + 50 * len(job_dict) + SESSION_OFFSET, anchor=NW)
		label_job_time = Label(window, text="0:00:00", bg='#505050')
		label_job_time.place(x=85, y=50 + 50 * len(job_dict) + SESSION_OFFSET, anchor=NW)
		label_job_name = Label(window, text=job_name, bg='#505050')
		label_job_name.place(x=190, y=50 + 50 * len(job_dict) + SESSION_OFFSET, anchor=NW)

		job_dict[job_name] = Job(button_activate_job, label_job_time, label_job_name, 0)
	else:
		pass #case where the job already exists

def job_time_routine(job_name):
	global job_dict, ongoing_jobs
	job = job_dict[job_name]
	print(ongoing_jobs)
	if (job.state and ongoing_jobs >= 1):
		job.time += 1
		job.session_time += 1
		job.update_label()
		if (job.time - job.last_save >= 60 and job_name != "Session"):
			job.last_save = job.time
			update_job(job_name, job.time, False)
		t1 = threading.Timer(1.0 - (time.time() - job.start_time - job.session_time), lambda: job_time_routine(job_name))
		t1.daemon = True
		t1.start()
	else:
		job.last_save = job.time
		if (job_name != "Session"):
			update_job(job_name, job.time, False)

WORK_DAY_LENGHT = 7
WINDOW_HEIGHT = 500
WINDOW_WIDTH = 400
SESSION_OFFSET = 50
SAVE_FOLDER = "projects_data/"

job_dict = {}
ongoing_jobs = 0

window = Tk()
window.title('Time allocator')
window.configure(bg='#505050', width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

button_create_job = Button(window, text="Create new job", command= create_job)
button_create_job.place(x=0, y=0 + SESSION_OFFSET, anchor=NW)

entry_create_job = Entry(window, width=20)
entry_create_job.place (x=100,y=0  + SESSION_OFFSET, anchor=NW)

session_job_time = Label(window, text=timedelta(seconds=0), bg='#505050')
session_job_time.place(x=0, y=0, anchor=NW)
session_job_name = Label(window, text="Session", bg='#505050')
session_job_name.place(x=105, y=0, anchor=NW)
session_job =  Job(None, session_job_time, session_job_name, 0)

read_jobs()
job_dict["Session"] = session_job

window.mainloop()



#command= lambda: temp(cookie, actual_cookie, text_list, buildings)
#def temp(cookie, actual_cookie, text_list, buildings):
#text_list.append(Label(window, text=cookie.buy_next_one(),font=("Courier", 30), bg="black", fg="white"))
'''t1 = threading.Timer(5.0, refresh_watcher)
t1.daemon = True
t1.start()'''