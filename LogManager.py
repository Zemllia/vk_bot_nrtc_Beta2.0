
def AddLog(LogMessage):
    print(LogMessage)
    f = open("Log.txt", "a+", encoding="utf-8")
    f.write(LogMessage + "\n")
    f.close()
