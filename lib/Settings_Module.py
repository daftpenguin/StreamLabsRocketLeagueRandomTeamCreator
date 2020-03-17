import os
import codecs
import json

class MySettings(object):
    def __init__(self, settingsfile=None):
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        except:
            self.RegisterCommand = "!register"
            self.UnregisterCommand = "!unregister"
            self.RegisteredCommand = "!registered"
            self.NumTeamsCommand = "!numteams"
            self.CreateTeamsCommand = "!createteams"
            self.CreateTeamsPermission = "moderator"
            self.CreateTeamsInfo = ""
            self.MaxMMR = None
            self.AlertMMR = None

    def Reload(self, jsondata):
        self.__dict__ = json.loads(jsondata, encoding="utf-8")
        return

    def Save(self, settingsfile):
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="w+") as f:
                json.dump(self.__dict__, f, encoding="utf-8")
            with codecs.open(settingsfile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
                f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8')))

            if self.MaxMMR is not None and self.MaxMMR.strip().numeric():
                self.MaxMMR = int(self.MaxMMR)

            if self.AlertMMR is not None and self.AlertMMR.strip().numeric():
                self.AlertMMR = int(self.AlertMMR)
                
        except:
            #Parent.Log(ScriptName, "Failed to save settings to file.")
            pass #Parent doesn't exist?
        return