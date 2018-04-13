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

class ViewProviderGeneric():

	def __init__(self, obj, icon = 'Aile-icon.svg'):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + icon
		obj.Proxy = self

	def getIcon(self):
		return self.icon

	def attach(self, vobj):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		self.Object = vobj.Object
		self.standard = coin.SoGroup()
		vobj.addDisplayMode(self.standard,"Standard")
		icon = 'Aile-icon.svg'
		self.icon = iconPath + icon

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

class ViewProviderProfile(ViewProviderGeneric):

	def getIcon(self):
		return iconPath + 'Profile-icon.svg' #self.icon
		
	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		doc.removeObject(obj.Wire.Name)
		return True

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
#		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop in ["Length", "TipXOffset", "TipYOffset", "TipAngle"] and self.check(fp):
			if hasattr(fp, "TipYOffset"):
				self.updatePosition(fp)
		if prop in ["RootProfile", "TipProfile"] and self.check(fp):
#			msgCsl("prop in RootProfile...")
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

class ViewProviderWing(ViewProviderGeneric):

	def getIcon(self):
		return iconPath + 'Aile-icon.svg'
		

class CoordSys:
	
	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink","LinkedObject","LinkedObject","Object to link with the coordinate system")
		obj.addProperty("App::PropertyEnumeration","CenterType","Settings","Either center of mass or vertexes").CenterType = ["MassCenter","Vertexes"]
		obj.addProperty("App::PropertyFloat","VertexNum","Settings","Vertexes or intermediate point of vertexes couple").VertexNum = 0.0
		obj.addProperty("App::PropertyAngle","Angle","Settings","Deviation").Angle = 0.0
		obj.addProperty("App::PropertyLink","Tangent","Axis","Axis tangent to an edge", 1)
		obj.addProperty("App::PropertyLink","Normal","Axis","Normal of the reference face", 1)
		obj.addProperty("App::PropertyLink","Bend","Axis","Bend axis", 1)
		obj.addProperty("App::PropertyPlacement","LocalPlacement","Axis","Placement from linked object origin to new coordsys")
		obj.addProperty("App::PropertyEnumeration","Direction","Settings","X axis tangent to edge or Y axis through center of mass").Direction = ["Edge", "CenterOfMass"]
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
		obj.Direction = "Edge"
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
#		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop == "LinkedObject":
#			msgCsl("CoordSys class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
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
		if prop in ["CenterType","VertexNum", "Normal", "Direction", "Angle"]:
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
				index = int(fp.VertexNum % len(self.ObjectEdges))
				if fp.LinkedObject.TypeId == "PartDesign::Pad":
					fp.LinkedObject.Sketch.Placement = fp.Tangent.Placement
				else:
					fp.LinkedObject.Placement = fp.Tangent.Placement
				self.updateRefFace(fp)
				Fract = (int((round(fp.VertexNum,2) - int(fp.VertexNum)) * 100) + 100) % 100
#				msgCsl("Fract "+ str(Fract))
				mEdge = self.ObjectEdges[index]
				if Fract > 0:
					Pts = mEdge.discretize(101)
					Pt = Pts[Fract]  # Not Fract in order to have Y (Bend) local axis inward
				else:
					Pt = mEdge.valueAt(0) #mEdge.Length)
				if fp.CenterType == "MassCenter":
					self.NewOrigin = self.ObjectCenterOfMass
					mBend = PtsToVec(self.NewOrigin,Pt)
				else:
					self.NewOrigin = Pt
#					if fp.Direction == "Edge":
#						mBend = self.ObjectEdges[int(fp.VertexNum)].tangentAt(0)
#					else:
					mBend = PtsToVec(self.NewOrigin, self.ObjectCenterOfMass)
#				msgCsl("NewOrigin " + format(self.NewOrigin))
				mTrans = PtsToVec(self.NewOrigin,self.ObjectOrigin)
				if fp.CenterType == "Vertexes" and fp.Direction == "Edge":
					vectan = self.ObjectEdges[index].tangentAt(mEdge.Length * Fract / 100) #PtsToVec(self.ObjectEdges[int(fp.VertexNum)].Start, self.ObjectEdges[int(fp.VertexNum)].End)
#					vectan.multiply(-1)
					mRot = Rotation(vectan, fp.Tangent.End.sub(fp.Tangent.Start))
				else:
					mRot = Rotation(mBend,fp.Bend.End.sub(fp.Bend.Start))
				mPlacement2 = FreeCAD.Placement(mTrans,mRot,self.NewOrigin)
				fp.LocalPlacement = mPlacement2
				# Add rotation angle from CoordSys property
				mPlacement2 = Placement(VecNul, Rotation(fp.Normal.End.sub(fp.Normal.Start), fp.Angle), fp.Tangent.Start)
				fp.LocalPlacement = mPlacement2.multiply(fp.LocalPlacement)
				if fp.LinkedObject.TypeId == "PartDesign::Pad":
					fp.LinkedObject.Sketch.Placement = fp.LocalPlacement.multiply(fp.LinkedObject.Sketch.Placement)
				else:
					fp.LinkedObject.Placement = fp.LocalPlacement.multiply(fp.LinkedObject.Placement)
#				msgCsl("LocalPlacement: " + format(fp.LocalPlacement))

class ViewProviderCoordSys(ViewProviderGeneric):

	def getIcon(self):
		return iconPath + 'WF_Axes.svg'

	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		obj.LinkedObject = None
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
		obj.addProperty("App::PropertyDistance","RootInwardOffset", "Root","Root inner offset").RootInwardOffset = 0.0
		obj.addProperty("App::PropertyDistance","TipInwardOffset", "Tip","Tip inner offset").TipInwardOffset = 0.0
		obj.addProperty("App::PropertyEnumeration","TangentType","Settings","Either center of mass or vertexes").TangentType = ["Previous", "Next", "PreviousAndNext"]	
		obj.addProperty("App::PropertyAngle","AngleOffset", "Settings","Angle offset").AngleOffset = 0.0
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
		obj.TangentType = "Next"
		obj.Proxy = self

	def check(self, fp):
		test = False
		if hasattr(fp, "RootWire") and hasattr(fp, "TipWire") and hasattr(fp, "CoordSystem"):
			if fp.RootWire != None and fp.TipWire != None and fp.CoordSystem != None:
				if hasattr(fp.RootWire, 'Shape') and hasattr(fp, "RootPoint"):
					if hasattr(fp.TipWire, 'Shape') and hasattr(fp, "TipPoint"):
						if len(fp.RootWire.Shape.Edges) > 0 and len(fp.TipWire.Shape.Edges) > 0: test = True
#						if hasattr(fp.RootWire.Shape, "Edges") and hasattr(fp.TipWire.Shape, "Edges"):
		return test

	def onChanged(self, fp, prop):
		# Do something when a property has changed
		if self.check(fp):
			if prop in ["RootPoint", "TipPoint", "RootOffset", "TipOffset", "RootInwardOffset",
						"TipInwardOffset", "AutoRotate", "TangentType", "AngleOffset"]:
				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
#				self.calcVecRoot(fp)
				self.updatePosition(fp)
#			if prop == "TipPoint":
#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
##				self.calcVecTip(fp)
#				self.updatePosition(fp)
			if fp.getTypeIdOfProperty(prop) == 'App::PropertyLink':
				obj = fp.getPropertyByName(prop)
				if hasattr(obj, "Name") and hasattr(self, "ObjNameList"):
					if obj.Name != self.ObjNameList[prop]:
						self.ObjNameList[prop] = obj.Name
						if prop in ["RootWire", "TipWire", "CoordSystem"]:
							msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
#								self.calcVecRoot(fp)
							self.updatePosition(fp)
#							elif prop == "TipWire":
#								msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
##								self.calcVecTip(fp)
#								self.updatePosition(fp)
#							elif prop == "CoordSystem":
#								self.updatePosition(fp)
#					else:
#						self.ObjNameList = {"RootWire":"", "TipWire":"", "CoordSystem":""}
#			if prop == "TipOffset":
#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
#				self.updateLength(fp)
#			if prop == "RootOffset":
#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
#				self.updateRootPosition(fp)
#			if prop == "RootInwardOffset":
#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
##				self.calcVecRoot(fp)
#				self.updatePosition(fp)
#			if prop == "TipInwardOffset":
#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
##				self.calcVecTip(fp)
#				self.updatePosition(fp)
#			if prop == "AutoRotate":
#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
#				self.updatePosition(fp)
#			if prop == "TangentType":
##				self.calcVecRoot(fp)
##				self.calcVecTip(fp)
#				self.updatePosition(fp)
			
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
	
	def calcVecRoot(self, fp):
		msgCsl("int(fp.RootPoint) "+ str(int(fp.RootPoint)))
		msgCsl("nb fp.RootWire.Shape.Edges: " + str(len(fp.RootWire.Shape.Edges)))
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
		self.VecRootTangent = tangentVec(fp.RootWire, int(fp.RootPoint), fp.TangentType)
		VecRootNormal = normalVec(fp.RootWire, int(fp.RootPoint))
		self.VecRootCurvature = self.VecRootTangent.cross(VecRootNormal)
#			msgCsl("VecRootNormal "+ format(VecRootNormal))
		self.VecRootCurvature.normalize()
		if fp.RootInwardOffset != 0:
			self.VecRoot = Pt.add(self.VecRootCurvature.multiply(fp.RootInwardOffset))
			self.VecRootCurvature.normalize()
		else:
			self.VecRoot = Pt
#		msgCsl("VecRoot "+ format(self.VecRoot))
		self.calcVecDirRod(fp)

	def calcVecTip(self, fp):
		mEdge = fp.TipWire.Shape.Edges[int(fp.TipPoint)]
#		msgCsl("mEdge "+ str(mEdge))
		Fract = int((round(fp.TipPoint,2) - int(fp.TipPoint))*100)
#		msgCsl("Fract "+ str(Fract))
		if Fract > 0:
			Pts = mEdge.discretize(101)
			Pt = Pts[Fract]
		else:
			Pt = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)].Point
		msgCsl("Pt "+ format(Pt))
		# Tip tangent, normal, curvature axis calculated with adjacent points:
		self.VecTipTangent = tangentVec(fp.TipWire, int(fp.TipPoint), fp.TangentType)
		VecTipNormal = normalVec(fp.TipWire, int(fp.TipPoint))
		self.VecTipCurvature = self.VecTipTangent.cross(VecTipNormal)
#		msgCsl("VecTipNormal "+ format(VecTipNormal))
		self.VecTipCurvature.normalize()
		if fp.TipInwardOffset != 0:
			self.VecTip = Pt.add(self.VecTipCurvature.multiply(fp.TipInwardOffset))
			self.VecTipCurvature.normalize()
		else:
			self.VecTip = Pt
#		msgCsl("VecTip "+ format(self.VecTip))
		self.calcVecDirRod(fp)

	def calcVecDirRod(self, fp):
		self.VecDirRod = self.VecTip.sub(self.VecRoot)
#		msgCsl("VecDirRod "+ format(self.VecDirRod))

	def calcVecRod(self, fp):
#		if self.testWires(fp):
			self.VecRodCenter = fp.CoordSystem.Tangent.Start
			self.VecRodEdge = PtsToVec(fp.CoordSystem.Tangent.Start,fp.CoordSystem.Tangent.End)

	def updateRootPosition(self, fp):
		mDir = self.VecDirRod
		if mDir != VecNul:
			mDir = FreeCAD.Vector(mDir.x, mDir.y, mDir.z)
			mDir.normalize()
			mDir.multiply(-fp.RootOffset)
			self.calcVecRod(fp)
			mDir = mDir.sub(PtsToVec(self.VecRoot,self.VecRodCenter))
			mPlacement = Placement(mDir,Rotation())
			mPlacement = mPlacement.multiply(fp.CoordSystem.Tangent.Placement)
			mPlacement = Placement(VecNul, Rotation(mDir, fp.AngleOffset), DiscretizedPoint(fp.RootWire, fp.RootPoint)).multiply(mPlacement)
			self.updateAxis(fp.CoordSystem, mPlacement)
			self.updateLength(fp)

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
		obj.Proxy.updatePlacement(obj)

	def updatePosition(self,fp):
#		if self.testWires(fp) and fp.CoordSystem.Proxy.ObjectOk:
			self.calcVecRoot(fp)
			self.calcVecTip(fp)
			VecRoot = self.VecRoot
			VecDirRod = self.VecDirRod
			mRot = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), VecDirRod)
#			msgCsl("VecRoot "+ format(VecRoot))
			mPlacementAlign = Placement()
			mPlacementAlign.move(VecRoot)
			mPlacementAlign = FreeCAD.Placement(VecNul, mRot, VecRoot).multiply(mPlacementAlign)
#			msgCsl("mPlacementAlign "+ format(mPlacementAlign))
			self.updateAxis(fp.CoordSystem, mPlacementAlign)
			if fp.AutoRotate and self.VecRootTangent != VecNul:
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
#				mPlacement = mPlacement.multiply(mPlacement2)
#				msgCsl("Rotation center: " + format(DiscretizedPoint(fp.RootWire, fp.RootPoint)))
#				msgCsl("Placement Rotation "+ format(mPlacement))
				self.updateAxis(fp.CoordSystem, mPlacement.multiply(fp.CoordSystem.Tangent.Placement))
			self.updateRootPosition(fp)


class ViewProviderRod(ViewProviderGeneric):

	def getIcon(self):
		return iconPath + 'Rod-icon.svg' #self.icon


class WrapLeadingEdge:

	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink", "Wire", "LinkedObject", "Wire to wrap")
		obj.addProperty("App::PropertyFloat","StartPoint", "Settings","Start point of the wrap").StartPoint = 0.0
		obj.addProperty("App::PropertyFloat","EndPoint", "Settings","End point of the wrap").EndPoint = 1.0
		obj.addProperty("App::PropertyDistance", "Thickness", "Settings", "Thickness of the wrap").Thickness = 1.5
		obj.addProperty("App::PropertyLink", "Wrap", "LinkedObject", "Wrapped wire", 1)
		obj.addProperty("App::PropertyLink", "CutWire", "LinkedObject", "Cut wire after having cut the wrap", 1)
		self.WireLinked = False
		obj.Proxy = self

	def onChanged(self, fp, prop):
		# Do something when a property has changed
		if hasattr(fp, "Wire"):
			if fp.Wire != None:
				if prop in ["StartPoint", "EndPoint", "Thickness"]:
					if self.WireLinked:
						self.updateWrap(fp, fp.Wire, fp.StartPoint, fp.EndPoint)
						self.updateCutWire(fp.Wire, fp.Wrap, fp.CutWire, fp.StartPoint, fp.EndPoint)
				if prop == "Wire":
					if not self.WireLinked:
						self.createWrap(fp, fp.Wire, fp.StartPoint, fp.EndPoint)
						self.WireLinked = True
					elif hasattr(fp, "Wrap"):
						self.updateWrap(fp, fp.Wire, fp.StartPoint, fp.EndPoint)
						self.updateCutWire(fp.Wire, fp.Wrap, fp.CutWire, fp.StartPoint, fp.EndPoint)

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")

	def calculateWrapPoints(self, fp, wire, start, end):
		pts = []
		if wire != None and int(end) > int(start):
			pts.append(DiscretizedPoint(wire, start))
#			nbpts = int(end) - int(start)
			nbp = int(end) - int(start)
			i = 1
			while i < (nbp + 1):
				pts.append(wire.Shape.Vertexes[int(start) + i].Point)
				i += 1
			if end > int(end):
				pt = DiscretizedPoint(wire, end)
				pts.append(pt)
				nbp += 1
#			nbpts = 2 * nbp #len(pts)
			for i in range(nbp, -1, -1):
				vecdec = curveVec(wire, int(start) + i)
				vecdec.normalize()
				vecdec.multiply(fp.Thickness)
				pts.append(pts[i].add(vecdec))
		return pts
	
	def calculateCutWirePoints(self, wire, wrap, start, end):
		pts2 = []
		if wire != None and wrap != None and int(end) > int(start):
			pts = wrap.Points
			nbp = int(len(pts) / 2)
			i = 0
			while i <= int(start):
				pts2.append(wire.Shape.Vertexes[i].Point)
				i += 1
			if start > int(start):  # if start point is inside edge
				pts2.append(pts[0])
			for i in range(2 * nbp - 1, nbp - 2, -1):  # end=nbp then -1 because of index start at 0, then -1 because range stops at end-1
				pts2.append(pts[i])
#			if end > int(end):
#				pts2.append(pts[nbp])
			for i in range(int(end) + 1, len(wire.Points), +1):
				pts2.append(wire.Shape.Vertexes[i].Point)
		return pts2

	def createWrap(self, fp, wire,  start,  end):
		if wire != None and int(end) > int(start):
			msgCsl("create wrap")
			pts = self.calculateWrapPoints(fp, wire, start, end)
			wrapobj = Draft.makeWire(pts, True, False)
			wrapobj.Label = "Wrap"
			fp.Wrap = wrapobj
			msgCsl("create cut wire")
			pts2 = self.calculateCutWirePoints(wire, wrapobj, start, end)
			cutobj = Draft.makeWire(pts2, True, False)
			cutobj.Label = "CutWire"
			fp.CutWire = cutobj
	
	def updateWrap(self, fp, wire, start, end):
		if wire != None and fp.Wrap != None and int(end) > int(start):
			pts = self.calculateWrapPoints(fp, wire, start, end)
			wrappts = fp.Wrap.Points
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
			fp.Wrap.Points = pts

	def updateCutWire(self, wire, wrap, cutwire, start, end):
		if wire != None and wrap != None and int(end) > int(start):
			pts = self.calculateCutWirePoints(wire, wrap, start, end)
			wrappts = cutwire.Points
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
			cutwire.Points = pts

#	def __setstate__(self, state):
#		self.WireLinked = False
		
		
class ViewProviderWrapLeadingEdge(ViewProviderGeneric):

	def getIcon(self):
		return iconPath + 'WrapLeadingEdge-icon.svg'

	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		doc.removeObject(obj.Wrap.Name)
		doc.removeObject(obj.CutWire.Name)
#		obj.Wrap = None
		return True
	

class CutWire:
	
	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink","RootWire","Root", "")
		obj.addProperty("App::PropertyFloat","RootStartPoint", "Root","Start point of the root wire").RootStartPoint = 0.0
		obj.addProperty("App::PropertyFloat","RootEndPoint", "Root","End point of the root wire").RootEndPoint = 0.0
		obj.addProperty("App::PropertyLink","LeftCutRoot","Root","", 1)
		obj.addProperty("App::PropertyLink","RightCutRoot","Root","", 1)
		obj.addProperty("App::PropertyLink","TipWire","Tip","")
		obj.addProperty("App::PropertyFloat","TipStartPoint", "Tip","Digit point of the root wire").TipStartPoint = 0.0
		obj.addProperty("App::PropertyFloat","TipEndPoint", "Tip","Digit point of the root wire", 1).TipEndPoint = 0.0
		obj.addProperty("App::PropertyLink","LeftCutTip","Tip","", 1)
		obj.addProperty("App::PropertyLink","RightCutTip","Tip","", 1)
#		obj.addProperty("App::PropertyBool", "CutWire", "CutWire", "Cut the wire in two wires").CutWire = False
		self.Initialized = False
		obj.Proxy = self

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")
		
	def check(self, fp):
		if hasattr(fp, "RootWire") and hasattr(fp, "TipWire"):
			if fp.RootWire != None and fp.TipWire != None:
				if hasattr(fp, "RootStartPoint") and hasattr(fp, "RootEndPoint") and hasattr(fp, "TipStartPoint"):
					return True
		else: return False
		
		
	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if self.check(fp) and prop in ["RootWire", "RootStartPoint", "RootEndPoint", "TipWire", "TipStartPoint"]:
			if not self.Initialized:
				self.createCutWires(fp)
			else:
				self.updateCutWires(fp)

	def calculateTipEndPoint(self, fp):
		RStartPt = DiscretizedPoint(fp.RootWire, fp.RootStartPoint)
		REndPt = DiscretizedPoint(fp.RootWire, fp.RootEndPoint)
		TStartPt = DiscretizedPoint(fp.TipWire, fp.TipStartPoint)
		normVec = PtsToVec(RStartPt, REndPt).cross(PtsToVec(RStartPt, TStartPt))
		mplane = Part.makePlane(10, 10, RStartPt, normVec)
		startindex = int(fp.TipStartPoint)
		for i in range(startindex + 1, len(fp.TipWire.Points) - 1, +1):
			intersectPt = intersecLinePlane(fp.TipWire.Shape.Vertexes[i].Point, fp.TipWire.Shape.Vertexes[i + 1].Point, mplane)
			vec1 = PtsToVec(intersectPt, fp.TipWire.Shape.Vertexes[i].Point)
			vec2 = PtsToVec(intersectPt, fp.TipWire.Shape.Vertexes[i + 1].Point)
			mdot = vec1.dot(vec2)
			if mdot <= 0:
				fp.TipEndPoint = i + vec1.Length / (vec1.Length + vec2.Length) # TipEndPoint is TipWire point index i + part of edge[i]
				mplane.nullify()
				return True
		mplane.nullify()
		return False

	def createCutWires(self, fp):
		if fp.RootEndPoint > fp.RootStartPoint + 1:
			if self.calculateTipEndPoint(fp):
				leftpts, rightpts = cutWire(fp.RootWire, fp.RootStartPoint, fp.RootEndPoint)
				fp.LeftCutRoot = Draft.makeWire(leftpts, True, False)
				fp.RightCutRoot = Draft.makeWire(rightpts, True, False)
				fp.LeftCutRoot.Label = "LeftCutRoot"
				fp.RightCutRoot.Label = "RightCutRoot"
				leftpts, rightpts = cutWire(fp.TipWire, fp.TipStartPoint, fp.TipEndPoint)
				fp.LeftCutTip = Draft.makeWire(leftpts, True, False)
				fp.RightCutTip = Draft.makeWire(rightpts, True, False)
				fp.LeftCutTip.Label = "LeftCutTip"
				fp.RightCutTip.Label = "RightCutTip"
				self.Initialized = True

	def updateCutWires(self, fp):
		if fp.RootEndPoint > fp.RootStartPoint + 1:
			if self.calculateTipEndPoint(fp):
				leftpts, rightpts = cutWire(fp.RootWire, fp.RootStartPoint, fp.RootEndPoint)
				fp.LeftCutRoot.Points = leftpts
				fp.RightCutRoot.Points = rightpts
				leftpts, rightpts = cutWire(fp.TipWire, fp.TipStartPoint, fp.TipEndPoint)
				fp.LeftCutTip.Points = leftpts
				fp.RightCutTip.Points = rightpts
				

class ViewProviderCutWire(ViewProviderGeneric):
	
	def getIcon(self):
		return iconPath + 'LeadingEdge-icon.svg'

	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		doc.removeObject(obj.LeftCutRoot.Name)
		doc.removeObject(obj.RightCutRoot.Name)
		doc.removeObject(obj.LeftCutTip.Name)
		doc.removeObject(obj.RightCutTip.Name)
		return True


def createWing():
	msgCsl("createWing method starting...")
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Wing")  #FeaturePython
	Wing(obj)
	ViewProviderWing(obj.ViewObject,  "Aile-icon.svg")
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
	ViewProviderCoordSys(obj.ViewObject, "WF_Axes.svg")
	if len(sel) > 0:
		pobj = sel[0].Object
		if pobj.TypeId in ["Part::Box", "Part::Extrusion", "Part::Cylinder", "PartDesign::Pad"]:
			obj.LinkedObject = pobj
	
def createRod():
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Rod")
	Rod(obj)
	ViewProviderRod(obj.ViewObject, "Rod-icon.svg")

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
			wobj1, wobj2 = sel[:2]
			if wobj2.Object.Proxy.__class__.__name__ == "CoordSys":
				obj.CoordSystem = wobj2.Object
			elif wobj1.TypeName == wobj2.TypeName == "Part::Part2DObjectPython":
				if len(sel) > 2:
					wobj = sel[2].Object
					if wobj.Proxy.__class__.__name__ == "CoordSys":
						obj.CoordSystem = wobj
				obj.RootWire = wobj1.Object
				obj.TipWire = wobj2.Object
				FreeCAD.ActiveDocument.recompute()
				obj.RootPoint = 1
				obj.TipPoint = 1
	return obj

def createWrapLeadingEdge():
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "WrapLeadingEdge")
	WrapLeadingEdge(obj)
	ViewProviderWrapLeadingEdge(obj.ViewObject, "WrapLeadingEdge-icon.svg")
	obj.StartPoint = 1.0
	obj.EndPoint = 2.0
	if len(sel) > 0:
		wobj = sel[0].Object
		if wobj.Proxy.__class__.__name__ == "Profile":
			msgCsl("Wing type found in selection for linking WrapLeadingEdge")
			obj.Wire = wobj.Wire
#			obj.Proxy.createWrap(obj, obj.RootWire, obj.RootStartPoint, obj.RootLength, "Root")
#			obj.Proxy.createWrap(obj, obj.TipWire, obj.TipStartPoint, obj.TipLength, "Tip")
		return obj
	else:
		userMsg("No selection or selection is not a wing object")

def createProfile():
	msgCsl("createProfile method starting...")
	a = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Profile")
	Profile(a)
	ViewProviderProfile(a.ViewObject, 'Profile-icon.svg')
	a.Scale = 300

def createCutWire():
	msgCsl("createCutWire method starting...")
	sel = FreeCADGui.Selection.getSelectionEx()
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","LeadingEdge")
	CutWire(obj)
	ViewProviderCutWire(obj.ViewObject, 'LeadingEdge-icon.svg')
	if len(sel) > 1:
		wobj1 = sel[0].Object
		wobj2 = sel[1].Object
		if wobj1.TypeId == wobj2.TypeId == "Part::Part2DObjectPython":
			obj.RootWire = wobj1
			obj.TipWire = wobj2
	
