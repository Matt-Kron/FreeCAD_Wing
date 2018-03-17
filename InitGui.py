# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
#  
#  Copyright 2018 Matthieu Carron
#  this file is based on the code and the ideas
#  of the macro AIRFOIL IMPORT & SCALE v2.1 
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
import Wing

__dir__ = os.path.dirname(Wing.__file__)
global iconPath
iconPath = __dir__ + '/Icons/'

class _CommandWing():

	def __init__(self,name='WingWorkbench',icon='Aile-icon.svg',command='',modul=''):
#		say("create Wing Command")
#		say(name)
		self.name=name
		self.icon= iconPath + icon
		self.command=command
		self.modul=modul
#		say(self.icon)

	def GetResources(self): 
		return {'Pixmap' : self.icon, 'MenuText': self.name, 'ToolTip': self.name +' creation'} 


	def IsActive(self):
		if FreeCADGui.ActiveDocument:
			return True
		else:
			return False

	def Activated(self):
		if FreeCADGui.ActiveDocument:
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
			Msg("First open a document")
		return

if FreeCAD.GuiUp:
	FreeCADGui.addCommand('Wing_Wing',_CommandWing("Wing",'Aile-icon.svg',"WingCommands.createWing()","WingCommands"))
	FreeCADGui.addCommand('Wing_Nervures',_CommandWing("Nervures",'IconBOM.svg',"WingCommands.createNervures()","WingCommands"))

class WingWorkbench (Workbench):
	'''Wing workbench object'''

	Icon = '''
/* XPM */
static char * Aile_icon_xpm[] = {
"48 48 122 2",
"  	c None",
". 	c #C80037",
"+ 	c #F1000E",
"@ 	c #FF0000",
"# 	c #BE0041",
"$ 	c #4C00B2",
"% 	c #1100ED",
"& 	c #D4002B",
"* 	c #B80047",
"= 	c #3000CE",
"- 	c #0000FE",
"; 	c #0F00EF",
"> 	c #D2002D",
", 	c #F2000D",
"' 	c #FE0001",
") 	c #B3004C",
"! 	c #2400DB",
"~ 	c #0B00F3",
"{ 	c #0100FD",
"] 	c #C90036",
"^ 	c #B90045",
"/ 	c #2700D7",
"( 	c #0500F9",
"_ 	c #1C00E2",
": 	c #1400EB",
"< 	c #C70038",
"[ 	c #EF0010",
"} 	c #C3003B",
"| 	c #3100CE",
"1 	c #0100FC",
"2 	c #1200EC",
"3 	c #2E00D1",
"4 	c #1500E9",
"5 	c #0000FF",
"6 	c #0A00F4",
"7 	c #C4003A",
"8 	c #F0000F",
"9 	c #E2001D",
"0 	c #5900A5",
"a 	c #0300FB",
"b 	c #2D00D2",
"c 	c #3C00C3",
"d 	c #0E00F0",
"e 	c #0700F7",
"f 	c #BB0043",
"g 	c #F5000A",
"h 	c #8D0072",
"i 	c #0000FD",
"j 	c #1300EC",
"k 	c #4D00B2",
"l 	c #3900C4",
"m 	c #0400F9",
"n 	c #0600F8",
"o 	c #B90046",
"p 	c #D70028",
"q 	c #4100BC",
"r 	c #3800C7",
"s 	c #63009C",
"t 	c #2D00D1",
"u 	c #B60048",
"v 	c #EE0011",
"w 	c #FB0004",
"x 	c #AA0054",
"y 	c #0F00ED",
"z 	c #1900E6",
"A 	c #660099",
"B 	c #680095",
"C 	c #1700E6",
"D 	c #AD0052",
"E 	c #F90006",
"F 	c #970067",
"G 	c #0300FC",
"H 	c #0500FA",
"I 	c #5C00A3",
"J 	c #890076",
"K 	c #5500A9",
"L 	c #0200FB",
"M 	c #AA0055",
"N 	c #C4003B",
"O 	c #9B0064",
"P 	c #860078",
"Q 	c #2600D7",
"R 	c #A80057",
"S 	c #E3001C",
"T 	c #BC0043",
"U 	c #A1005E",
"V 	c #4F00AE",
"W 	c #9E0061",
"X 	c #0000FC",
"Y 	c #990065",
"Z 	c #8B0074",
"` 	c #82007D",
" .	c #81007D",
"..	c #7F0080",
"+.	c #74008A",
"@.	c #73008B",
"#.	c #70008E",
"$.	c #F3000C",
"%.	c #0D00F1",
"&.	c #74008B",
"*.	c #EA0015",
"=.	c #1800E7",
"-.	c #9D0062",
";.	c #F4000B",
">.	c #1000ED",
",.	c #950068",
"'.	c #EC0013",
").	c #F80007",
"!.	c #64009A",
"~.	c #EB0014",
"{.	c #BF003F",
"].	c #D5002A",
"^.	c #F3000D",
"/.	c #0700F6",
"(.	c #B60047",
"_.	c #E80016",
":.	c #A0005F",
"<.	c #B70047",
"[.	c #E70018",
"}.	c #DB0024",
"|.	c #F60009",
"1.	c #FA0005",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                          . +                                                   ",
"                                    @ # $ % & +                                                 ",
"                                @ * = - - - ; > ,                                               ",
"                            ' ) ! ~ ~ { - - - ~ ] +                                             ",
"                        ' ^ / ( _ : { - - - - - ~ < [                                           ",
"                    @ } | 1 2 3 4 - - - - 5 - - - 6 7 8                                         ",
"                @ 9 0 a a b c d - - - 5 - - - - - - e f [                                       ",
"              g h ; i j k l m - - - 5 - - - - - - - - n o [                                     ",
"          @ p q i 5 r s t i i - 5 - - - - - 5 - - - - - n u v                                   ",
"        w x y 5 z A B C i i 5 5 - - - - 5 5 - - - - - - - a D 8                                 ",
"      E F G H I J K L i 5 5 i i i i 5 5 - - - - - 5 - - - - a M [                               ",
"    @ N   A O P Q i 5 5 5 i i i 5 5 5 - - - - 5 - - - - - 5 - a R v                             ",
"    @ S T U V   5 5 5 5 i i 5 5 5 i i i i 5 5 - - - - 5 - - - - { W 8                           ",
"                    X X 5 5 5 5 i i i 5 5 i i - - 5 5 - - - - - 5 { O [                         ",
"                      5 5 5 i i i 5 5 5 i i i i 5 5 - - - - 5 - - - { Y [                       ",
"                          X X 5 5 5 i i i i 5 5 i i - - 5 5 - - - - - - h 8                     ",
"                            5 5 5 i i i 5 5 5 i i i 5 5 - - - - - 5 - - - Z 8                   ",
"                                X X 5 5 5 i i i 5 5 5 i i - - 5 - - - - - 5 ` 8                 ",
"                                    5 5 i i 5 5 5 i i i i 5 5 - - - - 5 5 - -  .+               ",
"                                      X 5 5 5 5 i i i 5 5 5 i i - - 5 - - - - - ..+             ",
"                                          5 X i i 5 5 5 i i i i 5 5 - - - - 5 - - +.+           ",
"                                            X 5 5 5 5 i i i 5 5 i i i - 5 5 - - - - @.,         ",
"                                                5 X i i 5 5 5 i i i 5 5 5 - - - - 5 - #.$.      ",
"                                                    5 5 5 i i i 5 5 5 i i i - 5 5 - %.&.*.g     ",
"                                                        X i 5 5 5 5 i i i 5 5 i =.-.$.' ;.      ",
"                                                            5 5 i i i 5 5 5 >.,.'.*.).          ",
"                                                              X i 5 5 5 i !.~.{.].^.            ",
"                                                                  5 5 /.(._.:.8 ;.              ",
"                                                                      <.[.}.g                   ",
"                                                                      8 |.1.                    ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                ",
"                                                                                                "};
'''

	MenuText = "Wing creation"
	ToolTip = "Create wing and nervures for aeromodels"

	def Initialize(self):
		"This function is executed when FreeCAD starts"


		self.appendToolbar("Wing", ["Wing_Wing","Wing_Nervures"])
		self.appendMenu("Wing", ["Wing_Wing","Wing_Nervures"])
		Log ("Loading Wing module done\n")
 
	def Activated(self):
		"This function is executed when the workbench is activated"
		Msg ("MyWorkbench.Activated()\n")
		return
 
	def Deactivated(self):
		"This function is executed when the workbench is deactivated"
		Msg ("MyWorkbench.Deactivated()\n")
		return
 
	def ContextMenu(self, recipient):
		"This is executed whenever the user right-clicks on screen"
		# "recipient" will be either "view" or "tree"
		#self.appendContextMenu("My commands",self.list) # add commands to the context menu
 
	def GetClassName(self): 
		# this function is mandatory if this is a full python workbench
		return "Gui::PythonWorkbench"
 
Gui.addWorkbench(WingWorkbench())
