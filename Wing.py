# -*- coding: utf-8 -*-
###################################################################################
#
#  Wing.py
#  
#  Copyright 2018 Matthieu Carron
#  this file is based on the code and the ideas
#  of the macro AIRFOIL IMPORT & SCALE v2.1 and other modules like 
# 		Animation module of microelly
#		WorkFeature, Assembly2
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

import os, sys
sys.path.append("/usr/lib/freecad/lib/")
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
		# delete last point if it's the same as first one
		if points[0].sub(points[len(points)-1]).Length <= 1.e-14: points.remove([len(points)-1])
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
		obj.CenterType = "Vertexes"
		obj.Direction = "Edge"
		obj.Proxy = self

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")

	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop == "LinkedObject":
#			msgCsl("CoordSys class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
			if hasattr(fp, "LinkedObject") and hasattr(self, "pName"):
				if fp.LinkedObject != None:
					if self.pName != fp.LinkedObject.Name:
						self.pName = fp.LinkedObject.Name
						self.updatePlacement(fp)
				else:
					self.pName = ""
		if prop in ["CenterType","VertexNum", "Normal", "Direction", "Angle"]:
#			msgCsl("CoordSys class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
			self.updatePlacement(fp)

	def updateRefFace(self, fp):
		ObjectOk = False
		if fp.LinkedObject.TypeId == "Part::Extrusion":
			nb = len(fp.LinkedObject.Base.Shape.Edges)
			mface = fp.LinkedObject.Shape.Faces[nb]
			ObjectEdges = mface.Edges
			ObjectCenterOfMass = mface.CenterOfMass
			ObjectOrigin = fp.LinkedObject.Shape.Vertex1.Point
			ObjectOk = True
		elif fp.LinkedObject.TypeId == "PartDesign::Pad":
			nb = len(fp.LinkedObject.OutList[0].Shape.Edges)
			mface = fp.LinkedObject.Shape.Faces[nb]
#			ObjectEdges = fp.LinkedObject.OutList[0].Shape.Edges
#			ObjectCenterOfMass = fp.LinkedObject.OutList[0].Shape.CenterOfMass
			ObjectEdges = mface.Edges
			ObjectCenterOfMass = mface.CenterOfMass
			ObjectOrigin = fp.LinkedObject.OutList[0].AttachmentOffset.Base
			ObjectOk = True
		elif fp.LinkedObject.TypeId == "Part::Cylinder":
			ObjectEdges = fp.LinkedObject.Shape.Face3.Edges
			ObjectCenterOfMass = fp.LinkedObject.Shape.Face3.CenterOfMass
			ObjectOrigin = ObjectCenterOfMass
			ObjectOk = True
		elif fp.LinkedObject.TypeId == "Part::Box":
			ObjectEdges = fp.LinkedObject.Shape.Face5.Edges
			ObjectCenterOfMass = fp.LinkedObject.Shape.Face5.CenterOfMass
			ObjectOrigin = fp.LinkedObject.Shape.Vertex2.Point
			ObjectOk = True
		return ObjectOk, ObjectEdges, ObjectCenterOfMass, ObjectOrigin

	def updatePlacement(self, fp):
		if hasattr(fp, "LinkedObject"):
			if fp.LinkedObject != None and hasattr(fp.LinkedObject.Shape, "Face1"):
				ObjectOk, ObjectEdges, ObjectCenterOfMass, ObjectOrigin = self.updateRefFace(fp)
				if ObjectOk:
					index = int(fp.VertexNum % len(ObjectEdges))  # % len(ObjectEdges) to avoid error if VertexNum is set to high
					if fp.LinkedObject.TypeId == "PartDesign::Pad":
						fp.LinkedObject.OutList[0].AttachmentOffset = fp.Tangent.Placement
					else:
						fp.LinkedObject.Placement = fp.Tangent.Placement
					FreeCAD.ActiveDocument.recompute()
					ObjectOk, ObjectEdges, ObjectCenterOfMass, ObjectOrigin = self.updateRefFace(fp)
					Fract = int((round((round(fp.VertexNum,2) - int(fp.VertexNum)), 2) * 100 + 100)) % 100
					msgCsl("ObjectOrigin : "+ format(ObjectOrigin))
					mEdge = ObjectEdges[index]
					longueur = mEdge.LastParameter - mEdge.FirstParameter
					if mEdge.Orientation == "Reversed": Fract = 100 - Fract #;msgCsl("reverse fract")
					Pt = mEdge.Curve.value(longueur * (100 - Fract) / 100) #mEdge.discretize(101)
					msgCsl("Pt: " + format(Pt))
					if fp.CenterType == "MassCenter":
						NewOrigin = ObjectCenterOfMass
						mBend = PtsToVec(NewOrigin,Pt)
					else:
						NewOrigin = Pt
						mBend = PtsToVec(NewOrigin, ObjectCenterOfMass)
					msgCsl("NewOrigin " + format(NewOrigin))
					mTrans = PtsToVec(NewOrigin,ObjectOrigin)
					msgCsl("mTrans " + format(mTrans))
					if fp.CenterType == "Vertexes" and fp.Direction == "Edge":
						vectan = mEdge.Curve.tangent(longueur * (100 - Fract) / 100)[0] #PtsToVec(self.ObjectEdges[int(fp.VertexNum)].Start, self.ObjectEdges[int(fp.VertexNum)].End)
						if mEdge.Orientation == "Forward": vectan.multiply(-1)
						mRot = Rotation(vectan, fp.Tangent.End.sub(fp.Tangent.Start))
					else:
						mRot = Rotation(mBend,fp.Bend.End.sub(fp.Bend.Start))
					mPlacement2 = FreeCAD.Placement(mTrans,mRot,NewOrigin)
					fp.LocalPlacement = mPlacement2
					# Add rotation angle from CoordSys property
					mPlacement2 = Placement(VecNul, Rotation(fp.Normal.End.sub(fp.Normal.Start), fp.Angle), fp.Tangent.Start)
					fp.LocalPlacement = mPlacement2.multiply(fp.LocalPlacement)
					if fp.LinkedObject.TypeId == "PartDesign::Pad":
						fp.LinkedObject.OutList[0].AttachmentOffset = fp.LocalPlacement.multiply(fp.LinkedObject.OutList[0].AttachmentOffset)
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
		self.VecRoot = [0, 0, 0] #VecNul
		self.VecRootTangent = [0, 0, 0] #VecNul
		self.VecRootCurvature = [0, 0, 0] #VecNul
		self.VecTip = [0, 0, 0] #VecNul
		self.VecTipTangent = [0, 0, 0] #VecNul
		self.VecTipCurvature = [0, 0, 0] #VecNul
		self.VecDirRod = [0, 0, 0] #VecNul
#		self.VecRodEdge = VecNul
		self.VecRodCenter = [0, 0, 0] #VecNul
		self.ObjNameList = {"RootWire":"", "TipWire":"", "CoordSystem":""}
		obj.TangentType = "Next"
		obj.Proxy = self

	def check(self, fp):
		test = {"Root" : False, "All" : False}
		if hasattr(fp, "RootWire") and hasattr(fp, "CoordSystem"):
			if fp.RootWire != None and fp.CoordSystem != None:
				if hasattr(fp.RootWire, 'Shape') and hasattr(fp, "RootPoint"):
					if len(fp.RootWire.Shape.Edges) > 0: test["Root"] = True
					if hasattr(fp, "TipWire"):
						if fp.TipWire != None :
							if hasattr(fp.TipWire, 'Shape') and hasattr(fp, "TipPoint"):
								if len(fp.TipWire.Shape.Edges) > 0: test["All"] = True
		return test

	def onChanged(self, fp, prop):
		# Do something when a property has changed
			if prop in ["RootPoint", "TipPoint", "RootOffset", "TipOffset", "RootInwardOffset",
						"TipInwardOffset", "AutoRotate", "TangentType", "AngleOffset"]:
#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
#				self.calcVecRoot(fp)
				if self.check(fp)["Root"]: self.updatePosition(fp)
			if fp.getTypeIdOfProperty(prop) == 'App::PropertyLink':
				obj = fp.getPropertyByName(prop)
				if hasattr(obj, "Name") and hasattr(self, "ObjNameList"):
					if obj.Name != self.ObjNameList[prop]:
						self.ObjNameList[prop] = obj.Name
						if prop in ["RootWire", "TipWire", "CoordSystem"]:
#							msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
#								self.calcVecRoot(fp)
							if self.check(fp)["Root"]: self.updatePosition(fp)

#	def __getstate__(self):
#		state = {}
#		state["VecRoot"] = list(self.VecRoot)
#		state["VecRootTangent"] = list(self.VecRootTangent)
#		state["VecRootCurvature"] = list(self.VecRootCurvature)
#		state["VecTip"] = list(self.VecTip)
#		state["VecTipTangent"] = list(self.VecTipTangent)
#		state["VecTipCurvature"] = list(self.VecTipCurvature)
#		state["VecDirRod"] = list(self.VecDirRod)
##		state["VecRodEdge"] = list(self.VecRodEdge)
#		state["VecRodCenter"] = list(self.VecRodCenter)
#		return state
#
#	def __setstate__(self, state):
#		self.VecRoot = Vector(tuple( i for i in state["VecRoot"]))
#		self.VecRootTangent = Vector(tuple( i for i in state["VecRootTangent"]))
#		self.VecRootCurvature = Vector(tuple( i for i in state["VecRootCurvature"]))
#		self.VecTip = Vector(tuple( i for i in state["VecTip"]))
#		self.VecTipTangent = Vector(tuple( i for i in state["VecTipTangent"]))
#		self.VecTipCurvature = Vector(tuple( i for i in state["VecTipCurvature"]))
#		self.VecDirRod = Vector(tuple( i for i in state["VecDirRod"]))
##		self.VecRodEdge = Vector(tuple( i for i in state["VecRodEdge"]))
#		self.VecRodCenter = Vector(tuple( i for i in state["VecRodCenter"]))
#		self.ObjNameList = {"RootWire":"", "TipWire":"", "CoordSystem":""}

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")
	
	def calcVecRoot(self, fp):
#		msgCsl("int(fp.RootPoint) "+ str(int(fp.RootPoint)))
#		msgCsl("nb fp.RootWire.Shape.Edges: " + str(len(fp.RootWire.Shape.Edges)))
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
		VecRootTangent = tangentVec(fp.RootWire, int(fp.RootPoint), fp.TangentType)
		VecRootNormal = normalVec(fp.RootWire, int(fp.RootPoint))
		VecRootCurvature = VecRootTangent.cross(VecRootNormal)
#			msgCsl("VecRootNormal "+ format(VecRootNormal))
		VecRootCurvature.normalize()
		if fp.RootInwardOffset != 0:
			VecRoot = Pt.add(VecRootCurvature.multiply(fp.RootInwardOffset))
			VecRootCurvature.normalize()
		else:
			VecRoot = Pt
#		msgCsl("VecRoot "+ format(VecRoot))
		self.VecRoot = setVec(VecRoot)
		self.VecRootTangent = setVec(VecRootTangent)
		self.VecRootCurvature = setVec(VecRootCurvature)
		if not self.check(fp)["All"]:
			VecDirRod = VecRootNormal.multiply(-1)
			self.VecDirRod = setVec(VecDirRod)
			self.VecTipTangent = setVec(VecNul)
		else:
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
		VecTipTangent = tangentVec(fp.TipWire, int(fp.TipPoint), fp.TangentType)
		VecTipNormal = normalVec(fp.TipWire, int(fp.TipPoint))
		VecTipCurvature = VecTipTangent.cross(VecTipNormal)
#		msgCsl("VecTipNormal "+ format(VecTipNormal))
		VecTipCurvature.normalize()
		if fp.TipInwardOffset != 0:
			VecTip = Pt.add(VecTipCurvature.multiply(fp.TipInwardOffset))
			VecTipCurvature.normalize()
		else:
			VecTip = Pt
#		msgCsl("VecTip "+ format(VecTip))
		self.VecTip = setVec(VecTip)
		self.VecTipTangent = setVec(VecTipTangent)
		self.VecTipCurvature = setVec(VecTipCurvature)
		self.calcVecDirRod(fp)

	def calcVecDirRod(self, fp):
		self.VecDirRod = setVec(getVec(self.VecTip).sub(getVec(self.VecRoot)))
#		msgCsl("VecDirRod "+ format(self.VecDirRod))

	def calcVecRod(self, fp):
#		if self.testWires(fp):
			self.VecRodCenter = setVec(fp.CoordSystem.Tangent.Start)
#			self.VecRodEdge = PtsToVec(fp.CoordSystem.Tangent.Start,fp.CoordSystem.Tangent.End)

	def updateRootPosition(self, fp):
		mDir = getVec(self.VecDirRod)
		if mDir != VecNul:
			mDir = FreeCAD.Vector(mDir.x, mDir.y, mDir.z)
			mDir.normalize()
			mDir.multiply(-fp.RootOffset)
			self.calcVecRod(fp)
			mDir = mDir.sub(PtsToVec(getVec(self.VecRoot),getVec(self.VecRodCenter)))
			mPlacement = Placement(mDir,Rotation())
			mPlacement = mPlacement.multiply(fp.CoordSystem.Tangent.Placement)
			mPlacement = Placement(VecNul, Rotation(mDir, fp.AngleOffset), DiscretizedPoint(fp.RootWire, fp.RootPoint)).multiply(mPlacement)
			self.updateAxis(fp.CoordSystem, mPlacement)
			self.updateLength(fp)

	def updateLength(self, fp):
		if self.check(fp)["All"]:
			if fp.CoordSystem.LinkedObject.TypeId in ["Part::Box","Part::Cylinder"]:
				fp.CoordSystem.LinkedObject.Height = getVec(self.VecDirRod).Length + float(fp.RootOffset) + float(fp.TipOffset)
#				msgCsl("indice VecDirRod: " + str(self.VecList["VecDirRod"]) + " vector VecDirRod: " + format(fp.VectorList[self.VecList["VecDirRod"]]))
			if fp.CoordSystem.LinkedObject.TypeId == "PartDesign::Pad":
				fp.CoordSystem.LinkedObject.Length = getVec(self.VecDirRod).Length + float(fp.RootOffset) + float(fp.TipOffset)
			if fp.CoordSystem.LinkedObject.TypeId == "Part::Extrusion":
				fp.CoordSystem.LinkedObject.LengthFwd = getVec(self.VecDirRod).Length + float(fp.RootOffset) + float(fp.TipOffset)

	def updateAxis(self, obj, placmnt):
		obj.Tangent.Placement = placmnt
		obj.Bend.Placement = placmnt
		obj.Normal.Placement = placmnt
		obj.Proxy.updatePlacement(obj)

	def updatePosition(self,fp):
		self.calcVecRoot(fp)
		if self.check(fp)["All"]:
			self.calcVecTip(fp)
		VecRoot = getVec(self.VecRoot)
		VecDirRod = getVec(self.VecDirRod)
		mRot = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), VecDirRod)
#			msgCsl("VecRoot "+ format(VecRoot))
		mPlacementAlign = Placement()
		mPlacementAlign.move(VecRoot)
		mPlacementAlign = FreeCAD.Placement(VecNul, mRot, VecRoot).multiply(mPlacementAlign)
#			msgCsl("mPlacementAlign "+ format(mPlacementAlign))
		self.updateAxis(fp.CoordSystem, mPlacementAlign)
		if fp.AutoRotate and getVec(self.VecRootTangent) != VecNul:
			VecRootTangent = getVec(self.VecRootTangent)
			VecTipTangent = getVec(self.VecTipTangent)
			VecBisector = VecRootTangent.add(VecTipTangent).normalize()  # Vector mean of root and tip tangents
#				msgCsl("VecBisector "+ format(VecBisector))
			VecBisector.projectToPlane(VecNul,VecDirRod)  # projection in the normal plan of rod axis
#			msgCsl("VecBisector "+ format(VecBisector))
#			msgCsl("VecRootTangent "+ format(VecRootTangent))
#			msgCsl("VecTipTangent "+ format(VecTipTangent))
			mRot = FreeCAD.Rotation(fp.CoordSystem.Tangent.End.sub(fp.CoordSystem.Tangent.Start), VecBisector)
#				msgCsl("Rotation "+ format(mRot))
			mPlacement = FreeCAD.Placement(VecNul, mRot, VecRoot)
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
		obj.addProperty("App::PropertyBool", "Inward", "Settings", "Draw the wrap inward or backward").Inward = True
#		obj.addProperty("App::PropertyBool", "DeleteLoop", "Settings", "Delete loop of wrap and cut wires").DeleteLoop = False
		self.WireLinked = False
		obj.Proxy = self

	def onChanged(self, fp, prop):
		# Do something when a property has changed
		if hasattr(fp, "Wire"):
			if fp.Wire != None:
				if prop in ["StartPoint", "EndPoint", "Thickness", "Inward"]:
					if self.WireLinked:
						self.updateWrap(fp, fp.Wire, fp.StartPoint, fp.EndPoint)
						if fp.Inward: self.updateCutWire(fp.Wire, fp.Wrap, fp.CutWire, fp.StartPoint, fp.EndPoint)
#						if fp.DeleteLoop: DeleteLoop(fp.CutWire)
				if prop == "Wire":
					if not self.WireLinked:
						self.createWrap(fp, fp.Wire, fp.StartPoint, fp.EndPoint)
						self.WireLinked = True
					elif hasattr(fp, "Wrap"):
						self.updateWrap(fp, fp.Wire, fp.StartPoint, fp.EndPoint)
						if fp.Inward: self.updateCutWire(fp.Wire, fp.Wrap, fp.CutWire, fp.StartPoint, fp.EndPoint)
#						if fp.DeleteLoop: DeleteLoop(fp.CutWire)

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")

	def calculateWrapPoints(self, fp, wire, start, end):
		pts = []
		if wire != None and int(end) > int(start):
			sens = 1 if fp.Inward else -1
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
				vecdec.multiply(sens * fp.Thickness)
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
#			if fp.DeleteLoop: DeleteLoop(wrapobj)
			fp.Wrap = wrapobj
			if fp.Inward:
				msgCsl("create cut wire")
				pts2 = self.calculateCutWirePoints(wire, wrapobj, start, end)
				cutobj = Draft.makeWire(pts2, True, False)
				cutobj.Label = "CutWire"
#				if fp.DeleteLoop: DeleteLoop(cutobj)
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
#			if fp.DeleteLoop: DeleteLoop(fp.Wrap)

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
		if obj.Wrap != None: doc.removeObject(obj.Wrap.Name)
		if obj.CutWire != None: doc.removeObject(obj.CutWire.Name)
		return True
	

class LeadingEdge:
	
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
		obj.addProperty("App::PropertyLink","Plane","CutPlane","", 1)
		obj.addProperty("App::PropertyEnumeration", "CutType", "CutPlane", "Define wire to be created").CutType = ["Left", "Right", "Both"]
		self.Initialized = {"Left" : False, "Right" : False}
		obj.CutType = "Right"
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
		if self.check(fp) and prop in ["RootWire", "RootStartPoint", "RootEndPoint", "TipWire", "TipStartPoint", "CutType"]:
			create = False
			for mkey, mvalue in self.Initialized.items():
				if not mvalue and (fp.CutType == "Both" or mkey == fp.CutType): create = True
			if create: self.createCutWires(fp)
			else: self.updateCutWires(fp)
			self.deleteWires(fp)

	def updatePlane(self, fp):
		RStartPt = DiscretizedPoint(fp.RootWire, fp.RootStartPoint)
		REndPt = DiscretizedPoint(fp.RootWire, fp.RootEndPoint)
		TStartPt = DiscretizedPoint(fp.TipWire, fp.TipStartPoint)
		vec1 = PtsToVec(RStartPt, REndPt)
		vec2 = PtsToVec(RStartPt, TStartPt)
		normVec = vec2.cross(vec1)
		if fp.Plane == None:
#			mplane = Part.makePlane(vec1.Length + 10, vec2.Length + 10, RStartPt, normVec)
			mplane = FreeCAD.ActiveDocument.addObject("Part::Plane","Plane")
			mplane.ViewObject.ShapeColor = (0.33,0.67,1.00)
			mplane.ViewObject.LineColor = (1.00,0.67,0.00)
			mplane.ViewObject.LineWidth = 3.00
			mplane.ViewObject.Transparency = 50
		else:
			mplane = fp.Plane
		mplane.Length = vec1.Length + 10
		mplane.Width = vec2.Length + 10
		mrot = Rotation(Vector(0, 1, 0), vec2)
		mplane.Placement = Placement(VecNul, mrot)
		mrot = Rotation(mplane.Shape.normalAt(0, 0).multiply(-1), normVec)
		mplane.Placement = Placement(RStartPt.add(vec1.multiply(-5 / vec1.Length)), mrot).multiply(mplane.Placement)
		mplane.Placement.move(vec2.multiply(-5 / vec2.Length))
		fp.Plane = mplane

	def calculateTipEndPoint(self, fp):
		self.updatePlane(fp)
		mplane = fp.Plane
		startindex = int(fp.TipStartPoint)
		for i in range(startindex + 1, len(fp.TipWire.Points) - 1, +1):
			intersectPt = intersecLinePlane(fp.TipWire.Shape.Vertexes[i].Point, fp.TipWire.Shape.Vertexes[i + 1].Point, mplane.Shape)
			vec1 = PtsToVec(intersectPt, fp.TipWire.Shape.Vertexes[i].Point)
			vec2 = PtsToVec(intersectPt, fp.TipWire.Shape.Vertexes[i + 1].Point)
			mdot = vec1.dot(vec2)
			if mdot <= 0:  #intersection point is in edge if dot is negative (vectors are in opposite directions)
				fp.TipEndPoint = i + vec1.Length / (vec1.Length + vec2.Length) # TipEndPoint is TipWire point index i + part of edge[i]
				return True
		return False

	def createCutWires(self, fp):
		if fp.RootEndPoint > fp.RootStartPoint + 1:
			if self.calculateTipEndPoint(fp):
				type = fp.CutType
				leftpts, rightpts = cutWire(fp.RootWire, fp.RootStartPoint, fp.RootEndPoint, type)
				leftpts2, rightpts2 = cutWire(fp.TipWire, fp.TipStartPoint, fp.TipEndPoint, type)
				if type == "Right" or (type == "Both" and not self.Initialized["Right"]):
					fp.RightCutRoot = Draft.makeWire(rightpts, True, False)
					fp.RightCutRoot.Label = "RightCutRoot"
					fp.RightCutTip = Draft.makeWire(rightpts2, True, False)
					fp.RightCutTip.Label = "RightCutTip"
					self.Initialized[type] = True
				if type == "Left" or (type == "Both" and not self.Initialized["Left"]):
					fp.LeftCutRoot = Draft.makeWire(leftpts, True, False)
					fp.LeftCutRoot.Label = "LeftCutRoot"
					fp.LeftCutTip = Draft.makeWire(leftpts2, True, False)
					fp.LeftCutTip.Label = "LeftCutTip"
					self.Initialized[type] = True
				del leftpts, leftpts2, rightpts, rightpts2

	def updateCutWires(self, fp):
		if hasattr(fp.RootWire.Shape, "Edge1"):
			if fp.RootEndPoint > fp.RootStartPoint + 1:
				if self.calculateTipEndPoint(fp):
					type = fp.CutType
					leftpts, rightpts = cutWire(fp.RootWire, fp.RootStartPoint, fp.RootEndPoint, type)
					leftpts2, rightpts2 = cutWire(fp.TipWire, fp.TipStartPoint, fp.TipEndPoint, type)
					if type in ["Left", "Both"]:
						fp.LeftCutRoot.Points = leftpts
						fp.LeftCutTip.Points = leftpts2
					if type in ["Right", "Both"]:
						fp.RightCutRoot.Points = rightpts
						fp.RightCutTip.Points = rightpts2
					del leftpts, leftpts2, rightpts, rightpts2
	
	def deleteWires(self, fp):
		if fp.CutType == "Left": # and self.Initialized["Right"]:  # delete Right wires
			if fp.RightCutRoot != None: FreeCAD.ActiveDocument.removeObject(fp.RightCutRoot.Name)
			if fp.RightCutTip != None: FreeCAD.ActiveDocument.removeObject(fp.RightCutTip.Name)
			self.Initialized["Right"] = False
		if fp.CutType == "Right": # and self.Initialized["Left"]:  # delete Left wires
			if fp.LeftCutRoot != None: FreeCAD.ActiveDocument.removeObject(fp.LeftCutRoot.Name)
			if fp.LeftCutTip != None: FreeCAD.ActiveDocument.removeObject(fp.LeftCutTip.Name)
			self.Initialized["Left"] = False			

class ViewProviderLeadingEdge(ViewProviderGeneric):
	
	def getIcon(self):
		return iconPath + 'LeadingEdge-icon.svg'

	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		if obj.LeftCutRoot != None:	doc.removeObject(obj.LeftCutRoot.Name)
		if obj.RightCutRoot != None: doc.removeObject(obj.RightCutRoot.Name)
		if obj.LeftCutTip != None: doc.removeObject(obj.LeftCutTip.Name)
		if obj.RightCutTip != None:	doc.removeObject(obj.RightCutTip.Name)
		if obj.Plane != None: doc.removeObject(obj.Plane.Name)
		return True


class CutWire:
	
	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink","Wire","Wire", "")
		obj.addProperty("App::PropertyFloat","StartPoint", "Wire","Start point of the root wire").StartPoint = 0.0
		obj.addProperty("App::PropertyFloat","EndPoint", "Wire","End point of the root wire").EndPoint = 0.0
		obj.addProperty("App::PropertyLink","StartPointObj","Wire","", -1)
		obj.addProperty("App::PropertyLink","EndPointObj","Wire","", -1)
		obj.addProperty("App::PropertyLink","LeftCut","Wire","", 1)
		obj.addProperty("App::PropertyLink","RightCut","Wire","", 1)
		obj.addProperty("App::PropertyEnumeration", "CutType", "CutPlane", "Define wire to be created").CutType = ["Left", "Right", "Both"]
		self.Initialized = {"Left" : False, "Right" : False}
		obj.CutType = "Right"
		obj.Proxy = self

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")
		
	def check(self, fp):
		if hasattr(fp, "Wire"):
			if fp.Wire != None:
				if hasattr(fp, "StartPoint") and hasattr(fp, "EndPoint"):
					return True
		else: return False
		
	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop in ["Wire", "StartPoint", "EndPoint", "CutType"]:
			if self.check(fp):
				msgCsl("CutWire onChanged check&prop = true prop= " + str(prop))
				create = False
				for mkey, mvalue in self.Initialized.items():
					if (mkey == fp.CutType) or (fp.CutType == "Both"):
#						msgCsl("onChanged in if mkey, mkey= " + mkey + " fp.CutType= " + fp.CutType)
#						msgCsl("mvalue= " + str(mvalue))
						if not mvalue: create = True
				if create: self.createCutWires(fp)
				else: self.updateCutWires(fp)
				self.deleteWires(fp)

	def createCutWires(self, fp):
		if fp.EndPoint > fp.StartPoint + 1:
			type = fp.CutType
			leftpts, rightpts = cutWire(fp.Wire, fp.StartPoint, fp.EndPoint, type)
			if not self.Initialized["Right"]: #((type == "Right") or (type == "Both")) and (
				msgCsl("createCutWires if right ok")
				fp.RightCut = Draft.makeWire(rightpts, True, False)
				msgCsl("createCutWires right makeWire")
				fp.RightCut.Label = "RightCut"
				msgCsl("createCutWires right label change")
				self.Initialized["Right"] = True
			if not self.Initialized["Left"]: #((type == "Left") or (type == "Both")) and (
				msgCsl("Create left CutWire")
				fp.LeftCut = Draft.makeWire(leftpts, True, False)
				fp.LeftCut.Label = "LeftCut"
				self.Initialized["Left"] = True
			del leftpts, rightpts
			if fp.StartPointObj == None:
#				msgCsl("createCutWires before start makePoint")
				fp.StartPointObj = Draft.makePoint(DiscretizedPoint(fp.Wire, fp.StartPoint))
#				msgCsl("createCutWires after start makePoint")
				fp.StartPointObj.Label = "StartPoint"
				fp.StartPointObj.ViewObject.PointColor = (1.00,0.67,0.00, 0.0)
				fp.StartPointObj.ViewObject.PointSize = 7.0
			if fp.EndPointObj == None:
				fp.EndPointObj = Draft.makePoint(DiscretizedPoint(fp.Wire, fp.EndPoint))
				fp.EndPointObj.Label = "EndPoint"
				fp.EndPointObj.ViewObject.PointColor = (1.00,0.67,0.00, 0.0)
				fp.EndPointObj.ViewObject.PointSize = 7.0

	def updateCutWires(self, fp):
		if hasattr(fp.Wire.Shape, "Edge1"):
			if fp.EndPoint > fp.StartPoint + 1:
				type = fp.CutType
				leftpts, rightpts = cutWire(fp.Wire, fp.StartPoint, fp.EndPoint, type)
				if type in ["Left", "Both"]:
					fp.LeftCut.Points = leftpts
				if type in ["Right", "Both"]:
					fp.RightCut.Points = rightpts
				del leftpts, rightpts
				setPointCoord(fp.StartPointObj, DiscretizedPoint(fp.Wire, fp.StartPoint))
				setPointCoord(fp.EndPointObj, DiscretizedPoint(fp.Wire, fp.EndPoint))
	
	def deleteWires(self, fp):
#		msgCsl("deleteWires starting...")
		if fp.CutType == "Left": # and self.Initialized["Right"]:  # delete Right wires
			if fp.RightCut != None:
				FreeCAD.ActiveDocument.removeObject(fp.RightCut.Name)
				self.Initialized["Right"] = False
		if fp.CutType == "Right": # and self.Initialized["Left"]:  # delete Left wires
			if fp.LeftCut != None:
				FreeCAD.ActiveDocument.removeObject(fp.LeftCut.Name)
				self.Initialized["Left"] = False			

class ViewProviderCutWire(ViewProviderGeneric):
	
	def getIcon(self):
		return iconPath + 'CutWire-icon.svg'

	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		if obj.LeftCut != None:	doc.removeObject(obj.LeftCut.Name)
		if obj.RightCut != None: doc.removeObject(obj.RightCut.Name)
		if obj.StartPointObj != None: doc.removeObject(obj.StartPointObj.Name)
		if obj.EndPointObj != None: doc.removeObject(obj.EndPointObj.Name)
		return True


class Section:

	def __init__(self, obj):
		msgCsl("class " + self.__class__.__name__ + ", __init__")
		obj.addProperty("App::PropertyLink", "SlicedObject", "Section", "Sliced object")
		obj.addProperty("App::PropertyFloat", "Offset", "Settings", "Distance from the object origin").Offset = 0.001
		obj.addProperty("App::PropertyEnumeration", "RefPlane", "Settings", "Reference plane of the section").RefPlane = ["XY", "XZ", "YZ"]
		obj.addProperty("App::PropertyLink", "CutPlane", "Section", "Plane of the section", 1)
		obj.addProperty("App::PropertyLink", "Section", "Section", "Section's wire", 1)
		obj.addProperty("App::PropertyVector", "planeToX", "CalculatedParam", "", 1).planeToX = VecNul
		obj.addProperty("App::PropertyVector", "planeToNormal", "CalculatedParam", "", 1).planeToNormal = VecNul
		obj.addProperty("App::PropertyPlacement", "planePlacement", "CalculatedParam", "", 1)
		obj.RefPlane = "XY"
		self.bboxLength = 0.0
		self.bboxOrigin = 0.0
		self.external = False
		obj.Proxy = self

	def execute(self, fp):
		msgCsl("class " + self.__class__.__name__ + ", execute")
		
	def check(self, fp):
		msgCsl("check method starting")
		if hasattr(fp, "SlicedObject") and hasattr(fp, "planeToX") and hasattr(fp, "planeToNormal") and hasattr(fp, "planePlacement"):
			if fp.SlicedObject != None:
#				if hasattr(fp.SlicedObject, "Shape"):
#					if hasattr(fp.SlicedObject.Shape, "Volume"):
#						if fp.SlicedObject.Shape.Volume > 0.001:
				return True
#						else:
#							msgCsl("Shape volume is under 0.001, slice abort")
		else: return False
		
	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		msgCsl(self.__class__.__name__ + " class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop == "Offset":
			if self.check(fp):
				if fp.CutPlane == None: self.createSection(fp)
				else: self.updateSection(fp)
		if prop == "SlicedObject":
			if self.check(fp):
				if fp.CutPlane == None: self.createSection(fp)
				else:
					self.external = True
					self.CalculateParam(fp)
					self.external = False
					self.updateSection(fp)
		if prop == "RefPlane":
			if self.check(fp):
				if fp.CutPlane == None:
					msgCsl("Section plane not created")
					return
				self.external = True
				self.CalculateParam(fp)
				self.external = False
				self.updateSection(fp)

	def CalculateParam(self, fp):
		msgCsl("CalculateParam method starting")
		bbox = fp.SlicedObject.Shape.BoundBox
		pos = Vector(bbox.XMin, bbox.YMin, bbox.ZMin)
		vecX = PtsToVec(pos, Vector(bbox.XMax, bbox.YMin, bbox.ZMin))
		vecY = PtsToVec(pos, Vector(bbox.XMin, bbox.YMax, bbox.ZMin))
		vecZ = PtsToVec(pos, Vector(bbox.XMin, bbox.YMin, bbox.ZMax))
		i = 1
		if fp.RefPlane == "XY":
			msgCsl("refplane XY checked")
			self.bboxLength = bbox.ZLength
			self.bboxOrigin = bbox.ZMin
			fp.planeToX = vecX
			fp.planeToNormal = vecZ
			length = bbox.XLength
			width = bbox.YLength
		elif fp.RefPlane == "XZ":
			msgCsl("refplane XZ checked")
			self.bboxLength = bbox.YLength
			self.bboxOrigin = bbox.YMin
			fp.planeToX = vecX
			fp.planeToNormal = vecY
			length = bbox.XLength
			width = bbox.ZLength
			i = -1
		elif fp.RefPlane == "YZ":
			msgCsl("refplane YZ checked")
			self.bboxLength = bbox.XLength
			self.bboxOrigin = bbox.XMin
			fp.planeToX = vecY
			fp.planeToNormal = vecX
			length = bbox.YLength
			width = bbox.ZLength
		if length * width == 0: return 0, 0
		mrot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), fp.planeToX)
		mplacement = FreeCAD.Placement(VecNul, mrot)
		mrot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, i * 1), fp.planeToNormal)
		mplacement = FreeCAD.Placement(pos, mrot).multiply(mplacement)
		fp.planePlacement = mplacement
		if self.external:
			mplane = fp.CutPlane
			mplane.Length = length
			mplane.Width = width
			mplane.Placement = fp.planePlacement
			fp.CutPlane = mplane
			self.updatePlane(fp, fp.Offset)
		return length, width
	
	def createPlane(self, fp, length, width):
		msgCsl("createPlane method starting")
		if fp.CutPlane == None:
			mplane = FreeCAD.ActiveDocument.addObject("Part::Plane","Plane")
			mplane.ViewObject.ShapeColor = (0.33,0.67,1.00)
			mplane.ViewObject.LineColor = (1.00,0.67,0.00)
			mplane.ViewObject.LineWidth = 1.00
			mplane.ViewObject.Transparency = 50
#			bbox = fp.SlicedObject.Shape.BoundBox
#			pos = Vector(bbox.XMin, bbox.YMin, bbox.ZMin)
			fp.planeToNormal.normalize()
			mplane.Length = length
			mplane.Width = width
#			mrot = Rotation(Vector(1, 0, 0), fp.planeToX)
#			mplane.Placement = Placement(VecNul, mrot)
#			mrot = Rotation(Vector(0, 0, 1), fp.planeToNormal)
			mplane.Placement = fp.planePlacement #Placement(pos, mrot).multiply(mplane.Placement)
			dist = fp.Offset
			if dist != 0:
				if dist >= self.bboxLength: dist = self.bboxLength
				mplane.Placement.move(fp.planeToNormal.multiply(dist))
			fp.CutPlane = mplane

	def updatePlane(self, fp, dist):
		if hasattr(fp, "planePlacement"):
			msgCsl("updatePlane method starting")
			mplane = fp.CutPlane
			if dist != 0:
				if dist >= self.bboxLength: dist = self.bboxLength
				mplane.Placement = fp.planePlacement
				fp.planeToNormal.normalize()
	#			msgCsl("Plane normal vector: " + format(fp.planeToNormal) + " plane offset: " + str(dist))
				mplane.Placement.move(fp.planeToNormal.multiply(dist))
			fp.CutPlane = mplane

	def createSection(self, fp):
		msgCsl("createSection method starting")
		length, width = self.CalculateParam(fp)
		if length * width == 0: return
		self.createPlane(fp, length, width)
		slice = Part.Compound(fp.SlicedObject.Shape.slice(fp.planeToNormal.normalize(), self.bboxOrigin + fp.Offset))
#		msgCsl("normVec: " + format(normVec))
		pts = []
		for e in slice.Edges:
			if e.Orientation == "Reversed":
				pts.append(e.firstVertex().Point)
			else:
				pts.append(e.lastVertex().Point)
		fp.Section = Draft.makeWire(pts, True, False)
		fp.Section.Label = "CutWire"
		del slice		
	
	def updateSection(self, fp):
		msgCsl("updateSection method starting")
		msgCsl("updateSection method starting")
		# in case of freecad file is loading, check plane is build
		self.updatePlane(fp, fp.Offset)
		if len(fp.CutPlane.Shape.Edges) == 0: return
		slice = Part.Compound(fp.SlicedObject.Shape.slice(fp.planeToNormal.normalize(), self.bboxOrigin + fp.Offset))
		pts = []
#		msgCsl("slice.Edges number: " + str(len(slice.Edges)))
		for e in slice.Edges:
			if e.Orientation == "Reversed":
				pts.append(e.firstVertex().Point)
			else:
				pts.append(e.lastVertex().Point)
		fp.Section.Points = pts
		del slice		


class ViewProviderSection(ViewProviderGeneric):
	
	def getIcon(self):
		return iconPath + 'Section.svg'

	def onDelete(self, viewObject, subelements):  # subelements is a tuple of strings
		obj = viewObject.Object
		doc = FreeCAD.ActiveDocument
		if obj.Section != None:	doc.removeObject(obj.Section.Name)
		if obj.CutPlane != None: doc.removeObject(obj.CutPlane.Name)
		return True


def createWing():
	msgCsl("createWing method starting...")
	sl = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sl)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Wing")  #FeaturePython
	Wing(obj)
	ViewProviderWing(obj.ViewObject,  "Aile-icon.svg")
	if len(sl) > 0:
		wobj = sl[0].Object
#		msgCsl(wobj.Proxy.__class__.__name__)
		if wobj.Proxy.__class__.__name__ == "Profile":
			obj.RootProfile = wobj
	if len(sl) > 1:
		wobj = sl[1].Object
		if wobj.Proxy.__class__.__name__ == "Profile":
			obj.TipProfile = wobj
		
	FreeCAD.ActiveDocument.recompute()
	FreeCADGui.SendMsgToActiveView("ViewFit")

def createCoordSys():
	sl = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sl)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "CoordSystem")
	CoordSys(obj)
	ViewProviderCoordSys(obj.ViewObject, "WF_Axes.svg")
	if len(sl) > 0:
		pobj = sl[0].Object
		if pobj.TypeId in ["Part::Box", "Part::Extrusion", "Part::Cylinder", "PartDesign::Pad"]:
			obj.LinkedObject = pobj
	
def createRod():
	sl = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sl)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Rod")
	Rod(obj)
	ViewProviderRod(obj.ViewObject, "Rod-icon.svg")

	if len(sl) > 0:
		msgCsl("Wing found for linking Rod")
		wobj = sl[0].Object
		if wobj.Proxy.__class__.__name__ == "Wing":
			msgCsl("Wing type found in selection")
			if hasattr(wobj, "RootProfile"):
				if wobj.RootProfile != None: obj.RootWire = wobj.RootProfile.Wire
			if hasattr(wobj, "TipProfile"):
				if wobj.TipProfile != None: obj.TipWire = wobj.TipProfile.Wire
			obj.RootPoint = 1
			obj.TipPoint = 1
		if len(sl) > 1:
			wobj1, wobj2 = sl[:2]
			if wobj2.Object.Proxy.__class__.__name__ == "CoordSys":
				obj.CoordSystem = wobj2.Object
			elif wobj1.TypeName == wobj2.TypeName == "Part::Part2DObjectPython":
				if len(sl) > 2:
					wobj = sl[2].Object
					if wobj.Proxy.__class__.__name__ == "CoordSys":
						obj.CoordSystem = wobj
				obj.RootWire = wobj1.Object
				obj.TipWire = wobj2.Object
				FreeCAD.ActiveDocument.recompute()
				obj.RootPoint = 1
				obj.TipPoint = 1
	return obj

def createWrapLeadingEdge():
	sl = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sl)))
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "WrapLeadingEdge")
	WrapLeadingEdge(obj)
	ViewProviderWrapLeadingEdge(obj.ViewObject, "WrapLeadingEdge-icon.svg")
	obj.StartPoint = 1.0
	obj.EndPoint = 2.0
	if len(sl) > 0:
		wobj = sl[0]
		if wobj.Object.Proxy.__class__.__name__ == "Profile":
			msgCsl("Wing type found in selection for linking WrapLeadingEdge")
			obj.Wire = wobj.Object.Wire
		elif wobj.TypeName == "Part::Part2DObjectPython":
			obj.Wire = wobj.Object
		return obj
	else:
		userMsg("No selection or selection is not a wing object")

def createProfile():
	msgCsl("createProfile method starting...")
	a = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Profile")
	Profile(a)
	ViewProviderProfile(a.ViewObject, 'Profile-icon.svg')
	a.Scale = 300

def createLeadingEdge():
	msgCsl("createLeadingEdge method starting...")
	sl = FreeCADGui.Selection.getSelectionEx()
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","LeadingEdge")
	LeadingEdge(obj)
	ViewProviderLeadingEdge(obj.ViewObject, 'LeadingEdge-icon.svg')
	if len(sl) > 1:
		wobj1 = sl[0].Object
		wobj2 = sl[1].Object
		if wobj1.TypeId == wobj2.TypeId == "Part::Part2DObjectPython":
			obj.RootWire = wobj1
			obj.TipWire = wobj2

def createCutWire():
	msgCsl("createCutWire method starting...")
	sl = FreeCADGui.Selection.getSelectionEx()
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","CutWire")
	CutWire(obj)
	ViewProviderCutWire(obj.ViewObject, 'CutWire-icon.svg')
	if len(sl) > 0:
		wobj = sl[0].Object
		if wobj.TypeId == "Part::Part2DObjectPython":
			obj.Wire = wobj
			if len(wobj.Points) > 2:
				obj.StartPoint = 1.0
				obj.EndPoint = 3.0

def createSection():
	msgCsl("createCutWire method starting...")
	sl = FreeCADGui.Selection.getSelectionEx()
	obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Section")
	Section(obj)
	ViewProviderSection(obj.ViewObject, 'Section.svg')
	if len(sl) > 0:
		wobj = sl[0].Object
		if wobj.Shape.Volume > 0.001:
			obj.SlicedObject = wobj
		else:
			msgCsl("Shape volume is under 0.001, slice abort")
