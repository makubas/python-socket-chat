import os
import pickle
import socket
import threading
import tkinter as tk
from tkinter import *
from tkinter.ttk import *

from config import *


def on_window_close():
    """ Handles action after tkinter window is closed """
    ServerNetwork.send_to_all_clients({
        "type": "serverClosed"
    })
    root.destroy()


class Server(tk.Frame):

    def __init__(self, master):
        """ Server __init__ function """
        self.master = master
        Frame.__init__(self, self.master)
        self.pack(fill='both', expand=True)
        root.geometry("1050x750")
        root.title("Server Console")

        self.logsTextVariable = StringVar()
        self.logsTextVariable.set("Init")
        self.currentLogLine = 1
        self.commandList = {"list": "List all active connections",
                            "help": "Lista all avaible commands"
                            }


        self.serverDirectoryPath = os.path.abspath(os.getcwd())
        self.serverStylePath = os.path.join(self.serverDirectoryPath, "styles")

        root.call('lappend', 'auto_path', self.serverStylePath)
        root.call('package', 'require', 'awdark')
        style = Style(root)
        style.theme_use("awdark")


        self.create_widgets_server_window()

        threading.Thread(target=self.waiting_for_connections, args=()).start()

    # ------------------------------------------
    # Creation of tkinter widgets

    def create_widgets_server_window(self):
        """ Creates widgets for main server window """
        self.serverFrame = Frame(self)
        self.serverFrame.grid(row=0, column=0, sticky=NSEW)
        self.serverFrame.pack(side="top", fill="both", expand=True)
        self.serverFrame.grid_propagate(False)

        self.logsText = Text(self.serverFrame, font=('Helvetica', 16), height=2)
        self.logsText.configure(state="disabled")
        self.logsText.pack(side="top", fill="both", expand=True)
        self.commandEntry = Entry(self.serverFrame, font=('Helvetica', 16))
        self.commandEntry.bind('<Return>', self.register_log)
        self.commandEntry.pack(side="top", fill="x")

    # ------------------------------------------

    # ==========================================
    # Logging in console

    def add_server_log(self, message, **properties):
        """ Adds new log in console
        Log colors can be configured with **properites:
        - color | color of text
        - start | first color char index
        - end   | last color char index
        """
        self.logsText.configure(state="normal")
        self.logsText.insert(END, str(str(message) + "\n"))
        if "start" in properties:
            self.logsText.tag_add("log_style", str(self.currentLogLine) + "." + properties["start"],
                                  str(self.currentLogLine) + "." + properties["end"])
            self.logsText.tag_config("log_style", background=properties["color"])
        self.logsText.configure(state="disabled")

    def register_log(self, event):
        """ Checks if log sent was a command """
        logInput = str(self.commandEntry.get())
        self.commandEntry.delete(0, END)
        self.add_server_log(f"[COMMAND]                {logInput}")
        if logInput not in self.commandList:
            self.add_server_log(
                f"[COMMAND]                Wrong command: '{logInput}'! Type 'help' to get list of commands.")
        elif logInput == "list":
            for connectionCl in ACTIVE_CONNECTIONS:
                self.add_server_log(f"[COMMAND]                {connectionCl}: {ACTIVE_CONNECTIONS[connectionCl]}")

    # ==========================================

    # ------------------------------------------
    # Handling clients / listening for data

    def listen_for_client(self, clientConnected, clientAdress):
        """ Waits for client to send any data to handle """
        self.add_server_log(f"[SERVER]                    New connection: {clientAdress}")
        self.add_server_log(f"[SERVER]                    Active connections: {threading.activeCount() - 2}")
        ACTIVE_CONNECTIONS[clientAdress] = DEFAULT_USERNAME
        ACTIVE_CONNECTIONS_2[clientConnected] = clientAdress
        ACTIVE_CONNECTIONS_3[clientAdress] = clientConnected
        ServerNetwork.send_to_client(clientConnected, {
            "type": "clientInformations",
            "fromWho": "server",
            "clientAdress": clientAdress,
            "totalUsers": threading.activeCount() - 2,
        })
        connected = True
        while connected:
            fullData = b''
            newData = True
            while True:
                data = clientConnected.recv(1024)
                if len(data) <= 0:
                    break
                if newData:
                    dataLen = int(data[:HEADER])
                    newData = False
                fullData += data
                if len(fullData) - HEADER == dataLen:
                    recievedData = pickle.loads(fullData[HEADER:])
                    if recievedData["type"] == "disconnect":
                        connected = False
                        break
                    self.handle_recieved_data(recievedData)
                    fullData = b''
                    newData = True
        clientConnected.close()
        self.add_server_log(f"[SERVER]                    Client disconnected: {clientAdress}")
        self.add_server_log(f"[SERVER]                    Active connections: {threading.activeCount() - 3}")
        ServerNetwork.send_to_all_clients({
            "type": "userLeft",
            "userLeft": ACTIVE_CONNECTIONS[clientAdress],
            "totalUsers": threading.activeCount() - 3
        }, ACTIVE_CONNECTIONS_2[clientConnected], clientConnected)
        del ACTIVE_CONNECTIONS[clientAdress]
        del ACTIVE_CONNECTIONS_2[clientConnected]
        del ACTIVE_CONNECTIONS_3[clientAdress]

    def waiting_for_connections(self):
        """ Waits for connection from a new client, creates thread for it """
        self.add_server_log("--------------------------------------------------------------------------")
        self.add_server_log("[SERVER]                    Server is Starting...")
        self.add_server_log(f"[SERVER]                    IP:   {SERVER}")
        self.add_server_log(f"[SERVER]                    PORT: {PORT}")
        self.add_server_log(f"[SERVER]                    Connect on: {SERVER}:{PORT}")
        self.add_server_log("--------------------------------------------------------------------------")
        server.listen()
        while True:
            (clientConnected, clientAdress) = server.accept()
            threading.Thread(target=self.listen_for_client, args=(clientConnected, clientAdress)).start()

    # ------------------------------------------

    # ==========================================
    # Handling data

    def handle_recieved_data(self, recievedData):
        """ Handles recieved data and choose what to do depending on type """
        self.add_server_log(f"[DATA RECIEVED]      {recievedData}")
        actionType = recievedData["type"]
        if actionType == "clientUsername":
            ACTIVE_CONNECTIONS[recievedData["fromWho"]] = recievedData["messageData"]
            ServerNetwork.send_to_all_clients({
                "type": "userJoined",
                "userJoined": recievedData["messageData"],
                "totalUsers": threading.activeCount() - 2
            })
            del ACTIVE_CONNECTIONS[recievedData["fromWho"]]
            ServerNetwork.send_to_client(ACTIVE_CONNECTIONS_3[recievedData["fromWho"]], {
                "type": "allUsersConnected",
                "allUsers": ACTIVE_CONNECTIONS
            })
            ACTIVE_CONNECTIONS[recievedData["fromWho"]] = recievedData["messageData"]
        elif actionType == "chatMessageSent":
            ServerNetwork.send_to_all_clients({
                "type": "chatMessageSent",
                "fromWho": "server",
                "author": ACTIVE_CONNECTIONS[recievedData["fromWho"]],
                "messageData": recievedData["messageData"]
            })

    # ==========================================


# ------------------------------------------
# Helper ServerNetwork.functions

class ServerNetwork():
    """ Instance of this class shouldn't be created
    It provides:
    - sending data to clients
    - checking connection to client
    """

    @staticmethod
    def send_to_client(clientConnected, data):
        """ Sends data to client """
        serverApp.add_server_log(f"[DATA SENT]               {data}")
        packedData = pickle.dumps(data)
        packedData = bytes(f"{len(packedData):<{HEADER}}", 'utf-8') + packedData
        clientConnected.send(packedData)

    @staticmethod
    def send_to_all_clients(data, *skipList):
        """ Sends data to all clients """
        for client in ACTIVE_CONNECTIONS_2:
            if client not in skipList:
                ServerNetwork.send_to_client(client, data)


# ------------------------------------------


if __name__ == "__main__":
    """ Program starts here """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(ADDR)

    ACTIVE_CONNECTIONS = {}
    ACTIVE_CONNECTIONS_2 = {}
    ACTIVE_CONNECTIONS_3 = {}

    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_window_close)
    serverApp = Server(root)

    root.mainloop()
