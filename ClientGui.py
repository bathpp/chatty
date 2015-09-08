from tkinter import *
import tkinter.messagebox
import socket, sys, traceback, os
import ast
from threading import Thread
import time

class Client:
	# Initiation..
	def __init__(self, master, serveraddr, serverport):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.logingui(1)
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.clientname =""
		self.connectToServer()
		self.requestSent=""
		self.reply=""
		self.chatlist={}

	'''Below are the GUI builder, there are GUI for log in, sign up, and main chat window.'''		
	def logingui(self, i):
		chatlogo=PhotoImage(file="chatlogo.gif")
		self.logo = Label(image=chatlogo)
		self.logo.image = chatlogo
		self.logo.pack()
		if i==1:
			self.frame = Frame(self.master, relief=RAISED, borderwidth=1)
			self.frame.pack(fill=BOTH, expand=1)
			self.nameentry = Entry(self.master, width=10)
			self.nameentry.pack(side=LEFT)
			self.passentry = Entry(self.master, show="*", width=10)
			self.passentry.pack(side=LEFT)

			self.log = Button(self.master, width=8, padx=3, pady=3)
			self.log["text"] = "Log in"
			self.log["command"] = self.login
			self.log.pack(side=LEFT)
		
			self.sign = Button(self.master, width=8, padx=3, pady=3)
			self.sign["text"] = "Sign up"
			self.sign["command"] = self.signup
			self.sign.pack(side=LEFT)
		
			self.teardown = Button(self.master, width=8, padx=3, pady=3)
			self.teardown["text"] = "Exit"
			self.teardown["command"] =  self.exitClient
			self.teardown.pack(side=LEFT)
		else:
			self.log["text"] = "Log in"
			self.log["command"] = self.login
			self.sign["text"] = "Sign up"
			self.sign["command"] = self.signup		

	def signupgui(self):		
		self.log["text"] = "Submit"
		self.log["command"] = self.submit

		self.sign["text"] = "Back"
		self.sign["command"] =  self.back

	def chatgui(self, friendlist):
		self.logo.destroy()
		self.nameentry.destroy()
		self.passentry.destroy()
		self.teardown.destroy()
		self.sign.destroy()
		self.log.destroy()
		
		self.chatbutton = Button(self.master, width=10, padx=3, pady=3)
		self.chatbutton["text"] = "Chat"
		self.chatbutton["command"] = self.chat
		self.chatbutton.pack(side=LEFT)		
		
		self.addbutton = Button(self.master, width=10, padx=3, pady=3)
		self.addbutton["text"] = "Add friend"
		self.addbutton["command"] = self.displayadd
		self.addbutton.pack(side=LEFT)
		
		self.teardown = Button(self.master, width=10, padx=3, pady=3)
		self.teardown["text"] = "Exit"
		self.teardown["command"] =  self.exitClient
		self.teardown.pack(side=LEFT)
		friendlist = ast.literal_eval(friendlist)
		self.lb = Listbox(self.master)
		#self.lb.bind("<Double-Button-1>", self.chat)
		for i in friendlist:
			self.lb.insert(END, i)
		self.lb.place(x=10, y=10)
		
	#Keep reading the reply from server, then update the friendlist or the chatting window
	def read(self):
		try:
			if (self.reply!=None):
				print("reading "+self.reply)
				if self.reply=="You guys are already friends!" or self.reply=="username doesn't exist":
					tkinter.messagebox.showinfo(self.reply,self.reply)
				
				index=self.reply.find(":")			
				try:
					friendlist = ast.literal_eval(self.reply)
					self.lb.destroy()
					self.lb = Listbox(self.master)
					#self.lb.bind("<Double-Button-1>", self.chat)
					for i in friendlist:
						self.lb.insert(END, i)
					self.lb.place(x=10, y=10)
					self.reply=None
				except:
					if index!=-1:
						sender=self.reply[0:index]
						msg=self.reply[index+1:]
						self.chatwindow(sender, msg)
							
					
					self.reply=None
		except:
			pass
		self.master.after(1000,self.read)
		self.reply=None

	#Get reply from server	
	def getreply(self):
		while True:
			self.reply=(self.chatSocket.recv(1024).decode())

		
	'''Below are the funtions on the GUI window, the function name is the button name'''
	#log in button
	def login(self):
		self.username = self.nameentry.get().replace(' ', '')
		self.password = self.passentry.get().replace(' ', '')
		if self.username=="" or self.password=="":
			tkinter.messagebox.showinfo("Enter","Empty input")	
		else:
			self.sendChatRequest("login")
			reply = self.chatSocket.recv(1024).decode()
			
			if reply=="incorrect name/password" or reply=="User already logged in":
				tkinter.messagebox.showwarning(reply,reply)
			else:
				self.chatgui(reply)
				self.master.title("Welcom "+self.username)
				t1=Thread(target=self.getreply)
				t1.setDaemon(1)
				t1.start()
				self.master.after(500,self.read)
	
	#Sign up button, call the sign up window		
	def signup(self):
		self.signupgui()	
	
	#Submit button, check if the info not empty, send the signup request
	def submit(self):
		username = self.nameentry.get().replace(' ', '')
		password = self.passentry.get().replace(' ', '')
		
		if username=="" or password=="":
			tkinter.messagebox.showinfo("Enter","Empty input")	
		else:
			self.sendChatRequest("signup")
			self.reply=(self.chatSocket.recv(1024).decode())
			tkinter.messagebox.showinfo(self.reply,self.reply)

	#Back button, back to login window
	def back(self):
		self.logingui(0)

	#Chat button, if there is a selection on friendlist, then a chat window will be called
	def chat(self):
		try:
			index = self.lb.curselection()[0]
			self.receiver = self.lb.get(index)
			index1 = self.receiver.find("(")
			self.receiver = self.receiver[0:index1]
			statu = self.lb.get(index)[index1+1:index1+4]
			if statu=="off":
				tkinter.messagebox.showinfo("user not online", "user not online")
			else:
				self.chatwindow(self.receiver, "")
				
		except:
			tkinter.messagebox.showinfo("wrong","You didn't select a person to chat")
	
	#Add friend button, will send add friend request after valid input
	def addfriend(self):
		if self.addfrd.get()=="":
			tkinter.messagebox.showinfo("Enter","Empty input")	
		else:
			self.sendChatRequest("addfriend")
			self.read
			self.addfrd.destroy()
			self.add.destroy()
	'''Create or update a chatting window GUI, store all the windows in the chatlist dictinary,
		key is the chatting partners(withwho), and value is the the Toplevel window object,
		so that it could handle multiple chat ''' 
	def chatwindow(self, withwho, msg):
		if withwho not in self.chatlist:
			self.chatlist[withwho] = Toplevel()
			self.chatlist[withwho].protocol("WM_DELETE_WINDOW", self.handler1)
			frame = Frame(self.chatlist[withwho], relief=RAISED, borderwidth=1)
			frame.pack(fill=BOTH, expand=1)
			self.chatlist[withwho].geometry("300x300+300+300")
			self.chatlist[withwho].title("With "+ withwho)
			self.chatlist[withwho].sendbutton = Button(self.chatlist[withwho], width=10, padx=3, pady=3)
			self.chatlist[withwho].sendbutton["text"] = "Send"
			self.chatlist[withwho].sendbutton.bind("<Button-1>", self.sendmsg )
			self.chatlist[withwho].msgentry = Entry(self.chatlist[withwho], width=30)
			self.chatlist[withwho].msgentry.bind('<Return>', self.sendmsg )
			self.chatlist[withwho].msgentry.pack(side=LEFT)
			#Bind the command on the msgentry, so when typing message it will make the receiver be the current chat window receiver
			self.chatlist[withwho].msgentry.bind("<Button-1>", lambda event, arg=withwho: self.setrecv(event, arg))
			self.chatlist[withwho].sendbutton.pack(side=LEFT)
			self.chatlist[withwho].msgs = Text(self.chatlist[withwho])
			if msg!="":
				self.chatlist[withwho].msgs.insert(END, withwho+": "+msg+"\n")
			self.chatlist[withwho].msgs.config(state=NORMAL, width=40, height=15)
			self.chatlist[withwho].msgs.place(x=5, y=5)
			
		else:
			if msg!="":
				self.chatlist[withwho].msgs.insert(END, withwho+": "+msg+"\n")
	
	#Set the receiver to the current chat window, so the msg will send to the right receiver
	def setrecv(self, event, arg):
		self.receiver=arg		
	
	#The send message button function on the chat window, it sends the chat request
	def sendmsg(self,event):
		sender=self.clientname
		withwho=self.receiver
		if self.chatlist[withwho].msgentry.get()!='':
			self.chatlist[withwho].msgs.insert(END, "You: "+self.chatlist[withwho].msgentry.get()+"\n")
			self.sendChatRequest("chat")
			self.chatlist[withwho].msgentry.delete(0, END)
	
	#Display the add friend field when click addfriend button
	def displayadd(self):
		self.addfrd = Entry(self.master, width=10)
		self.addfrd.pack(side=LEFT)
		self.add = Button(self.master, width=8, padx=3, pady=3)
		self.add["text"] = "Add"
		self.add["command"] = self.addfriend
		self.add.pack(side=LEFT)
		
	#Exit, send exit request
	def exitClient(self):
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):	
			self.master.destroy()
			self.chatting=0 
			self.sendChatRequest("exit")
			sys.exit()		
	
	def connectToServer(self):
		
		self.chatSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.chatSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
			self.exitClient() 

	#Send request to server, the requestCode showing the request
	def sendChatRequest(self, requestCode):
		#Format
		#username:password:sender:receiver:function:msg

		if requestCode == "login":
			self.clientname=self.username
			request = "%s:%s:%s:%s:%s:%s" % (self.username, self.password, "", "", "fun0" , "")
			self.requestSent="login"

		elif requestCode == "signup":
			username = self.nameentry.get()
			password = self.passentry.get()
			request = "%s:%s:%s:%s:%s:%s" % (username, password, "", "", "fun1", "")
			self.requestSent="signup"
		
		elif requestCode == "chat":
			sender=self.clientname
			receiver=self.receiver
			msg = self.chatlist[receiver].msgentry.get()
			request = "%s:%s:%s:%s:%s:%s" % ("", "", sender, receiver, "fun2", msg)
			self.requestSent="chat"

		elif requestCode == "addfriend":
			sender=self.clientname
			friendtoadd=self.addfrd.get()
			request = "%s:%s:%s:%s:%s:%s" % ("", "", sender, friendtoadd, "fun3", "")
			self.requestSent="addfriend"

		elif requestCode == "exit":
			sender=self.clientname
			request = "%s:%s:%s:%s:%s:%s" % ("", "", sender, "", "fun4", "")
			self.requestSent="exit"
			
		self.chatSocket.send(request.encode())
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.exitClient()
		
	def handler1(self):
		"""Handler on explicitly closing the ChatGUI window."""
		self.chatlist[self.receiver].destroy()
		del self.chatlist[self.receiver]


if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port]\n")
	
	root = Tk()
	root.geometry("400x400+300+300")
	
	client = Client(root, serverAddr, serverPort)
	client.master.title("ChattyChat")	
	root.mainloop()

