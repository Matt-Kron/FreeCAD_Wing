# -*- coding: utf-8 -*-
###################################################################################
#
#  Wing.py
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

__title__="FreeCAD Wing Toolkit"
__author__ = "Matthieu Carron"

import os
#from PySide import QtGui
import FreeCAD, FreeCADGui, Part, Draft
from FreeCAD import Vector, Rotation, Placement
from WingLib import *
from pivy import coin

__dir__ = os.path.dirname(__file__)
global iconPath
iconPath = __dir__ + '/Icons/'
global ProfilesPath
ProfilesPath = __dir__ + '/Profiles/'

ModeVerbose = True
VecNul = Vector(0,0,0)
DefaultProfile = ProfilesPath + 'Default.dat'


def updateTree(grp):
#	msgCsl("updateTree method start\n")
	objlist = []
	if hasattr(grp,  "OutList"):
		objlist = grp.OutList
#	msgCsl("taille objlist: " + str(len(objlist)))
	fcobjlist = []
	for prop in grp.PropertiesList:
		if grp.getTypeIdOfProperty(prop) == 'App::PropertyLink':
			gobj = grp.getPropertyByName(prop)
			fcobjlist.append(gobj)
			if gobj != None and gobj not in objlist:
				grp.addObject(gobj)
#	msgCsl("taille fcobjlist: " + str(len(fcobjlist)))
	for obj in objlist:
		if obj not in fcobjlist:
#			msgCsl("Remove object " + obj.Name + " of group object " + grp.Name)
			grp.removeObject(obj)

def WireTangent(mWire,mIndex):
	if len(mWire.Points) > 1:
		pc=mWire.Shape.Vertexes[mIndex].Point
		pav=mWire.Shape.Vertexes[mIndex-1].Point
		pap=mWire.Shape.Vertexes[mIndex+1].Point
		msgCsl("pc "+ format(pc))
		msgCsl("pav "+ format(pav))
		msgCsl("pap "+ format(pap))
		mTangent=PtsToVec(pav,pap)
		mTangent.normalize()
		return mTangent

class Profile:

	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyFile", "File", "Profile", "Data source of wire").File = DefaultProfile
		obj.addProperty("App::PropertyLength", "Scale", "Profile", "Profile scale").Scale = 1.0
		obj.addProperty("App::PropertyVectorList","Points","Profile","Points of the profile", 1)
		obj.addProperty("App::PropertyLink","Wire","Profile","Wire build from the profile", 1)
		self.createWire(obj)
		obj.Proxy = self

	def createWire(self, fp):
		#############################
		# Dwire creation
		#############################
		# get the points from the root profile and make the wire
		userMsg("Loading root points from file...")
		points=[]
		points = getPoints(fp.File)
		e = fp.Scale
		for p in points:
			p.x = p.x * e
			p.y = p.y * e
		fp.Points = points
		wireP = Part.makePolygon(fp.Points, True)
		wire = Draft.makeWire(wireP, True, False)
		wire.Label = "ProfileWire"
		fp.Wire = wire
				
	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop == "File":
			fp.Points = getPoints(fp.File)
			self.updateWire(fp)
		if prop == "Scale":
			self.updateWire(fp)
				
	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")
	
	def updateWire(self, fp):
		if hasattr(fp, "Wire"):
			pts = []
			for p in fp.Points:
				pts.append(Vector(p.x * fp.Scale,p.y * fp.Scale, 0))
			fp.Wire.Points = pts
			#FreeCADGui.SendMsgToActiveView("ViewFit")

class ViewProviderProfile:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + 'Profile-icon.svg'
		obj.Proxy = self

	def getIcon(self):
		return iconPath + 'Profile-icon.svg' #self.icon
		
	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		doc.removeObject(obj.Wire.Name)
		return True

	def attach(self, vobj):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		self.Object = vobj.Object
		self.standard = coin.SoGroup()
		vobj.addDisplayMode(self.standard,"Standard");

	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

	def getDisplayModes(self,fp):
		"'''Return a list of display modes.'''"
		return ["Standard"]

	def getDefaultDisplayMode(self):
		"'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
		return "Standard"

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
				Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
				to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
				Since no data were serialized nothing needs to be done here.'''
		return None

class Wing:

	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLength", "Length", "Wing", "Length of the wing").Length = 500.0
		obj.addProperty("App::PropertyDistance", "TipXOffset", "Tip", "Tip offset in X from root wire").TipXOffset = 0.0
		obj.addProperty("App::PropertyDistance", "TipYOffset", "Tip", "Tip offset in Y from root wire").TipYOffset = 0.0
		obj.addProperty("App::PropertyAngle", "TipAngle", "Tip", "Tip angle").TipAngle = 0.0
		obj.addProperty("App::PropertyBool", "MakeLoft", "Wing", "Make the loft from the root and tip wires").MakeLoft = False
		obj.addProperty("App::PropertyLink","TipProfile","Wing","Profile of the wing tip")
		obj.addProperty("App::PropertyLink","RootProfile","Wing","Profile of the wing root")
		obj.addProperty("App::PropertyLink","Loft","Wing","Name of the wing's loft", 1)
		self.rName = ""
		self.tName = ""
		obj.Proxy = self
				
	def onChanged(self, fp, prop):
		# Do something when a property has changed
		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop in ["Length", "TipXOffset", "TipYOffset", "TipAngle"] and self.check(fp):
			if hasattr(fp, "TipYOffset"):
				self.updatePosition(fp)
		if prop in ["RootProfile", "TipProfile"] and self.check(fp):
			msgCsl("prop in RootProfile...")
			if fp.RootProfile.Name != self.rName:
				self.rName = fp.RootProfile.Name
				self.updatePosition(fp)
			if fp.TipProfile.Name != self.tName:
				self.tName = fp.TipProfile.Name
				self.updatePosition(fp)
		if prop == "MakeLoft":
			if fp.MakeLoft:
				self.createLoft(fp)
			else:
				# remove Loft
				FreeCAD.ActiveDocument.removeObject(fp.Loft.Name)		

	def check(self, fp):
		if hasattr(fp, "RootProfile") and hasattr(fp, "TipProfile"):
			if fp.RootProfile != None and fp.TipProfile != None:
				return True
			else:
				return False
		else:
			return False

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")

	def createLoft(self, fp):
		#############################
		# Wing's loft creation
		#############################
		AileBis = FreeCAD.ActiveDocument.addObject('Part::Loft','Loft')
		AileBis.Label = "Loft_Wing"
		fp.Loft = AileBis
		AileBis.Sections = [fp.RootProfile.Wire,fp.TipProfile.Wire]
		AileBis.Solid = True
		AileBis.Ruled = False
		FreeCAD.ActiveDocument.recompute()
		FreeCADGui.SendMsgToActiveView("ViewFit")
	
	def updatePosition(self, fp):
		if fp.RootProfile.Proxy.__class__.__name__ == "Profile" and fp.TipProfile.Proxy.__class__.__name__ == "Profile":
			pos = Vector(fp.TipXOffset,fp.TipYOffset,fp.Length)
			rot = FreeCAD.Rotation(Vector(0,0,1),fp.TipAngle)
			center = Vector(0, 0, 0)
			place = FreeCAD.Placement(pos, rot, center)
			place = fp.RootProfile.Wire.Placement.multiply(place)
#			msgCsl(format(place))
			fp.TipProfile.Wire.Placement = place
		if fp.RootProfile.TypeId == "Part::Part2DObjectPython" and fp.TipProfile.TypeId == "Part::Part2DObjectPython":
#			msgCsl("... in self.updatePosition")
			pos = Vector(fp.TipXOffset,fp.TipYOffset,fp.Length)
			rot = FreeCAD.Rotation(Vector(0,0,1),fp.TipAngle)
			center = Vector(0, 0, 0)
			place = FreeCAD.Placement(pos, rot, center)
			place = fp.RootProfile.Placement.multiply(place)
#			msgCsl(format(place))
			fp.TipProfile.Placement = place

class ViewProviderWing:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + 'Aile-icon.svg'
		obj.Proxy = self

	def getIcon(self):
		return iconPath + 'Aile-icon.svg'
		
	def attach(self, vobj):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		self.Object = vobj.Object
		self.standard = coin.SoGroup()
		vobj.addDisplayMode(self.standard,"Standard");

	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

	def getDisplayModes(self,fp):
		"'''Return a list of display modes.'''"
		return ["Standard"]

	def getDefaultDisplayMode(self):
		"'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
		return "Standard"

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
				Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
				to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
				Since no data were serialized nothing needs to be done here.'''
		return None

class CoordSys:
	
	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink","LinkedObject","CoordSys","Object to link with the coordinate system")
		obj.addProperty("App::PropertyEnumeration","CenterType","CoordSys","Either center of mass or vertexes").CenterType = ["MassCenter","Vertexes"]
		obj.addProperty("App::PropertyFloat","VertexNum","CoordSys","Vertexes or intermediate point of vertexes couple").VertexNum = 0.0
		obj.addProperty("App::PropertyLink","Tangent","CoordSys","Axis tangent to an edge", 1)
		obj.addProperty("App::PropertyLink","Normal","CoordSys","Normal of the reference face", 1)
		obj.addProperty("App::PropertyLink","Bend","CoordSys","Bend axis", 1)
		obj.addProperty("App::PropertyPlacement","LocalPlacement","CoordSys","Placement from linked object origin to new coordsys")
		obj.Tangent = Draft.makeWire([VecNul, FreeCAD.Vector(2,0,0)],closed=False,face=False,support=None)
		obj.Normal = Draft.makeWire([VecNul, FreeCAD.Vector(0,0,2)],closed=False,face=False,support=None)
		obj.Bend = Draft.makeWire([VecNul, FreeCAD.Vector(0,2,0)],closed=False,face=False,support=None)
		obj.Tangent.ViewObject.LineColor = (1.0,0.0,0.0)
		obj.Normal.ViewObject.LineColor = (0.0,0.0,1.0)
		obj.Bend.ViewObject.LineColor = (0.0,1.0,0.0)
		obj.Tangent.Label = "Tangent"
		obj.Normal.Label = "Normal"
		obj.Bend.Label = "Bend"
		self.pName = ""
		self.NewOrigin = VecNul
		self.ObjectOk = False
		self.ObjectOrigin = VecNul
		self.ObjectCenterOfMass = VecNul
		obj.CenterType = "Vertexes"
		obj.Proxy = self

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")

	def __getstate__(self):
		state = {}
		state["NewOrigin"] = list(self.NewOrigin)
		state["ObjectOrigin"] = list(self.ObjectOrigin)
		state["ObjectCenterOfMass"] = list(self.ObjectCenterOfMass)
		return state

	def __setstate__(self, state):
		self.NewOrigin = Vector(tuple( i for i in state["NewOrigin"]))
		self.ObjectOrigin = Vector(tuple( i for i in state["ObjectOrigin"]))
		self.ObjectCenterOfMass = Vector(tuple( i for i in state["ObjectCenterOfMass"]))
		self.pName = ""
		self.ObjectOk = False

	def onChanged(self, fp, prop):
		# Do something when a property has changed
		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop == "LinkedObject":
			msgCsl("CoordSys class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
			if hasattr(fp, "LinkedObject") and hasattr(self, "pName"):
				if fp.LinkedObject != None:
					if self.pName != fp.LinkedObject.Name:
						self.pName = fp.LinkedObject.Name
						self.updateRefFace(fp)
						self.updatePlacement(fp)
				else:
					self.pName = ""
					self.ObjectOk = False
			elif hasattr(self, "ObjectOk"):
				self.ObjectOk = False
		if prop in ["CenterType","VertexNum", "Normal"]:
#			msgCsl("CoordSys class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
			self.updatePlacement(fp)

	def updateRefFace(self, fp):
		if fp.LinkedObject.TypeId == "Part::Extrusion":
			nb = len(fp.LinkedObject.Base.Shape.Edges)
			mface = fp.LinkedObject.Shape.Faces[nb]
			self.ObjectEdges = mface.Edges
			self.ObjectCenterOfMass = mface.CenterOfMass
			self.ObjectOrigin = fp.LinkedObject.Shape.Vertex1.Point
			self.ObjectOk = True
		if fp.LinkedObject.TypeId == "PartDesign::Pad":
			self.ObjectEdges = fp.LinkedObject.Sketch.Shape.Edges
			self.ObjectCenterOfMass = fp.LinkedObject.Sketch.Shape.CenterOfMass
			self.ObjectOrigin = fp.LinkedObject.Sketch.Placement.Base
			self.ObjectOk = True
		elif fp.LinkedObject.TypeId == "Part::Cylinder":
			self.ObjectEdges = fp.LinkedObject.Shape.Face3.Edges
			self.ObjectCenterOfMass = fp.LinkedObject.Shape.Face3.CenterOfMass
			self.ObjectOrigin = self.ObjectCenterOfMass
			self.ObjectOk = True
		if fp.LinkedObject.TypeId == "Part::Box":
			self.ObjectEdges = fp.LinkedObject.Shape.Face5.Edges
			self.ObjectCenterOfMass = fp.LinkedObject.Shape.Face5.CenterOfMass
			self.ObjectOrigin = fp.LinkedObject.Shape.Vertex2.Point
			self.ObjectOk = True

	def updatePlacement(self, fp):
		if hasattr(self, "ObjectOk") and hasattr(fp, "LinkedObject"):
			if self.ObjectOk and fp.LinkedObject != None:
				if fp.LinkedObject.TypeId == "PartDesign::Pad":
					fp.LinkedObject.Sketch.Placement = fp.Tangent.Placement
				else:
					fp.LinkedObject.Placement = fp.Tangent.Placement
				self.updateRefFace(fp)
				Fract = int((round(fp.VertexNum,2) - int(fp.VertexNum))*100)
	#			msgCsl("Fract "+ str(Fract))
				mEdge = self.ObjectEdges[int(fp.VertexNum)]
				if Fract > 0:
					Pts = mEdge.discretize(101)
					Pt = Pts[Fract]
				else:
					Pt = mEdge.valueAt(0)
				if fp.CenterType == "MassCenter":
					self.NewOrigin = self.ObjectCenterOfMass
					mBend = PtsToVec(self.NewOrigin,Pt)
				else:
					self.NewOrigin = Pt
					mBend = PtsToVec(self.NewOrigin, self.ObjectCenterOfMass)
				msgCsl("NewOrigin "+ format(self.NewOrigin))
				mTrans = PtsToVec(self.NewOrigin,self.ObjectOrigin)
				mRot = FreeCAD.Rotation(mBend,fp.Bend.End.sub(fp.Bend.Start))
				mPlacement2 = FreeCAD.Placement(mTrans,mRot,self.NewOrigin)
				fp.LocalPlacement = mPlacement2
				if fp.LinkedObject.TypeId == "PartDesign::Pad":
					fp.LinkedObject.Sketch.Placement = fp.LocalPlacement.multiply(fp.LinkedObject.Sketch.Placement)
				else:
					fp.LinkedObject.Placement = fp.LocalPlacement.multiply(fp.LinkedObject.Placement)
				msgCsl("LocalPlacement: " + format(fp.LocalPlacement))

class ViewProviderCoordSys:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
#		obj.addProperty("App::PropertyColor","Color","CoordSys","Color of the box").Color=(1.0,0.0,0.0)
		self.Object = obj.Object
		self.icon = iconPath + 'WF_Axes.svg'
		obj.Proxy = self

	def getIcon(self):
		return iconPath + 'WF_Axes.svg'

	def attach(self, vobj):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		self.Object = vobj.Object
		self.standard = coin.SoGroup()
		vobj.addDisplayMode(self.standard,"Standard");

	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

	def getDisplayModes(self,fp):
		"'''Return a list of display modes.'''"
		return ["Standard"]

	def getDefaultDisplayMode(self):
		"'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
		return "Standard"

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
                Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
                to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
				Since no data were serialized nothing needs to be done here.'''
		return None

	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		obj.LinkedObject = None
		doc = FreeCAD.ActiveDocument
		doc.removeObject(obj.Tangent.Name)
		doc.removeObject(obj.Normal.Name)
		doc.removeObject(obj.Bend.Name)
		return True

class Rod:

	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink", "RootWire","Root","Root wire linked to the rod")
		obj.addProperty("App::PropertyLink", "TipWire","Tip","Tip wire linked to the rod")
		obj.addProperty("App::PropertyLink", "CoordSystem","Rod","Local coordinate system of the rod")
		obj.addProperty("App::PropertyFloat","RootPoint", "Root","Digit point of the root wire").RootPoint = 0.0
		obj.addProperty("App::PropertyFloat","TipPoint", "Tip","Digit point of the tip wire").TipPoint = 0.0
		obj.addProperty("App::PropertyBool","AutoRotate", "Rod","Rotate the rod according the mean of the root and tip tangents").AutoRotate = True
		obj.addProperty("App::PropertyDistance","RootOffset", "Root","Offset from the root (outside)").RootOffset = 1.0
		obj.addProperty("App::PropertyDistance","TipOffset", "Tip","Offset from the tip (outside)").TipOffset = 1.0
		obj.addProperty("App::PropertyDistance","RootInnerOffset", "Root","Root inner offset").RootInnerOffset = 0.0
		obj.addProperty("App::PropertyDistance","TipInnerOffset", "Tip","Tip inner offset").TipInnerOffset = 0.0
#		obj.addProperty("App::PropertyAngle","RootAngleOffset", "Rod","Angle offset").RootAngleOffset = 0.0
#		obj.addProperty("App::PropertyAngle","TipAngleOffset", "Rod","Angle offset").TipAngleOffset = 0.0
		self.VecRoot = VecNul
		self.VecRootTangent = VecNul
		self.VecRootCurvature = VecNul
		self.VecTip = VecNul
		self.VecTipTangent = VecNul
		self.VecTipCurvature = VecNul
		self.VecDirRod = VecNul
		self.VecRodEdge = VecNul
		self.VecRodCenter = VecNul
		self.ObjNameList = {"RootWire":"", "TipWire":"", "CoordSystem":""}
		obj.Proxy = self

	def check(self, fp):
		if hasattr(fp, "RootWire") and hasattr(fp, "TipWire") and hasattr(fp, "CoordSystem"):
			if fp.RootWire != None and fp.TipWire != None and fp.CoordSystem != None:
				if hasattr(fp.RootWire, 'Shape') and hasattr(fp, "RootPoint"):
					if hasattr(fp.TipWire, 'Shape') and hasattr(fp, "TipPoint"):
						return True
					else:
						return False
				else:
					return False
			else:
				return False
		else:
			return False
		return False

	def onChanged(self, fp, prop):
		# Do something when a property has changed
		if self.check(fp):
			if prop == "RootPoint":
	#			msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
				self.calcVecRoot(fp)
				self.updatePosition(fp)
			if prop == "TipPoint":
				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
				self.calcVecTip(fp)
				self.updatePosition(fp)
			if fp.getTypeIdOfProperty(prop) == 'App::PropertyLink':
				obj = fp.getPropertyByName(prop)
				if hasattr(obj, "Name"):
					if hasattr(self, "ObjNameList"):
						if obj.Name != self.ObjNameList[prop]:
							self.ObjNameList[prop] = obj.Name
							if prop == "RootWire":
				#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
								self.calcVecRoot(fp)
								self.updatePosition(fp)
							elif prop == "TipWire":
								msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
								self.calcVecTip(fp)
								self.updatePosition(fp)
							elif prop == "CoordSystem":
								self.updatePosition(fp)
#					else:
#						self.ObjNameList = {"RootWire":"", "TipWire":"", "CoordSystem":""}
			if prop == "TipOffset":
				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
				self.updateLength(fp)
			if prop == "RootOffset":
	#			msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
				self.updateLength(fp)
				self.updateRootPosition(fp)
			if prop == "RootInnerOffset":
	#			msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
				self.calcVecRoot(fp)
				self.updatePosition(fp)
			if prop == "TipInnerOffset":
	#			msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
				self.calcVecTip(fp)
				self.updatePosition(fp)
			if prop == "AutoRotate":
				self.updatePosition(fp)
			
	def __getstate__(self):
		state = {}
		state["VecRoot"] = list(self.VecRoot)
		state["VecRootTangent"] = list(self.VecRootTangent)
		state["VecRootCurvature"] = list(self.VecRootCurvature)
		state["VecTip"] = list(self.VecTip)
		state["VecTipTangent"] = list(self.VecTipTangent)
		state["VecTipCurvature"] = list(self.VecTipCurvature)
		state["VecDirRod"] = list(self.VecDirRod)
		state["VecRodEdge"] = list(self.VecRodEdge)
		state["VecRodCenter"] = list(self.VecRodCenter)
		return state

	def __setstate__(self, state):
		self.VecRoot = Vector(tuple( i for i in state["VecRoot"]))
		self.VecRootTangent = Vector(tuple( i for i in state["VecRootTangent"]))
		self.VecRootCurvature = Vector(tuple( i for i in state["VecRootCurvature"]))
		self.VecTip = Vector(tuple( i for i in state["VecTip"]))
		self.VecTipTangent = Vector(tuple( i for i in state["VecTipTangent"]))
		self.VecTipCurvature = Vector(tuple( i for i in state["VecTipCurvature"]))
		self.VecDirRod = Vector(tuple( i for i in state["VecDirRod"]))
		self.VecRodEdge = Vector(tuple( i for i in state["VecRodEdge"]))
		self.VecRodCenter = Vector(tuple( i for i in state["VecRodCenter"]))
		self.ObjNameList = {"RootWire":"", "TipWire":"", "CoordSystem":""}

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")
	
#	def testWires(self, fp):
#		test = False
#		if hasattr(fp.RootWire, 'Shape'):
#			if hasattr(fp.TipWire, 'Shape'):
#				if fp.CoordSystem != None: test = True
#				else: test = False
#			else:
#				test = False
#		else:
#			test = False
##		msgCsl("testWires " + str(test))
#		return test

	def calcVecRoot(self, fp):
#		if self.testWires(fp):
#			msgCsl("int(fp.RootPoint) "+ str(int(fp.RootPoint)))
			mEdge = fp.RootWire.Shape.Edges[int(fp.RootPoint)]
#			msgCsl("mEdge "+ str(mEdge))
			Fract = int((round(fp.RootPoint,2) - int(fp.RootPoint))*100)
#			msgCsl("Fract "+ str(Fract))
			if Fract > 0:
				Pts = mEdge.discretize(101)
				Pt = Pts[Fract]
			else:
				Pt = fp.RootWire.Shape.Vertexes[int(fp.RootPoint)].Point
			msgCsl("Pt "+ format(Pt))
			# Root tangent, curvature axis calculated with adjacent points:
#			pc = fp.RootWire.Shape.Vertexes[int(fp.RootPoint)].Point
#			pav = fp.RootWire.Shape.Vertexes[int(fp.RootPoint)-1].Point
#			pap = fp.RootWire.Shape.Vertexes[int(fp.RootPoint)+1].Point
#			msgCsl("pc "+ format(pc))
#			msgCsl("pav "+ format(pav))
#			msgCsl("pap "+ format(pap))
#			self.VecRootTangent = PtsToVec(pav,pap)
#			msgCsl("indice VecRootTangent: " + str(self.VecList["VecRootTangent"]) + " vector VecRootTangent: " + format(fp.VectorList[self.VecList["VecRootTangent"]]))
#			self.VecRootTangent.normalize()
			self.VecRootTangent = tangentVec(fp.RootWire, int(fp.RootPoint))
#			nbpts = len(fp.RootWire.Points)
#			gap = int(nbpts/3)
#			pav = fp.RootWire.Shape.Vertexes[int(fp.RootPoint) - gap].Point
#			pap = fp.RootWire.Shape.Vertexes[int(fp.RootPoint) + gap].Point
#			VecRootNormal = PtsToVec(pc,pav).cross(PtsToVec(pc,pap))
#			VecRootNormal.normalize()
			VecRootNormal = normalVec(fp.RootWire, int(fp.RootPoint))
#			msgCsl("VecRootNormal count i " + str(i))
			self.VecRootCurvature = self.VecRootTangent.cross(VecRootNormal)
#			msgCsl("VecRootNormal "+ format(VecRootNormal))
			self.VecRootCurvature.normalize()
			if fp.RootInnerOffset != 0:
				self.VecRoot = Pt.add(self.VecRootCurvature.multiply(fp.RootInnerOffset))
				self.VecRootCurvature.normalize()
			else:
				self.VecRoot = Pt
#			msgCsl("VecRoot "+ format(self.VecRoot))
			self.calcVecDirRod(fp)

	def calcVecTip(self, fp):
#		if fp.TipWire != None:
			mEdge = fp.TipWire.Shape.Edges[int(fp.TipPoint)]
			msgCsl("mEdge "+ str(mEdge))
			Fract = int((round(fp.TipPoint,2) - int(fp.TipPoint))*100)
			msgCsl("Fract "+ str(Fract))
			if Fract > 0:
				Pts = mEdge.discretize(101)
				Pt = Pts[Fract]
			else:
				Pt = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)].Point
			msgCsl("Pt "+ format(Pt))
			# Tip tangent, normal, curvature axis calculated with adjacent points:
#			pc = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)].Point
#			pav = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)-1].Point
#			pap = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)+1].Point
#			self.VecTipTangent = PtsToVec(pav,pap)
#			self.VecTipTangent.normalize()
			self.VecTipTangent = tangentVec(fp.TipWire, int(fp.TipPoint))
#			nbpts = len(fp.TipWire.Points)
#			gap = int(nbpts/3)
#			pav = fp.TipWire.Shape.Vertexes[int(fp.TipPoint) - gap].Point
#			pap = fp.TipWire.Shape.Vertexes[int(fp.TipPoint) + gap].Point
#			VecTipNormal = PtsToVec(pc,pav).cross(PtsToVec(pc,pap))
#			VecTipNormal.normalize()
			VecTipNormal = normalVec(fp.TipWire, int(fp.TipPoint))
#			msgCsl("VecTipNormal count i " + str(i))					
			self.VecTipCurvature = self.VecTipTangent.cross(VecTipNormal)
			msgCsl("VecTipNormal "+ format(VecTipNormal))
			self.VecTipCurvature.normalize()
			if fp.TipInnerOffset != 0:
				self.VecTip = Pt.add(self.VecTipCurvature.multiply(fp.TipInnerOffset))
				self.VecTipCurvature.normalize()
			else:
				self.VecTip = Pt
#				msgCsl("VecTip "+ format(self.VecTip))
			self.calcVecDirRod(fp)

	def calcVecDirRod(self, fp):
		self.VecDirRod = self.VecTip.sub(self.VecRoot)
#		msgCsl("VecDirRod "+ format(self.VecDirRod))

	def calcVecRod(self, fp):
#		if self.testWires(fp):
			self.VecRodCenter = fp.CoordSystem.Tangent.Start
			self.VecRodEdge = PtsToVec(fp.CoordSystem.Tangent.Start,fp.CoordSystem.Tangent.End)

	def updateRootPosition(self, fp):
#		if self.testWires(fp) and fp.CoordSystem.Proxy.ObjectOk:
			mDir = self.VecDirRod
			mDir = FreeCAD.Vector(mDir.x, mDir.y, mDir.z)
			mDir.normalize()
			mDir.multiply(-fp.RootOffset)
			self.calcVecRod(fp)
			mDir = mDir.sub(PtsToVec(self.VecRoot,self.VecRodCenter))
			mPlacement = Placement(mDir,Rotation())
#			mPlacement.move(mDir)
			mPlacement = mPlacement.multiply(fp.CoordSystem.Tangent.Placement)
			self.updateAxis(fp.CoordSystem, mPlacement)
#			fp.CoordSystem.Tangent.Placement = mPlacement.multiply(fp.CoordSystem.Tangent.Placement)
#			fp.CoordSystem.Bend.Placement = mPlacement.multiply(fp.CoordSystem.Bend.Placement)
#			fp.CoordSystem.Normal.Placement = mPlacement.multiply(fp.CoordSystem.Normal.Placement)
			self.updateLength

	def updateLength(self, fp):
#		if self.testWires(fp):
			if fp.CoordSystem.LinkedObject.TypeId in ["Part::Box","Part::Cylinder"]:
#				fp.Rod.Height = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)
				fp.CoordSystem.LinkedObject.Height = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)
#				msgCsl("indice VecDirRod: " + str(self.VecList["VecDirRod"]) + " vector VecDirRod: " + format(fp.VectorList[self.VecList["VecDirRod"]]))
			if fp.CoordSystem.LinkedObject.TypeId == "PartDesign::Pad":
#				fp.Rod.Length = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)
				fp.CoordSystem.LinkedObject.Length = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)
			if fp.CoordSystem.LinkedObject.TypeId == "Part::Extrusion":
#				fp.Rod.Length = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)
				fp.CoordSystem.LinkedObject.Dir.Length = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)

	def updateAxis(self, obj, placmnt):
		obj.Tangent.Placement = placmnt
		obj.Bend.Placement = placmnt
		obj.Normal.Placement = placmnt
#		obj.Proxy.updatePlacement(obj)

	def updatePosition(self,fp):
#		if self.testWires(fp) and fp.CoordSystem.Proxy.ObjectOk:
			VecRoot = self.VecRoot
			VecDirRod = self.VecDirRod
			mRot = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), VecDirRod)
			msgCsl("VecRoot "+ format(VecRoot))
			mPlacementAlign = Placement()
			mPlacementAlign.move(VecRoot)
			mPlacementAlign = FreeCAD.Placement(VecNul, mRot, VecRoot).multiply(mPlacementAlign)
			msgCsl("mPlacementAlign "+ format(mPlacementAlign))
			self.updateAxis(fp.CoordSystem, mPlacementAlign)
			if fp.AutoRotate:
				VecRootTangent = self.VecRootTangent
				VecTipTangent = self.VecTipTangent
				VecBisector = VecRootTangent.add(VecTipTangent).normalize()  # Vector mean of root and tip tangents
#				msgCsl("VecBisector "+ format(VecBisector))
				VecBisector.projectToPlane(VecNul,VecDirRod)  # projection in the normal plan of rod axis
#				msgCsl("VecBisector "+ format(VecBisector))
#				msgCsl("VecRootTangent "+ format(VecRootTangent))
#				msgCsl("VecTipTangent "+ format(VecTipTangent))
				mRot = FreeCAD.Rotation(fp.CoordSystem.Tangent.End.sub(fp.CoordSystem.Tangent.Start), VecBisector)
#				msgCsl("Rotation "+ format(mRot))
				mPlacement = FreeCAD.Placement(VecNul, mRot, VecRoot)
#				msgCsl("Placement Rotation "+ format(mPlacement))
				self.updateAxis(fp.CoordSystem, mPlacement.multiply(fp.CoordSystem.Tangent.Placement))
			self.updateRootPosition(fp)
			self.updateLength(fp)

class ViewProviderRod:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + 'Rod-icon.svg'
		obj.Proxy = self

	def getIcon(self):
		return iconPath + 'Rod-icon.svg' #self.icon

	def attach(self, vobj):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		self.Object = vobj.Object
		self.standard = coin.SoGroup()
		vobj.addDisplayMode(self.standard,"Standard");

	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

	def getDisplayModes(self,fp):
		"'''Return a list of display modes.'''"
		return ["Standard"]

	def getDefaultDisplayMode(self):
		"'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
		return "Standard"

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
                Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
                to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
				Since no data were serialized nothing needs to be done here.'''
		return None

class WrapLeadingEdge:

	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink", "RootWire", "Root", "Wire of the wing root")
		obj.addProperty("App::PropertyLink", "TipWire", "Tip", "Wire of the wing tip")
		obj.addProperty("App::PropertyFloat","RootStartPoint", "Root","Start digit point of the root wire").RootStartPoint = 0.0
		obj.addProperty("App::PropertyFloat","RootEndPoint", "Root","Number of points of the root wrap").RootEndPoint = 1.0
		obj.addProperty("App::PropertyFloat","TipStartPoint", "Tip","Start digit point of the tip wire").TipStartPoint = 0.0
		obj.addProperty("App::PropertyFloat","TipEndPoint", "Tip","Number of points of the tip wrap").TipEndPoint = 1.0
		obj.addProperty("App::PropertyDistance", "Thickness", "WrapLeadingEdge", "Thickness of the wrap").Thickness = 1.5
		obj.addProperty("App::PropertyBool", "MakeLoft", "WrapLeadingEdge", "Make the loft from the root wrap and tip wrap wires").MakeLoft = False
		obj.addProperty("App::PropertyLink","Loft","WrapLeadingEdge","Name of the wrapped leading edge's loft", 1)
		obj.addProperty("App::PropertyLink", "RootWrap", "Root", "Wrapped wire of the wing root", 1)
		obj.addProperty("App::PropertyLink", "TipWrap", "Tip", "Wrapped wire of the wing tip", 1)
		self.LoftName = ""
		self.RootWireLinked = False
		self.TipWireLinked = False
		obj.Proxy = self

	def onChanged(self, fp, prop):
		# Do something when a property has changed
		if prop in ["RootStartPoint", "RootEndPoint"]:
			if self.RootWireLinked:
				self.updateWrap(fp, fp.RootWire, fp.RootStartPoint, fp.RootEndPoint, "Root")
		if prop == "RootWire":
			if not self.RootWireLinked:
				self.createWrap(fp, fp.RootWire, fp.RootStartPoint, fp.RootEndPoint, "Root")
				self.RootWireLinked = True
			else:
				self.updateWrap(fp, fp.RootWire, fp.RootStartPoint, fp.RootEndPoint, "Root")
		if prop in ["TipStartPoint", "TipEndPoint"]:
			if self.TipWireLinked:
				self.updateWrap(fp, fp.TipWire, fp.TipStartPoint, fp.TipEndPoint, "Tip")
		if prop == "TipWire":
			if not self.TipWireLinked:
				self.createWrap(fp, fp.TipWire, fp.TipStartPoint, fp.TipEndPoint, "Tip")
				self.TipWireLinked = True
			else:
				self.updateWrap(fp, fp.TipWire, fp.TipStartPoint, fp.TipEndPoint, "Tip")
		if prop == "Thickness":
			self.updateWrap(fp, fp.RootWire, fp.RootStartPoint, fp.RootEndPoint, "Root")
			self.updateWrap(fp, fp.TipWire, fp.TipStartPoint, fp.TipEndPoint, "Tip")
		if prop == "MakeLoft":
			if fp.MakeLoft:
				self.createLoft(fp)
			else:
				# remove Loft
				FreeCAD.ActiveDocument.removeObject(fp.Loft.Name)

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")
		
	def createLoft(self, fp):
		#############################
		# Leading edge wrap loft creation
		#############################
		wraploft = FreeCAD.ActiveDocument.addObject('Part::Loft','Loft')
		wraploft.Label = "Loft_WrapLeadingEdge"
		fp.Loft = wraploft
		wraploft.Sections = [fp.RootWrap, fp.TipWrap]
		wraploft.Solid = True
		wraploft.Ruled = False
		FreeCAD.ActiveDocument.recompute()
		FreeCADGui.SendMsgToActiveView("ViewFit")

	def calculateWrapPoints(self, fp, wire, start, end):
		pts = []
		if wire != None and int(end) > int(start):
			pts.append(DiscretizedPoint(wire, start))
			nbpts = int(end) - int(start)
			i = 1
			while i < (nbpts + 1):
				pts.append(wire.Shape.Vertexes[int(start) + i].Point)
				i += 1
			if end > int(end):
				pt = DiscretizedPoint(wire, end)
				pts.append(pt)
			nbpts = len(pts)
			for i in range(nbpts-1, -1, -1):
				vecdec = curveVec(wire, int(start) + i)
				vecdec.normalize()
				vecdec.multiply(fp.Thickness)
				pts.append(pts[i].add(vecdec))
		return pts

	def createWrap(self, fp, wire,  start,  end,  side):
		if wire != None and int(end) > int(start):
			pts = self.calculateWrapPoints(fp, wire, start, end)
			wrapobj = Draft.makeWire(pts, True, False)
			if side == "Root":
				wrapobj.Label = "RootWrap"
				fp.RootWrap = wrapobj
			else:
				wrapobj.Label = "TipWrap"
				fp.TipWrap = wrapobj
	
	def updateWrap(self, fp, wire,  start,  end,  side):
		if wire != None and int(end) > int(start):
			pts = self.calculateWrapPoints(fp, wire, start, end)
			wrapOk = False
			if side == "Root":
				if fp.RootWrap != None :
					wrappts = fp.RootWrap.Points
					wrapOk = True
			else:
				if fp.TipWrap != None :
					wrappts = fp.TipWrap.Points
					wrapOk = True
			if wrapOk:
				nbwrap = len(wrappts)
				nbpts = len(pts)
				msgCsl("len(wrappts): " + str(nbwrap) + "  len(pts): " + str(nbpts))
				if nbpts < nbwrap:
					for i in range(nbpts, nbwrap, +1):
#						msgCsl("count i: " + str(i))
						wrappts.remove(wrappts[nbpts])
				if nbpts > nbwrap:
					for i in range(nbwrap, nbpts, +1):
						wrappts.append(pts[i])   # pts[i] does not matter, it's just to increase the wire points number
				if side == "Root":
					fp.RootWrap.Points = pts
				else:
					fp.TipWrap.Points = pts

class ViewProviderWrapLeadingEdge:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + 'WrapLeadingEdge-icon.svg'
		obj.Proxy = self

	def getIcon(self):
		return iconPath + 'WrapLeadingEdge-icon.svg'
		
	def attach(self, vobj):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		self.Object = vobj.Object
		self.standard = coin.SoGroup()
		vobj.addDisplayMode(self.standard,"Standard");

	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

	def getDisplayModes(self,fp):
		"'''Return a list of display modes.'''"
		return ["Standard"]

	def getDefaultDisplayMode(self):
		"'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
		return "Standard"

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
				Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
				to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
				Since no data were serialized nothing needs to be done here.'''
		return None

def createWing():
	msgCsl("createWing method starting...")
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Wing")  #FeaturePython
	Wing(obj)
	ViewProviderWing(obj.ViewObject)
	if len(sel) > 0:
		wobj = sel[0].Object
#		msgCsl(wobj.Proxy.__class__.__name__)
		if wobj.Proxy.__class__.__name__ == "Profile":
			obj.RootProfile = wobj
	if len(sel) > 1:
		wobj = sel[1].Object
		if wobj.Proxy.__class__.__name__ == "Profile":
			obj.TipProfile = wobj
		
	FreeCAD.ActiveDocument.recompute()
	FreeCADGui.SendMsgToActiveView("ViewFit")

def createCoordSys():
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "CoordSystem")
	CoordSys(obj)
	ViewProviderCoordSys(obj.ViewObject)
	if len(sel) > 0:
		msgCsl("Wing found for linking Rod")
		pobj = sel[0].Object
		if pobj.TypeId in ["Part::Box", "Part::Extrusion", "Part::Cylinder", "PartDesign::Pad"]:
			obj.LinkedObject = pobj
	
def createRod():
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Rod")
	Rod(obj)
	ViewProviderRod(obj.ViewObject)

	if len(sel) > 0:
		msgCsl("Wing found for linking Rod")
		wobj = sel[0].Object
		if wobj.Proxy.__class__.__name__ == "Wing":
			msgCsl("Wing type found in selection")
			if hasattr(wobj, "RootProfile"):
				if wobj.RootProfile != None: obj.RootWire = wobj.RootProfile.Wire
			if hasattr(wobj, "TipProfile"):
				if wobj.TipProfile != None: obj.TipWire = wobj.TipProfile.Wire
			obj.RootPoint = 1
			obj.TipPoint = 1
	if len(sel) > 1:
		wobj = sel[1].Object
		if wobj.Proxy.__class__.__name__ == "CoordSys":
			obj.CoordSystem = wobj	
		
#  temporaire !!!!!!!!!!!!
#	obj.RootWire = FreeCAD.ActiveDocument.DWire  #  temporaire !!!!!!!!!!!!
#	obj.TipWire = FreeCAD.ActiveDocument.DWire001  #  temporaire !!!!!!!!!!!!
#	obj.RootPoint = 20  #  temporaire !!!!!!!!!!!!
#	obj.TipPoint = 15  #  temporaire !!!!!!!!!!!!
#	FreeCAD.ActiveDocument.Wing.addObject(obj)
#  temporaire !!!!!!!!!!!!

	return obj

def createWrapLeadingEdge():
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "WrapLeadingEdge")
	WrapLeadingEdge(obj)
	ViewProviderWrapLeadingEdge(obj.ViewObject)
	obj.RootStartPoint = 1.0
	obj.RootEndPoint = 2.0
	obj.TipStartPoint = 1.0
	obj.TipEndPoint = 2.0
	if len(sel) > 0:
		wobj = sel[0].Object
		if wobj.Proxy.__class__.__name__ == "Wing":
			msgCsl("Wing type found in selection for linking WrapLeadingEdge")
			obj.RootWire = wobj.RootProfile.Wire
			obj.TipWire = wobj.TipProfile.Wire
#			obj.Proxy.createWrap(obj, obj.RootWire, obj.RootStartPoint, obj.RootLength, "Root")
#			obj.Proxy.createWrap(obj, obj.TipWire, obj.TipStartPoint, obj.TipLength, "Tip")
		return obj
	else:
		userMsg("No selection or selection is not a wing object")

def createProfile():
	msgCsl("importProfile method starting...")
	a = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Profile")
	Profile(a)
	ViewProviderProfile(a.ViewObject)
	a.Scale = 300
