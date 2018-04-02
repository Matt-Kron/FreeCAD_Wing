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
#	else:
#		mTangent = VecNul
		return mTangent

class Wing:

	def __init__(self, obj):
		msgCsl("class Wing, __init__")
		#############################
		# Wing properties creation
		#############################
		obj.addProperty("App::PropertyFile", "WingRootFile", "Root", "Wing root profile").WingRootFile = DefaultProfile
		obj.addProperty("App::PropertyFile", "WingTipFile", "Tip", "Wing tip profile").WingTipFile = DefaultProfile
		obj.addProperty("App::PropertyLength", "TipScale", "Tip", "Wing tip scale").TipScale = 1.0
		obj.addProperty("App::PropertyLength", "RootScale", "Root", "Wing root scale").RootScale = 1.0
		obj.addProperty("App::PropertyLength", "Length", "Wing", "Length of the wing").Length = 10.0
		obj.addProperty("App::PropertyDistance", "TipXOffset", "Tip", "Tip offset in X from root wire").TipXOffset = 0.0
		obj.addProperty("App::PropertyDistance", "TipYOffset", "Tip", "Tip offset in Y from root wire").TipYOffset = 0.0
		obj.addProperty("App::PropertyAngle", "TipAngle", "Tip", "Tip angle").TipAngle = 0.0
		obj.addProperty("App::PropertyBool", "MakeLoft", "Wing", "Make the loft from the root and tip wires").MakeLoft = False
		obj.addProperty("App::PropertyVectorList","TipPoints","Wing","Points of the wing tip", 1)
		obj.addProperty("App::PropertyVectorList","RootPoints","Wing","Points of the wing root", 1)
		obj.addProperty("App::PropertyLink","TipWire","Wing","Wire of the wing tip", 1)
		obj.addProperty("App::PropertyLink","RootWire","Wing","wire of the wing root", 1)
		obj.addProperty("App::PropertyLink","Loft","Wing","Name of the wing's loft", 1)
#		self.RootPoints = None
#		self.RootWire = None
#		self.TipPoints = None
#		self.TipWire = None
#		self.Loft = None
		obj.Proxy = self

		#############################
		# Dwire creation
		#############################
		# get the points from the root profile and make the wire
		userMsg("Loading root points from file...")
		points=[]
		points = getPoints(obj.WingRootFile)
		e = obj.RootScale
		for p in points:
			p.x = p.x * e
			p.y = p.y * e
		obj.RootPoints = points
		emplantureP = Part.makePolygon(obj.RootPoints, True)
		emplanture = Draft.makeWire(emplantureP, True, False)
		emplanture.Label = "Root wire"
		obj.RootWire = emplanture
		obj.addObject(emplanture)  # add wire object under wing group object in the tree view

		# get the points from the tip profile and make the wire
		userMsg("Loading tip points from file...")
		points=[]
		points = getPoints(obj.WingTipFile)
		e = obj.TipScale
		for p in points:
			p.x = p.x * e
			p.y = p.y * e
			p.z = obj.Length
		obj.TipPoints = points
		saumonP = Part.makePolygon(obj.TipPoints, True)
		saumon = Draft.makeWire(saumonP, True, False)
		saumon.Label = "Tip wire"
		obj.TipWire = saumon
		obj.addObject(saumon)  # add wire object under wing group object in the tree view
				
	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		msgCsl("Wing class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
		if prop == "WingRootFile":
			fp.RootPoints = getPoints(fp.WingRootFile)
			self.updateWire(fp, fp.RootWire, fp.RootPoints, False, fp.RootScale)
		if prop == "WingTipFile":
			fp.TipPoints= getPoints(fp.WingTipFile)
			self.updateWire(fp, fp.TipWire, fp.TipPoints, True,  fp.TipScale)
		if prop == "RootScale":
			self.updateWire(fp, fp.RootWire, fp.RootPoints,  False, fp.RootScale)
		if prop in ["TipScale","Length"]:
			self.updateWire(fp, fp.TipWire, fp.TipPoints, True, fp.TipScale)
#		if fp.getTypeIdOfProperty(prop) == 'App::PropertyLink':
#			msgCsl("update Tree\n")
#			updateTree(fp)
		if prop in ["TipXOffset", "TipYOffset", "TipAngle"]:
			self.updateWire(fp, fp.TipWire, fp.TipPoints,  True, fp.TipScale)
		if prop == "MakeLoft":
			if fp.MakeLoft:
				self.createLoft(fp)
			else:
				# remove Loft under wing group in the tree view, maybe not useful when removing from the document
				fp.removeObject(fp.Loft)
				# remove Loft
				FreeCAD.ActiveDocument.removeObject(fp.Loft.Name)
				
	def execute(self, fp):
		msgCsl("class Wing, execute")

	def createLoft(self, fp):
		#############################
		# Wing's loft creation
		#############################
		AileBis = FreeCAD.ActiveDocument.addObject('Part::Loft','Loft')
		AileBis.Label = "Loft_Wing"
		fp.Loft = AileBis
		AileBis.Sections = [fp.RootWire,fp.TipWire]
		AileBis.Solid = True
		AileBis.Ruled = False
		fp.addObject(AileBis)  # add Loft under wing group in the tree view
		FreeCAD.ActiveDocument.recompute()
		FreeCADGui.SendMsgToActiveView("ViewFit")
	
	def updateWire(self, fp, oWire, fWire, tipwire,  echelle):
#		msgCsl("class Wing, updateWire, " + str(fWire))
#		fW = fp.getPropertyByName(fWire)
#		e = fp.getPropertyByName(Echelle)
		z = 0.0
		if tipwire:
			z = fp.Length
			mPosition = FreeCAD.Vector(fp.TipXOffset,fp.TipYOffset,z)
			mRotation = FreeCAD.Rotation(FreeCAD.Vector(0,0,1),fp.TipAngle)
		else:
			mPosition = FreeCAD.Vector(0,0,z)
			mRotation = FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0)
		mCenter = FreeCAD.Vector(0,0,1)
		mPlacement = FreeCAD.Placement(mPosition,mRotation,mCenter)
		mPlacement = fp.RootWire.Placement.multiply(mPlacement)
		oWire.Placement = mPlacement
		pts = []
		for p in fWire:
			pts.append(FreeCAD.Vector(p.x * echelle,p.y * echelle, 0))
		oWire.Points = pts
		#FreeCADGui.SendMsgToActiveView("ViewFit")

class ViewProviderWing:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + 'Aile-icon.svg'
		obj.Proxy = self

	def getIcon(self):
		return self.icon
		
	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

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
		msgCsl("class CoordSys, __init__")
		obj.addProperty("App::PropertyLink","Parent","CoordSys","Parent object")
		obj.addProperty("App::PropertyEnumeration","CenterType","CoordSys","Either center of mass or vertexes").CenterType = ["MassCenter","Vertexes"]
		obj.addProperty("App::PropertyFloat","VertexNum","CoordSys","Vertexes or intermediate point of vertexes couple").VertexNum = 0.0
		obj.addProperty("App::PropertyLink","Tangent","CoordSys","Axis tangent to an edge", 1)
		obj.addProperty("App::PropertyLink","Normal","CoordSys","Normal of the reference face", 1)
		obj.addProperty("App::PropertyLink","Bend","CoordSys","Bend axis", 1)
		obj.addProperty("App::PropertyPlacement","LocalPlacement","CoordSys","Placement from parent initialized placement to local coordsys")
		obj.Tangent = Draft.makeWire([VecNul, FreeCAD.Vector(2,0,0)],closed=False,face=False,support=None)
		obj.Normal = Draft.makeWire([VecNul, FreeCAD.Vector(0,0,2)],closed=False,face=False,support=None)
		obj.Bend = Draft.makeWire([VecNul, FreeCAD.Vector(0,2,0)],closed=False,face=False,support=None)
		obj.Tangent.ViewObject.LineColor = (1.0,0.0,0.0)
		obj.Normal.ViewObject.LineColor = (0.0,0.0,1.0)
		obj.Bend.ViewObject.LineColor = (0.0,1.0,0.0)
#		self.FaceNumber = 0
		self.pName = ""
		self.LocalOrigin = VecNul
#		self.Parent = None
		self.ParentOk = False
		self.ParentOrigin = VecNul
		self.ParentCenterOfMass = VecNul
		self.ParentEdges = None
		obj.addObject(obj.Tangent)
		obj.addObject(obj.Normal)
		obj.addObject(obj.Bend)
		obj.CenterType = "Vertexes"
		obj.Proxy = self

	def execute(self, fp):
		msgCsl("class CoordSys, execute")

	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		if fp.getTypeIdOfProperty(prop) == 'App::PropertyLink':
#		msgCsl("CoordSys class property change: " + str(prop))
		if prop == "Parent":
			msgCsl("CoordSys class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
			if self.pName != fp.Parent.Name:
				self.pName = fp.Parent.Name
#			if self.Parent != None: self.updateRefFace(fp)
				self.updateRefFace(fp)
				self.updatePlacement(fp)
		if prop in ["CenterType","VertexNum"]:
#			msgCsl("CoordSys class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
			self.updatePlacement(fp)

#	def claimChildren(self, fp):
#		if hasattr(self, "Object"):
#		return fp.Group
#		else:
#			return []
	
	def updateRefFace(self, fp):
		if fp.Parent.TypeId == "Part::Extrusion": # "PartDesign::Pad":
			nb = len(fp.Parent.Base.Shape.Edges)
			mface = fp.Parent.Shape.Faces[nb+1]
			self.ParentEdges = mface.Edges
			self.ParentCenterOfMass = mface.CenterOfMass
			self.ParentOrigin = fp.Parent.Shape.Vertex1.Point
			self.ParentOk = True
		if fp.Parent.TypeId == "PartDesign::Pad":
			self.ParentEdges = fp.Parent.Sketch.Shape.Edges
			self.ParentCenterOfMass = fp.Parent.Sketch.Shape.CenterOfMass
			self.ParentOrigin = fp.Parent.Sketch.Placement.Base
			self.ParentOk = True
		elif fp.Parent.TypeId == "Part::Cylinder":
			self.ParentEdges = fp.Parent.Shape.Face3.Edges
			self.ParentCenterOfMass = fp.Parent.Shape.Face3.CenterOfMass
			self.ParentOrigin = self.ParentCenterOfMass
			self.ParentOk = True
		if fp.Parent.TypeId == "Part::Box":
			self.ParentEdges = fp.Parent.Shape.Face5.Edges
			self.ParentCenterOfMass = fp.Parent.Shape.Face5.CenterOfMass
			self.ParentOrigin = fp.Parent.Shape.Vertex2.Point
			self.ParentOk = True

	def updatePlacement(self, fp):
		if self.ParentOk:
			if fp.Parent.TypeId == "PartDesign::Pad":
				fp.Parent.Sketch.Placement = fp.Tangent.Placement
			else:
				fp.Parent.Placement = fp.Tangent.Placement
			self.updateRefFace(fp)
			Fract = int((round(fp.VertexNum,2) - int(fp.VertexNum))*100)
#			msgCsl("Fract "+ str(Fract))
			mEdge = self.ParentEdges[int(fp.VertexNum)] #fp.Parent.Shape.Faces[self.FaceNumber].Edges[int(fp.VertexNum)]
			if Fract > 0:
				Pts = mEdge.discretize(101)
				Pt = Pts[Fract]
			else:
				Pt = mEdge.valueAt(0) #fp.Parent.Shape.Faces[self.FaceNumber].Vertexes[int(fp.VertexNum)].Point
			if fp.CenterType == "MassCenter":
				self.LocalOrigin = self.ParentCenterOfMass #fp.Parent.Shape.Faces[self.FaceNumber].CenterOfMass
				mBend = PtsToVec(self.LocalOrigin,Pt)
			else:
				self.LocalOrigin = Pt
				mBend = PtsToVec(self.LocalOrigin, self.ParentCenterOfMass) #fp.Parent.Shape.Faces[self.FaceNumber].CenterOfMass)
			msgCsl("LocalOrigin "+ format(self.LocalOrigin))
			mTrans = PtsToVec(self.LocalOrigin,self.ParentOrigin)
			mRot = FreeCAD.Rotation(mBend,fp.Bend.End.sub(fp.Bend.Start))
			mPlacement2 = FreeCAD.Placement(mTrans,mRot,self.LocalOrigin)
			fp.LocalPlacement = mPlacement2
			if fp.Parent.TypeId == "PartDesign::Pad":
				fp.Parent.Sketch.Placement = fp.LocalPlacement.multiply(fp.Parent.Sketch.Placement)
			else:
				fp.Parent.Placement = fp.LocalPlacement.multiply(fp.Parent.Placement)

	def updateAxis(self, fp, mPlacement1 = FreeCAD.Placement()):
		if self.ParentOk:
			fp.Tangent.Placement = mPlacement1
			fp.Normal.Placement = mPlacement1
			fp.Bend.Placement = mPlacement1
			self.updatePlacement(fp)


class ViewProviderCoordSys:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
#		obj.addProperty("App::PropertyColor","Color","CoordSys","Color of the box").Color=(1.0,0.0,0.0)
		self.Object = obj.Object
		self.icon = iconPath + 'WF_Axes.svg'
		obj.Proxy = self

	def attach(self, fp):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
#		self.line = coin.SoSeparator()
#		self.color = coin.SoBaseColor()
#		c=fp.Color
#		self.color.rgb.setValue(c[0],c[1],c[2])
#		data=coin.SoCube()
#		self.line.addChild(self.color)
#		self.line.addChild(data)

	def getIcon(self):
		return self.icon

	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
                Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
                to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
                Since no data were serialized nothing needs to be done here.'''
		return None


class Rod:

	def __init__(self, obj):
		msgCsl("class Rod, __init__")
		#############################
		# Rod properties
		#############################
		obj.addProperty("App::PropertyLink", "Rod","Rod","Object linked to the rod")
		obj.addProperty("App::PropertyLink", "RootWire","Root","Root wire linked to the rod")
		obj.addProperty("App::PropertyLink", "TipWire","Tip","Tip wire linked to the rod")
		obj.addProperty("App::PropertyLink", "CoordSystem","Rod","Local coordinate system", 1)
		obj.addProperty("App::PropertyFloat","RootPoint", "Root","Digit point of the root wire").RootPoint = 0.0
		obj.addProperty("App::PropertyFloat","TipPoint", "Tip","Digit point of the tip wire").TipPoint = 0.0
		obj.addProperty("App::PropertyBool","AutoRotate", "Rod","Rotate the rod according the mean of the root and tip tangents").AutoRotate = True
		obj.addProperty("App::PropertyDistance","RootOffset", "Root","Offset from the root (outside)").RootOffset = 1.0
		obj.addProperty("App::PropertyDistance","TipOffset", "Tip","Offset from the tip (outside)").TipOffset = 1.0
		obj.addProperty("App::PropertyDistance","RootInnerOffset", "Root","Root inner offset").RootInnerOffset = 0.0
		obj.addProperty("App::PropertyDistance","TipInnerOffset", "Tip","Tip inner offset").TipInnerOffset = 0.0
		obj.addProperty("App::PropertyVectorList", "VectorList", "Rod", "Vectors list used for placement", -1)
#		obj.addProperty("App::PropertyAngle","RootAngleOffset", "Rod","Angle offset").RootAngleOffset = 0.0
#		obj.addProperty("App::PropertyAngle","TipAngleOffset", "Rod","Angle offset").TipAngleOffset = 0.0
		Coord = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython","CoordSys")
		CoordSys(Coord)
		ViewProviderCoordSys(Coord.ViewObject)
		obj.CoordSystem = Coord
		self.VecList = {"VecRoot":0, "VecRootTangent":1, "VecRootCurvature":2, "VecTip":3, "VecTipTangent":4, "VecTipCurvature":5, "VecDirRod":6, "VecRodEdge":7, "VecRodCenter":8}
#		self.VecRoot = VecNul
#		self.VecRootTangent = VecNul
#		self.VecRootCurvature = VecNul
#		self.VecTip = VecNul
#		self.VecTipTangent = VecNul
#		self.VecTipCurvature = VecNul
#		self.VecDirRod = VecNul
#		self.VecRodEdge = VecNul
#		self.VecRodCenter = VecNul
#		self.VecList["VecRodCenter"] = 6
		vect = []
		for vec in self.VecList:
			vect.append(VecNul)
#			obj.VectorList.append(VecNul)
		obj.VectorList = vect
#		msgCsl("Vector: " + str(vec) + "  " + str(self.VecList[vec]))
#		msgCsl("obj vector: " + format(obj.VectorList[self.VecList[vec]]))
		self.ObjNameList = {"Rod":"",  "RootWire":"",  "TipWire":"", "CoordSystem":""}
		obj.addObject(Coord)
		obj.Proxy = self

	def onChanged(self, fp, prop):
		# Do something when a property has changed
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
				if obj.Name != self.ObjNameList[prop]:
					if self.ObjNameList[prop] != "":
						fp.removeObject(FreeCAD.ActiveDocument.getObject(self.ObjNameList[prop]))
					self.ObjNameList[prop] = obj.Name
					fp.addObject(obj)
					if prop == "Rod":
						self.updateLength(fp)
		#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
						self.updateCoordSys(fp)
					if prop == "RootWire":
		#				msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
						self.calcVecRoot(fp)
						self.updatePosition(fp)
					if prop == "TipWire":
						msgCsl("Rod class property change: " + str(prop) + "  Type of property :" + str(fp.getTypeIdOfProperty(prop)))
						self.calcVecTip(fp)
						self.updatePosition(fp)
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
			

	def execute(self, fp):
		msgCsl("class Rod, execute")
	
	def testWires(self, fp):
		test = False
		if hasattr(fp.RootWire, 'Shape'):
			if hasattr(fp.TipWire, 'Shape'):
				test = True
			else:
				test = False
		else:
			test = False
#		msgCsl("testWires " + str(test))
		return test

	def updateCoordSys(self,fp):
		fp.CoordSystem.Parent = fp.Rod
		
#	def Vec(self, fp, vectorstr):
#		return fp.VectorList[self.VecList[vectorstr]]

	def calcVecRoot(self, fp):
		try:  # if the root wire is not null
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
			pc = fp.RootWire.Shape.Vertexes[int(fp.RootPoint)].Point
			pav = fp.RootWire.Shape.Vertexes[int(fp.RootPoint)-1].Point
			pap = fp.RootWire.Shape.Vertexes[int(fp.RootPoint)+1].Point
#			msgCsl("pc "+ format(pc))
#			msgCsl("pav "+ format(pav))
#			msgCsl("pap "+ format(pap))
#			fp.VectorList[self.VecList["VecRootTangent"]] = PtsToVec(pav,pap) #self.VecRootTangent = PtsToVec(pav,pap)
			veclist = fp.VectorList
			veclist[self.VecList["VecRootTangent"]] = PtsToVec(pav,pap) #self.VecRootTangent = PtsToVec(pav,pap)
			fp.VectorList = veclist
#			msgCsl("indice VecRootTangent: " + str(self.VecList["VecRootTangent"]) + " vector VecRootTangent: " + format(fp.VectorList[self.VecList["VecRootTangent"]]))
#			fp.VectorList[self.VecList["VecRootTangent"]].normalize() #self.VecRootTangent.normalize()
			veclist[self.VecList["VecRootTangent"]].normalize()
			nbpts = len(fp.RootWire.Points)
			gap = int(nbpts/3)
#			Test = True
#			i = 1
#			while Test:
			pav = fp.RootWire.Shape.Vertexes[int(fp.RootPoint) - gap].Point
			pap = fp.RootWire.Shape.Vertexes[int(fp.RootPoint) + gap].Point
			VecRootNormal = PtsToVec(pc,pav).cross(PtsToVec(pc,pap))
#				try:
			VecRootNormal.normalize()
#					Test = False
#				except:
#					i += 1
#			msgCsl("VecRootNormal count i " + str(i))
#			fp.VectorList[self.VecList["VecRootCurvature"]] = fp.VectorList[self.VecList["VecRootTangent"]].cross(VecRootNormal)
			veclist[self.VecList["VecRootCurvature"]] = veclist[self.VecList["VecRootTangent"]].cross(VecRootNormal)
			# self.VecRootCurvature = self.VecRootTangent.cross(VecRootNormal)
#			msgCsl("VecRootNormal "+ format(VecRootNormal))
#			fp.VectorList[self.VecList["VecRootCurvature"]].normalize() #self.VecRootCurvature.normalize()
			veclist[self.VecList["VecRootCurvature"]].normalize() #self.VecRootCurvature.normalize()
			if fp.RootInnerOffset != 0:
				#self.VecRoot = Pt.add(self.VecRootCurvature.multiply(fp.RootInnerOffset))
#				fp.VectorList[self.VecList["VecRoot"]] = Pt.add(fp.VectorList[self.VecList["VecRootCurvature"]].multiply(fp.RootInnerOffset))
#				fp.VectorList[self.VecList["VecRootCurvature"]].normalize()
				veclist[self.VecList["VecRoot"]] = Pt.add(veclist[self.VecList["VecRootCurvature"]].multiply(fp.RootInnerOffset))
				veclist[self.VecList["VecRootCurvature"]].normalize()
			else:
#				fp.VectorList[self.VecList["VecRoot"]] = Pt #self.VecRoot = Pt
				veclist[self.VecList["VecRoot"]] = Pt #self.VecRoot = Pt
#			msgCsl("VecRoot "+ format(self.VecRoot))
			fp.VectorList = veclist
			self.calcVecDirRod(fp)
		except:
			pass

	def calcVecTip(self, fp):
#		try:  # if the root wire is not null
		if fp.TipWire != None:
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
			pc = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)].Point
			pav = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)-1].Point
			pap = fp.TipWire.Shape.Vertexes[int(fp.TipPoint)+1].Point
#			self.VecTipTangent = PtsToVec(pav,pap)
			veclist = fp.VectorList
#			fp.VectorList[self.VecList["VecTipTangent"]] = PtsToVec(pav, pap)
			veclist[self.VecList["VecTipTangent"]] = PtsToVec(pav, pap)
#			self.VecTipTangent.normalize()
#			fp.VectorList[self.VecList["VecTipTangent"]].normalize()
			veclist[self.VecList["VecTipTangent"]].normalize()
			msgCsl("indice VecTipTangent: " + str(self.VecList["VecTipTangent"]) + " vector VecTipTangent: " + format(veclist[self.VecList["VecTipTangent"]]))
			nbpts = len(fp.TipWire.Points)
			gap = int(nbpts/3)
#			Test = True
#			i = 1
#			while Test:
			pav = fp.TipWire.Shape.Vertexes[int(fp.TipPoint) - gap].Point
			pap = fp.TipWire.Shape.Vertexes[int(fp.TipPoint) + gap].Point
			VecTipNormal = PtsToVec(pc,pav).cross(PtsToVec(pc,pap))
#				try:
			VecTipNormal.normalize()
#					Test = False
#				except:
#					i += 1
#			msgCsl("VecTipNormal count i " + str(i))					
#			self.VecTipCurvature = self.VecTipTangent.cross(VecTipNormal)
#			fp.VectorList[self.VecList["VecTipCurvature"]] = fp.VectorList[self.VecList["VecTipTangent"]].cross(VecTipNormal)
			veclist[self.VecList["VecTipCurvature"]] = veclist[self.VecList["VecTipTangent"]].cross(VecTipNormal)
			msgCsl("VecTipNormal "+ format(VecTipNormal))
#			self.VecTipCurvature.normalize()
#			fp.VectorList[self.VecList["VecTipCurvature"]].normalize()
			veclist[self.VecList["VecTipCurvature"]].normalize()
			if fp.TipInnerOffset != 0:
#				self.VecTip = Pt.add(self.VecTipCurvature.multiply(fp.TipInnerOffset))
#				self.VecTipCurvature.normalize()
#				fp.VectorList[self.VecList["VecTip"]] = Pt.add(fp.VectorList[self.VecList["VecTipCurvature"]].multiply(fp.TipInnerOffset))
#				fp.VectorList[self.VecList["VecTipCurvature"]].normalize()
				veclist[self.VecList["VecTip"]] = Pt.add(veclist[self.VecList["VecTipCurvature"]].multiply(fp.TipInnerOffset))
				veclist[self.VecList["VecTipCurvature"]].normalize()
			else:
#				self.VecTip = Pt
				veclist[self.VecList["VecTip"]] = Pt
#				msgCsl("VecTip "+ format(self.VecTip))
				msgCsl("indice VecTip: " + str(self.VecList["VecTip"]) + " vector VecTip: " + format(veclist[self.VecList["VecTip"]]))
			fp.VectorList = veclist
			self.calcVecDirRod(fp)
#		except:
#			pass

	def calcVecDirRod(self, fp):
#		self.VecDirRod = self.VecTip.sub(self.VecRoot)
		veclist = fp.VectorList
		veclist[self.VecList["VecDirRod"]] = veclist[self.VecList["VecTip"]].sub(veclist[self.VecList["VecRoot"]])
		fp.VectorList = veclist
#		msgCsl("VecDirRod "+ format(self.VecDirRod))
#		msgCsl("VecDirRod.Length "+ str(self.VecDirRod.Length))

	def calcVecRod(self, fp):
#		self.VecRodCenter = fp.CoordSystem.Tangent.Start
#		self.VecRodEdge = PtsToVec(fp.CoordSystem.Tangent.Start,fp.CoordSystem.Tangent.End)
		veclist = fp.VectorList
		veclist[self.VecList["VecRodCenter"]] = fp.CoordSystem.Tangent.Start
		veclist[self.VecList["VecRodEdge"]] = PtsToVec(fp.CoordSystem.Tangent.Start, fp.CoordSystem.Tangent.End)
		fp.VectorList = veclist

	def updateRootPosition(self, fp):
		if self.testWires(fp):
			veclist = fp.VectorList
			mDir = veclist[self.VecList["VecDirRod"]] #self.VecDirRod
			mDir = FreeCAD.Vector(mDir.x, mDir.y, mDir.z)
			mDir.normalize()
			mDir.multiply(-fp.RootOffset)
			self.calcVecRod(fp)
#			mDir = mDir.sub(PtsToVec(self.VecRoot,self.VecRodCenter))
			mDir = mDir.sub(PtsToVec(veclist[self.VecList["VecRoot"]], veclist[self.VecList["VecRodCenter"]]))
			mPlacement = Placement() #FreeCAD.Placement(mDir,FreeCAD.Rotation())
			mPlacement.move(mDir)
			fp.CoordSystem.Proxy.updateAxis(fp.CoordSystem,mPlacement.multiply(fp.CoordSystem.Tangent.Placement))
#			fp.VectorList = veclist
			self.updateLength

	def updateLength(self, fp):
		if self.testWires:
			veclist = fp.VectorList
			if fp.Rod.TypeId in ["Part::Box","Part::Cylinder"]:
#				fp.Rod.Height = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)
#				msgCsl("indice VecDirRod: " + str(self.VecList["VecDirRod"]) + " vector VecDirRod: " + format(fp.VectorList[self.VecList["VecDirRod"]]))
				fp.Rod.Height = veclist[self.VecList["VecDirRod"]].Length + float(fp.RootOffset) + float(fp.TipOffset)
			if fp.Rod.TypeId == "PartDesign::Pad":
#				fp.Rod.Length = self.VecDirRod.Length + float(fp.RootOffset) + float(fp.TipOffset)
				fp.Rod.Length = veclist[self.VecList["VecDirRod"]].Length + float(fp.RootOffset) + float(fp.TipOffset)
#			fp.VectorList = veclist

	def updatePosition(self,fp):
		if self.testWires(fp):
			veclist = fp.VectorList
			VecRoot = veclist[self.VecList["VecRoot"]] #self.VecRoot
			VecDirRod = veclist[self.VecList["VecDirRod"]] #self.VecDirRod
			mRot = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), VecDirRod)
			msgCsl("VecRoot "+ format(VecRoot))
			mPlacementAlign = Placement()
			mPlacementAlign.move(VecRoot)
			mPlacementAlign = FreeCAD.Placement(VecNul, mRot, VecRoot).multiply(mPlacementAlign)
			msgCsl("mPlacementAlign "+ format(mPlacementAlign))
			fp.CoordSystem.Proxy.updateAxis(fp.CoordSystem, mPlacementAlign)
			if fp.AutoRotate:
				VecRootTangent = veclist[self.VecList["VecRootTangent"]] #self.VecRootTangent
				VecTipTangent = veclist[self.VecList["VecTipTangent"]] #self.VecTipTangent
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
				fp.CoordSystem.Proxy.updateAxis(fp.CoordSystem, mPlacement.multiply(fp.CoordSystem.Tangent.Placement))
			self.updateRootPosition(fp)
			self.updateLength(fp)

class ViewProviderRod:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + 'Rod-icon.svg'
		obj.Proxy = self

	def getIcon(self):
		return self.icon

	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

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
		msgCsl("class Wing, __init__")
		obj.addProperty("App::PropertyLink", "RootWire", "Root", "Wire of the wing root")
		obj.addProperty("App::PropertyLink", "TipWire", "Tip", "Wire of the wing tip")
		obj.addProperty("App::PropertyFloat","RootStartPoint", "Root","Start digit point of the root wire").RootStartPoint = 0.0
		obj.addProperty("App::PropertyFloat","RootEndPoint", "Root","Number of points of the root wrap").RootEndPoint = 1.0
		obj.addProperty("App::PropertyFloat","TipStartPoint", "Tip","Start digit point of the tip wire").TipStartPoint = 0.0
		obj.addProperty("App::PropertyFloat","TipEndPoint", "Tip","Number of points of the tip wrap").TipEndPoint = 1.0
		obj.addProperty("App::PropertyDistance", "Thickness", "WrapLeadingEdge", "Thickness of the wrap").Thickness = 1.5
		obj.addProperty("App::PropertyBool", "MakeLoft", "WrapLeadingEdge", "Make the loft from the root wrap and tip wrap wires").MakeLoft = False
		obj.addProperty("App::PropertyLink","Loft","WrapLeadingEdge","Name of the wrapped leading edge's loft", 1)
		self.LoftName = ""
		self.RootPortion = None
		self.ShiftedRootPortion = None
		self.RootWrap = None
#		self.TipPortion = None
#		self.ShiftedTipPortion = None
		self.TipWrap = None
#		self.Loft = None
		self.RootWireLinked = False
		self.TipWireLinked = False
		obj.Proxy = self

	def onChanged(self, fp, prop):
		# Do something when a property has changed
#		if prop == "Loft":
#			if fp.Loft.Name != self.LoftName:
#				if self.LoftName != "":
#					fp.removeObject(FreeCAD.ActiveDocument.getObject(self.LoftName))
#				fp.addObject(fp.Loft)
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
				# remove Loft under WrapLeadingEdge group in the tree view, maybe not useful when removing from the document
				fp.removeObject(fp.Loft)
				# remove Loft
				FreeCAD.ActiveDocument.removeObject(fp.Loft.Name)

	def execute(self, fp):
		msgCsl("class WrapLeadingEdge, execute")
		
	def createLoft(self, fp):
		#############################
		# Leading edge wrap loft creation
		#############################
		wraploft = FreeCAD.ActiveDocument.addObject('Part::Loft','Loft')
		wraploft.Label = "Loft_WrapLeadingEdge"
		fp.Loft = wraploft
		wraploft.Sections = [self.RootWrap, self.TipWrap]
		wraploft.Solid = True
		wraploft.Ruled = False
		fp.addObject(wraploft)  # add Loft under wing group in the tree view
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
#			else:
#				pt = wire.Shape.Vertexes[int(start) + int(length)].Point
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
			fp.addObject(wrapobj)
			if side == "Root":
				wrapobj.Label = "RootWrap"
				self.RootWrap = wrapobj
			else:
				wrapobj.Label = "TipWrap"
				self.TipWrap = wrapobj
	
	def updateWrap(self, fp, wire,  start,  end,  side):
		if wire != None and int(end) > int(start):
			pts = self.calculateWrapPoints(fp, wire, start, end)
			wrapOk = False
			if side == "Root":
				if self.RootWrap != None :
					wrappts = self.RootWrap.Points
					wrapOk = True
			else:
				if self.TipWrap != None :
					wrappts = self.TipWrap.Points
					wrapOk = True
			if wrapOk:
				nbwrap = len(wrappts)
				nbpts = len(pts)
				msgCsl("len(wrappts): " + str(nbwrap) + "  len(pts): " + str(nbpts))
				if nbpts < nbwrap:
					for i in range(nbpts, nbwrap, +1):
#						msgCsl("count i: " + str(i))
						wrappts.remove(wrappts[nbpts])
#				if nbpts == nbwrap:
#					for i in range(0, nbpts, +1):
##						msgCsl("count i: " + str(i))
#						wrappts[i] = pts[i]
				if nbpts > nbwrap:
					for i in range(nbwrap, nbpts, +1):
						wrappts.append(pts[i])   # pts[i] does not matter, it's just to increase the wire points number
#				for i in range(0, nbpts, +1):
#					msgCsl("count i: " + str(i))
#					wrappts[i] = pts[i]
				if side == "Root":
					self.RootWrap.Points = pts
				else:
					self.TipWrap.Points = pts

class ViewProviderWrapLeadingEdge:

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.Object = obj.Object
		self.icon = iconPath + 'WrapLeadingEdge-icon.svg'
		obj.Proxy = self

	def getIcon(self):
		return self.icon
		
	def claimChildren(self):
		if hasattr(self, "Object"):
			return self.Object.OutList
		else:
			return []

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
	a = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython","Wing")  #FeaturePython
	Wing(a)
	ViewProviderWing(a.ViewObject)
#	a.ViewObject.Proxy=0 # just set it to something different from None (this assignment is needed to run an internal notification)
	a.RootScale=300
	a.TipScale=150
	a.Length=500
#	a.execute
	FreeCAD.ActiveDocument.recompute()
	FreeCADGui.SendMsgToActiveView("ViewFit")

def createRod():
	sel = FreeCADGui.Selection.getSelectionEx()
	msgCsl("Content of selection: " + str(len(sel)))
	obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython","Rod")
	mBox = FreeCAD.ActiveDocument.addObject("Part::Box","Box")
	mBox.Width = 3
	mBox.Length = 3
	mBox.Height = 520
	Rod(obj)
	ViewProviderRod(obj.ViewObject)
	obj.Rod = mBox

	if len(sel) > 0:
		msgCsl("Wing found for linking Rod")
		wobj = sel[0].Object
		if wobj.Proxy.__class__.__name__ == "Wing":
			msgCsl("Wing type found in selection")
			obj.RootWire = wobj.RootWire
			obj.TipWire = wobj.TipWire
			obj.RootPoint = 1
			obj.TipPoint = 1
			wobj.addObject(obj)
		
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
	obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", "WrapLeadingEdge")
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
			obj.RootWire = wobj.RootWire
			obj.TipWire = wobj.TipWire
#			obj.Proxy.createWrap(obj, obj.RootWire, obj.RootStartPoint, obj.RootLength, "Root")
#			obj.Proxy.createWrap(obj, obj.TipWire, obj.TipStartPoint, obj.TipLength, "Tip")
			wobj.addObject(obj)
		return obj
	else:
		userMsg("No selection or selection is not a wing object")

