# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
#  
#  Copyright 2018 Matthieu Carron
#  this file is based on the code and the ideas
#  of the macro AIRFOIL IMPORT & SCALE v2.1 and Animation module of microelly
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
###################################################################################

import os
import FreeCAD
import FreeCADGui
import Wing, WingDialogs

__dir__ = os.path.dirname(Wing.__file__)
global iconPath
iconPath = __dir__ + '/Icons/'

#def userMsg(message):
#	FreeCAD.Console.PrintMessage(message + "\n")

class _CommandWing():

	def __init__(self,name='WingWorkbench',icon='Aile-icon.svg',command='',modul=''):
#		FreeCAD.Console.PrintMessage("_CommandWing.__init__ starting...\n")
		self.name = name
		self.icon = iconPath + icon
		self.command = command
		self.modul = modul

	def GetResources(self): 
		return {'Pixmap' : self.icon, 'MenuText': self.name, 'ToolTip': 'Add ' + self.name} 

	def IsActive(self):
		if FreeCADGui.ActiveDocument:
			return True
		else:
			return False

	def Activated(self):
		if FreeCADGui.ActiveDocument:
#			FreeCAD.Console.PrintMessage(self.name + " command activated\n")
			FreeCAD.ActiveDocument.openTransaction("create " + self.name)
			if self.command <> '':
				if self.modul <>'':
					modul=self.modul
				else:
					modul=self.name
				FreeCADGui.doCommand("import " + modul)
				FreeCADGui.doCommand(self.command)
			else:
				FreeCADGui.doCommand("import Wing")
				FreeCADGui.doCommand("Wing.create"+self.name+"()")
			FreeCAD.ActiveDocument.commitTransaction()
			FreeCAD.ActiveDocument.recompute()
		else:
			FreeCAD.Console.PrintMessage("First open a document\n")
		return

if FreeCAD.GuiUp:
	FreeCADGui.addCommand('Wing_ImportProfil',_CommandWing("Profile",'ImportProfile-icon.svg',"Wing.createProfile()","Wing"))
	FreeCADGui.addCommand('Wing_Wing',_CommandWing("Wing",'Aile-icon.svg',"Wing.createWing()","Wing"))
	FreeCADGui.addCommand('Wing_CoordSys',_CommandWing("Axis",'WF_Axes.svg',"Wing.createCoordSys()","Wing"))
#	FreeCADGui.addCommand('Wing_Nervures',_CommandWing("Nervures",'Nervures-icon.svg',"Nervures.createNervures()","Nervures"))
	FreeCADGui.addCommand('Wing_Rod',_CommandWing("Rod",'Rod-icon.svg',"Wing.createRod()","Wing"))
	FreeCADGui.addCommand('Wing_WrapLeadingEdge', _CommandWing("WrapLeadingEdge", "WrapLeadingEdge-icon.svg", "Wing.createWrapLeadingEdge()", "Wing"))
	FreeCADGui.addCommand('Wing_LeadingEdge', _CommandWing("LeadingEdge", "LeadingEdge-icon.svg", "Wing.createLeadingEdge()", "Wing"))
	FreeCADGui.addCommand('Wing_CutWire', _CommandWing("CutWire", "CutWire-icon.svg", "Wing.createCutWire()", "Wing"))
	FreeCADGui.addCommand('Wing_Section', _CommandWing("Section", "Section.svg", "Wing.createSection()", "Wing"))
	FreeCADGui.addCommand("WingDialog", WingDialogs.CommandWingDialog())

class WingWorkbench(Workbench):
	'''Wing workbench object'''

	Icon = iconPath + 'Aile-icon.svg'

	MenuText = "Wing toolkit"
	ToolTip = "Create wing and nervures for aeromodels"

	def Initialize(self):
		"This function is executed when FreeCAD starts"
		self.appendToolbar("Wing", ["Wing_ImportProfil", "Wing_Wing", "Wing_CoordSys", "Wing_Rod",
							"Wing_WrapLeadingEdge", 'Wing_LeadingEdge', "Wing_CutWire", "Wing_Section", 'WingDialog'])
		self.appendMenu("Wing", ["Wing_ImportProfil", "Wing_Wing", "Wing_CoordSys", "Wing_Rod",
							"Wing_WrapLeadingEdge", 'Wing_LeadingEdge', "Wing_CutWire", "Wing_Section", 'WingDialog'])
		Log ("Loading Wing module done")

	def Activated(self):
		"This function is executed when the workbench is activated"
		FreeCAD.Console.PrintMessage ("WingWorkbench.Activated()\n")
		return

	def Deactivated(self):
		"This function is executed when the workbench is deactivated"
		FreeCAD.Console.PrintMessage ("WingWorkbench.Deactivated()\n")
		return

	def ContextMenu(self, recipient):
		"This is executed whenever the user right-clicks on screen"
		# "recipient" will be either "view" or "tree"
		#self.appendContextMenu("My commands",self.list) # add commands to the context menu

	def GetClassName(self): 
		# this function is mandatory if this is a full python workbench
		return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(WingWorkbench())
