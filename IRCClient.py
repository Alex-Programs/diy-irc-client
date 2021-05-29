import socket
from enum import Enum
from dataclasses import dataclass
from threading import *
import time

class Command(Enum):
    PASSWORD = "PASS"
    NICK = "NICK"
    USER = "USER"
    PONG = "PONG"
    PING = "PING"
    PRIVMSG = "PRIVMSG"
    JOIN = "JOIN"

@dataclass
class UserData():
    username : str
    hostname : str
    servername : str
    realname : str

def printlog(text):
    print(text)
    with open("log.txt", "a") as f:
        if text[:2] != "\n":
            text += "\n"
        f.write(text)

def log(text):
    with open("log.txt", "a") as f:
        if text[:2] != "\n":
            text += "\n"
        f.write(text)

class IRCClient():
    def __init__(self, nick, userData, address, port, password="none", verbose=False):
        self.nick = nick
        self.userData = userData
        self.address = address
        self.port = port
        self.password = password
        self.verbose = verbose
        self.channel = None

        self.on_recv = None

    def start(self):
        self.s = socket.socket()
        self.s.connect((self.address, self.port))
        self._send_pass_(self.password)
        self._send_nick_(self.nick)
        self._send_user_(self.userData.username, self.userData.hostname, self.userData.servername, self.userData.realname)

        Thread(target=self._ping_thread_).start()

        Thread(target=self._loop_).start()
    
    def _send_cmd_(self, command, data):
        command = command.value
        if self.verbose:
            printlog("Sending data: ``" + command + " " + data + "``")
        self.s.send(bytes(command + " " + data + "\n", "utf8"))

    def _send_pass_(self, password):
        self._send_cmd_(Command.PASSWORD, password)

    def _send_nick_(self, nick):
        self._send_cmd_(Command.NICK, nick)

    def _send_user_(self, username, hostname, servername, realname):
        self._send_cmd_(Command.USER, f"{username} {hostname} {servername} {realname}")

    def _loop_(self):
        #TODO refactor into enums

        buffer = ""
        while True:
            buffer += self.s.recv(1024).decode("utf8")

            try:
                msgType = buffer.split(" ")[1]
            except: 
                pass

            for line in buffer.split("\n"):
                segments = line.split(" ")
                if segments[0].rstrip() == "PING":
                    self.s._send_cmd_(Command.PONG, segments[1])

                if self.on_recv:
                    self.on_recv(line)

                try:
                    lineType = line.split(" ")[1]
                    blacklisted = ["372", "005", "PONG", "MODE",]
                    bufferBlacklist = ["NOTICE", "PONG", "MODE"]

                    if lineType not in blacklisted and msgType not in bufferBlacklist:
                        print(str(line))
                except:
                    pass

    def _ping_thread_(self):
        while True:
            time.sleep(10)

            self._send_cmd_(Command.PING, self.address)

    def send_message(self, channel, text):
        self._send_cmd_(Command.PRIVMSG, channel + " " + text)

    def join_channel(self, channel):
        self.channel = channel
        self._send_cmd_(Command.JOIN, channel)

def on_recv(data):
    log(data)

if __name__ == "__main__":
    client = IRCClient("testing89054", UserData("testing89054", "*", "*", "Alex"), "irc.freenode.net", 6667, verbose=True)
    client.on_recv = on_recv

    client.start()

    while True:
        uinp = input("> ").split(" ")
        if uinp[0] == "send":
            client.send_message(client.channel, uinp[1])

        if uinp[0] == "join":
            client.join_channel(uinp[1])