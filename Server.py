import socket 
from time import ctime
import sys
from threading import Thread
import time
import os
import ast

argv = sys.argv 
PORT = int(argv[1])
HOST =  socket.gethostname()
BUFSIZE = 1024
ADDRESS = (HOST, PORT)
online = {}
passwords=''
friendlist=''


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDRESS)
server.listen(5)
print('Server is running ...', HOST)

class ClientHandler (Thread):
	def __init__(self, client, clientaddress):
		Thread.__init__(self, name = "My Thread")
		self._client=client
		self._clientaddress=clientaddress

	'''We have two files that store users' info, one contains the friendlist, one contains the passwords,
		we will reread the files anytime they have an change'''
	def run(self):
		passwords = open('userpass','r')
		passwords = ast.literal_eval(passwords.readline())
		friendlist = open('userfriends','r')
		friendlist = ast.literal_eval(friendlist.readline())
		running=1
		while running:
			clientData = self._client.recv(BUFSIZE).decode()
			index = clientData.find("fun")
			clientData1 = clientData[0: index+4]
			msg = clientData[index+5:]
			clientData1 = clientData1.split(":")
			#username:password:sender:receiver:function:msg
			username=clientData1[0]
			password=clientData1[1]
			sender=clientData1[2]
			receiver=clientData1[3]
			function=clientData1[4]

			#login, check if the login info correct
			if function=='fun0':
				if username in online:
					reply="User already logged in"
					self._client.send(reply.encode())
				elif username in passwords.keys() and password==passwords[username]:
					online[username]=self._client					
					#User goes online, send online notice to all of his friends
					for user in online:
						reply=friendlist[user]
						reply1=[]
						for i in reply:
							if i in online:
								i=i+"(online)"
							else:
								i=i+"(offline)"
							reply1.append(i)
						online[user].send(str(reply1).encode())
						print(reply1)
				else:
					reply="incorrect name/password"
					self._client.send(reply.encode())
					print(reply)
				
			#signup, check if the sign up info is valid
			elif function=='fun1':
				if username in passwords.keys():
					reply="username already exist"
					self._client.send(reply.encode())
				else:
					#Check the sign up infomation and reply
					passwords[username]=password
					friendlist[username]=[]
					os.remove('userfriends')
					os.remove('userpass')
					f=open('userpass', 'w')
					f.write(str(passwords))
					f1=open('userfriends', 'w')
					f1.write(str(friendlist))
					f.close()
					f1.close()
					reply="Sign up sccessfully"
					passwords = open('userpass','r')
					passwords = ast.literal_eval(passwords.readline())
					friendlist = open('userfriends','r')
					friendlist = ast.literal_eval(friendlist.readline())
					self._client.send(reply.encode())
				print(reply)

			#chat, we have a online{} dictionary store the online user and their address,
			#So the server will redirect the msg from client to the right receiver
			elif function=='fun2':
				msg= sender+":"+msg
				online[receiver].send(msg.encode())
				print(msg)

			#addfriend, it checks if the friendtoadd exists, or the user already has that friend,
			#reply client the new friendlist if add friend successful.
			elif function=='fun3':
				if receiver not in passwords.keys():
					reply="username doesn't exist"
					self._client.send(reply.encode())
				else:
					fl=friendlist
					#write to file to update the friend list
					if receiver not in fl[sender]:
						fl[sender].append(receiver)
						fl[receiver].append(sender)
						os.remove('userfriends')
						f=open('userfriends', 'w')
						f.write(str(fl))
						f.close()
						#read files to get the updated friend list
						passwords = open('userpass','r')
						passwords = ast.literal_eval(passwords.readline())
						friendlist = open('userfriends','r')
						friendlist = ast.literal_eval(friendlist.readline())
						#update the friend list for this user 
						reply=friendlist[receiver]
						reply1=[]
						for i in reply:
							if i in online:
								i=i+"(online)"
							else:
								i=i+"(offline)"
							reply1.append(i)
						if receiver in online:
							online[receiver].send(str(reply1).encode())
						#update the friend list for that just added friend
						reply=friendlist[sender]
						reply1=[]
						for i in reply:
							if i in online:
								i=i+"(online)"
							else:
								i=i+"(offline)"
							reply1.append(i)
						online[sender].send(str(reply1).encode())
					else:
						reply="You guys are already friends!"
						self._client.send(reply.encode())
				print(reply)

			#exit, delete the user from the online{} dictionary.
			elif function=='fun4':
				try:
					del online[sender]
					passwords = open('userpass','r')
					passwords = ast.literal_eval(passwords.readline())
					friendlist = open('userfriends','r')
					friendlist = ast.literal_eval(friendlist.readline())
					#update the user to be offline to his friends
					for user in online:
						reply=friendlist[user]
						reply1=[]
						for i in reply:
							if i in online:
								i=i+"(online)"
							else:
								i=i+"(offline)"
							reply1.append(i)
						print(reply1)
						online[user].send(str(reply1).encode())
					self._client.close()
					running =0
				except:
					self._client.close()
					running =0
				print("closing")
				print("closed" + str(self._clientaddress))
				
				
			
		print('Server is running ...', HOST)
				
if __name__=="__main__":
	while True:
		client, clientaddress = server.accept()
		print('... connected from: ', client, clientaddress)
		Handler=ClientHandler(client, clientaddress)
		Handler.start()



