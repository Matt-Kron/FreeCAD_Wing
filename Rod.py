import FreeCAD

ModeVerbose = True

def msgCsl(message):
	if ModeVerbose:
		FreeCAD.Console.PrintMessage(message  +"\n")
