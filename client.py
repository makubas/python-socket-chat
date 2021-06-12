import os
import pickle
import socket
import threading
import tkinter as tk
from tkinter import *
from tkinter.ttk import *

from config import *


def on_window_close():
    """ Handle action after closing tkinter window """
    clientApp.connected = False
    ClientNetwork.send_to_server({
        "type": "disconnect"
    })
    root.destroy()


def do_nothing():
    """ Pass - function """
    pass


class Client(tk.Frame):

    def __init__(self, master):
        """ Client __init__ function
        Creates window and core variables
        """
        self.master = master
        Frame.__init__(self, self.master)
        self.pack(fill='both', expand=True)
        root.geometry("284x200")
        root.title("Chat")

        self.username = DEFAULT_USERNAME
        self.clientAdress = None
        self.currentLogLine = 1
        self.log_num = "1"

        self.clientDirectoryPath = os.path.abspath(os.getcwd())
        self.clientStylePath = os.path.join(self.clientDirectoryPath, "styles")


        root.call('lappend', 'auto_path', self.clientStylePath)
        root.call('package', 'require', 'awdark')
        style = Style(root)
        style.theme_use("awdark")



        self.create_widgets_connection_window()

    # ------------------------------------------
    # Tkinter Gui functions

    def create_widgets_connection_window(self):
        """ Creates widgets for connection window """
        self.connectionFrame = Frame(self)
        self.connectionFrame.grid(row=0, column=0, sticky=NSEW)

        usernameEntry = Entry(self.connectionFrame, font=('Helvetica', 18), width=20)
        usernameEntry.grid(row=1, column=0, padx=5, columnspan=2)
        adressEntry = Entry(self.connectionFrame, font=('Helvetica', 18), width=20)
        adressEntry.grid(row=3, column=0, sticky=W, padx=5)
        adressEntry.bind('<Return>', lambda event: self.connect_to_server(str(usernameEntry.get()), adressEntry.get()))
        usernameText = Label(self.connectionFrame, text="Username:", font=('Helvetica', 12), foreground="black")
        usernameText.grid(row=0, column=0, sticky=W, padx=8, pady=3)
        adressText = Label(self.connectionFrame, text="Sever adress:", font=('Helvetica', 12), foreground="black")
        adressText.grid(row=2, column=0, sticky=W, padx=8, pady=3)
        connectButton = tk.Button(self.connectionFrame, text="Connect",
                                  font=('Helvetica', 18), bg="#1bb520", width=8, activebackground="#06780a",
                                  bd=1,
                                  command=lambda: self.connect_to_server(str(usernameEntry.get()), adressEntry.get()))
        connectButton.grid(row=5, column=0, pady=16)

    def create_widgets_main_window(self):
        """ Creates widgets for main chat window """
        self.clientFrame = Frame(self)
        self.clientFrame.grid(row=0, column=0, sticky=NSEW)
        self.clientFrame.pack(side="top", fill="both", expand=True)
        self.clientFrame.grid_propagate(False)

        self.messageSendEntry = Entry(self.clientFrame, font=('Helvetica', 14), width=14)
        self.messageSendEntry.pack(side="bottom", fill="x")
        self.messageSendEntry.bind('<Return>', lambda event: self.send_chat_to_server({
            "type": "chatMessageSent",
            "fromWho": self.clientAdress,
            "messageData": self.messageSendEntry.get()
        }))
        self.messageSendEntry.bind('<FocusIn>', self.on_message_focus_in)
        self.messageSendEntry.bind('<FocusOut>', self.on_message_focus_out)
        self.messageSendEntry.insert(0, "Send message...")
        self.messageSendEntry.config(foreground="grey")
        self.userListbox = Listbox(self.clientFrame, font=('Helvetica', 14), width=20)
        self.userListbox.pack(side="right", fill="y")
        self.chatText = Text(self.clientFrame, font=('Helvetica', 14))
        self.chatText.pack(side="top", fill="both", expand=True)
        self.chatText.configure(state="disabled")

    def on_message_focus_in(self, event):
        """" Detects focus on message sending box """
        if self.messageSendEntry.get() == "Send message...":
            self.messageSendEntry.delete(0, "end")
            self.messageSendEntry.insert(0, "")
            self.messageSendEntry.config(foreground="white")

    def on_message_focus_out(self, event):
        """" Detects defocus on message sending box """
        if self.messageSendEntry.get() == "":
            self.messageSendEntry.insert(0, "Send message...")
            self.messageSendEntry.config(foreground="grey")

    # ------------------------------------------

    # ==========================================
    # Handling gui changes

    def send_chat_to_server(self, data):
        """ Send message from chat to server """
        ClientNetwork.send_to_server(data)
        self.messageSendEntry.delete(0, "end")

    def add_chat_log(self, message, **properties):
        """ Adds a chat log
        Log colors can be configured with **properites:
        - color | color of text
        - start | first color char index
        - end   | last color char index
        """
        self.chatText.configure(state="normal")
        self.chatText.insert(END, str(str(message) + "\n"))
        self.log_num = str(int(self.log_num) + 1)
        if "start" in properties:
            self.chatText.tag_config(self.log_num, foreground=properties["color"], font=('Helvetica', 14, "bold"))
            self.chatText.tag_add(self.log_num, str(str(self.currentLogLine) + "." + str(properties["start"])),
                                  str(str(self.currentLogLine) + "." + str(properties["end"])))
            self.chatText.tag_config("log_dot", foreground="grey", font=('Helvetica', 14, "bold"))
            self.chatText.tag_add("log_dot", str(str(self.currentLogLine) + "." + str(int(properties["end"]))),
                                  str(str(self.currentLogLine) + "." + str(int(properties["end"]) + 2)))
        self.currentLogLine += 1
        self.chatText.configure(state="disabled")

    def set_start_users(self, users):
        """ Add users to user list after joining to server """
        for user in users:
            self.userListbox.insert("end", users[user])

    def add_to_user_list(self, data):
        """ Add user to user list """
        self.add_chat_log(f"Server: {data['userJoined']} has joined the server!",
                          start=0, end=len("Server"), color="grey")
        self.userListbox.insert("end", data['userJoined'])
        self.userListbox.delete(0)
        self.userListbox.insert(0, f"Connected users ({data['totalUsers']}):")

    def delete_from_user_list(self, data):
        """ Delete user from user list """
        self.add_chat_log(f"Server: {data['userLeft']} has left the server!",
                          start=0, end=len("Server"), color="grey")
        indexToDelete = self.userListbox.get(0, END).index(data["userLeft"])
        self.userListbox.delete(indexToDelete)
        self.userListbox.delete(0)
        self.userListbox.insert(0, f"Connected users ({data['totalUsers']}):")

    # ==========================================

    # ------------------------------------------
    # Connecting and waiting for server data

    def connect_to_server(self, username, serverAdress):
        """ Tries to connect client to selected server adress """
        if username == None:
            username = DEFAULT_USERNAME
        try:
            tempServerAdressTuple = tuple(serverAdress.split(":"))
            self.username = str(username)
            self.serverIp = str(tempServerAdressTuple[0])
            self.serverPort = int(tempServerAdressTuple[1])
            self.serverAdressTuple = (self.serverIp, self.serverPort)
            connectionStatus = bool(ClientNetwork.check_connection(self.serverAdressTuple))
        except:
            connectionStatus = False
        if connectionStatus:
            self.connectionFrame.destroy()
            root.geometry("900x550")
            self.create_widgets_main_window()
            threading.Thread(target=self.listen_for_server, args=()).start()

    def listen_for_server(self):
        """ THREAD: listening_thread
        This functions listen for server data
        """
        self.connected = True
        while self.connected:
            fullData = b''
            newData = True
            while self.connected:
                data = client.recv(1024)
                if len(data) <= 0:
                    break
                if newData:
                    dataLen = int(data[:HEADER])
                    newData = False
                fullData += data
                if len(fullData) - HEADER == dataLen:
                    recievedData = pickle.loads(fullData[HEADER:])
                    self.handle_recieved_data(recievedData)
                    fullData = b''
                    newData = True

    # ------------------------------------------

    # ==========================================
    # Hendling data from server

    def handle_recieved_data(self, recievedData):
        """ Checks data recieved and handle it """
        actionType = recievedData["type"]
        if actionType == "userListChange":
            pass
        elif actionType == "chatMessageSent":
            self.add_chat_log(f"{recievedData['author']}: {recievedData['messageData']}",
                              start=0, end=len(recievedData['author']), color="green")
        elif actionType == "chanelListChange":
            pass
        elif actionType == "userJoined":
            self.add_to_user_list(recievedData)
        elif actionType == "userLeft":
            self.delete_from_user_list(recievedData)
        elif actionType == "clientInformations":
            self.clientAdress = recievedData["clientAdress"]
            ClientNetwork.send_to_server({
                "type": "clientUsername",
                "fromWho": self.clientAdress,
                "messageData": self.username
            })
            self.userListbox.insert(0, f"Connected users ({recievedData['totalUsers']}):")
        elif actionType == "allUsersConnected":
            self.set_start_users(recievedData["allUsers"])
        elif actionType == "serverClosed":
            on_window_close()
        else:
            ClientNetwork.undefined_server_data(actionType, recievedData)

    # ==========================================


# ------------------------------------------
# Helper ClientNetwork.functions

class ClientNetwork():
    """ Instance of this class shouldn't be created
    It provides:
    - sending data to server
    - checking connection to server
    """

    @staticmethod
    def check_connection(serverAdress):
        """ Checks connection to serverAdress, returns boolean """
        try:
            client.connect(serverAdress)
            return True
        except:
            return False

    @staticmethod
    def send_to_server(data):
        """ Sends data to server """
        packedData = pickle.dumps(data)
        packedData = bytes(f"{len(packedData):<{HEADER}}", 'utf-8') + packedData
        client.send(packedData)

    @staticmethod
    def undefined_server_data(actionType, actionData):
        """ Handle undefined data from server """
        pass


# ------------------------------------------


if __name__ == "__main__":
    """ Program starts here """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_window_close)
    clientApp = Client(root)

    root.mainloop()
