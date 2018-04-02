import os, re
import FreeCAD
from PySide import QtGui

ModeVerbose = True
VecNul = FreeCAD.Vector(0,0,0)

def msgCsl(message):
	if ModeVerbose:
		FreeCAD.Console.PrintMessage(message + "\n")

def userMsg(message):
	FreeCAD.Console.PrintMessage(message + "\n")

if open.__module__ == '__builtin__':
	pythonopen = open

def FileProfil():
	# PySide returns a tuple (filename, filter) instead of just a string like in PyQt
	FileProfil, filefilter = QtGui.QFileDialog.getOpenFileName(QtGui.qApp.activeWindow(),'Open An Airfoil File',FreeCAD.ConfigGet("UserHomePath"),'*.dat')
	msgCsl(FileProfil+"\n")
	return  FileProfil

def NomFichier(filename):
	NomFichier = os.path.basename(filename)
	msgCsl(NomFichier+"\n")
	return NomFichier

def CheminFichier(filename):
	CheminFichier = os.path.dirname(filename)
	msgCsl(CheminFichier+"\n")
	return CheminFichier

def getPoints(filename):
	# Regex to identify data rows and throw away unused metadata
	regex = re.compile(r'^\s*(?P<xval>(\-|\d*)\.\d+(E\-?\d+)?)\,?\s*(?P<yval>\-?\s*\d*\.\d+(E\-?\d+)?)\s*$')
	afile = pythonopen(filename,'r')
	# read the airfoil name which is always at the first line
	afile.readline().strip()	# airfoilname = afile.readline().strip()
	coords=[]
#	upside=True
#	last_x=None
	# Collect the data for the upper and the lower side seperately if possible
	for lin in afile:
		curdat = regex.match(lin)
		if curdat != None:
			x = float(curdat.group("xval"))
			y = float(curdat.group("yval"))
			# the normal processing
			coords.append(FreeCAD.Vector(x,y,0))
		# End of if curdat != None
	# End of for lin in file
	afile.close()
	return coords

def PtsToVec(p1,p2):
	v=FreeCAD.Vector(p2.x-p1.x,p2.y-p1.y,p2.z-p1.z)
	return v

def middle(v1, v2):
	v=FreeCAD.Vector((v1.x+v2.x)/2,(v1.y+v2.y)/2,(v1.z+v2.z)/2)
	return v

def normalVec(wire, index):
	if len(wire.Points) >= 3:
		nbpts = len(wire.Points)
		gap = int(nbpts/3)
		pc = wire.Shape.Vertexes[index].Point
		pav = wire.Shape.Vertexes[index - gap].Point
		pap = wire.Shape.Vertexes[(index + gap) % nbpts].Point
		vecnorm = PtsToVec(pc,pav).cross(PtsToVec(pc,pap))
		vecnorm.normalize()
	else:
		vecnorm = VecNul
	return vecnorm
	
def tangentVec(wire, index):
	if len(wire.Points) >= 3:
		vectan = PtsToVec(wire.Shape.Vertexes[index - 1].Point, wire.Shape.Vertexes[index + 1].Point)
		vectan.normalize()
	elif len(wire.Points) == 2:
		vectan = PtsToVec(wire.Shape.Vertexes[index].Point, wire.Shape.Vertexes[index + 1].Point)
		vectan.normalize()
	else:
		vectan = VecNul
	return vectan

def curveVec(wire, index):
	veccurv = tangentVec(wire, index).cross(normalVec(wire, index))
	return veccurv
	
def DiscretizedPoint(wire, value):
	medge = wire.Shape.Edges[int(value)]
	fract = int((round(value,2) - int(value))*100)
	if fract > 0:
		ptsdis = medge.discretize(101)
		pt = ptsdis[fract]
	else:
		pt = wire.Shape.Vertexes[int(value)].Point
	return pt	

def cutWire(wire, start, end):
	intstart = int(start)
	fracstart = int((round(start, 2) - int(start))*100)
	intend = int(end)
	fracend = int((round(end, 2) - int(end))*100)
	ptsright = []
	ptsright.append(DiscretizedPoint(wire, start)) # first point is 'start' or intermediate point of 'first' edge
	for i in range(intstart + 1, intend + 1, + 1):  # second point is always 'start' + 1
		ptsright.append(wire.Shape.Vertexes[i].Point)
	if fracend > 0:   # if 'end' point has decimal, one should add the intermediate point of 'last' edge
		ptsright.append(DiscretizedPoint(wire, end))
	ptsleft = []
	for i in range(0, intstart + 1, + 1):
		ptsleft.append(wire.Shape.Vertexes[i].Point)
	if fracstart > 0:   # if 'start' point has decimal, one should add the intermediate point of 'first' edge
		ptsleft.append(DiscretizedPoint(wire, start))
	ptsleft.append(DiscretizedPoint(wire, end))  # next point is 'end' point or the intermediate point of 'last' edge
	for i in range(intend + 1, len(wire.Points), + 1):  # first point of the loop is always the following point of 'end' point
		ptsleft.append(wire.Shape.Vertexes[i].Point)
	return [ptsleft, ptsright]
