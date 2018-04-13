import os, re
import FreeCAD
from PySide import QtGui
from FreeCAD import Vector

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
	
def tangentVec(wire, index, mtype):
	i = 0
	j = -1
	if mtype == "Previous":
		i = 1
		j = 0
	elif mtype == "Next":
		i = 0
		j = 1
	elif mtype == "PreviousAndNext":
		i = 1
		j = 1
#	msgCsl("i: " + str(i) + "j: " + str(j) + "type: " + mtype)
	if len(wire.Points) >= 3:
		vectan = PtsToVec(wire.Shape.Vertexes[index - i].Point, wire.Shape.Vertexes[index + j].Point)
		vectan.normalize()
	elif len(wire.Points) == 2:
		vectan = PtsToVec(wire.Shape.Vertexes[index].Point, wire.Shape.Vertexes[index - 1].Point)
		vectan.normalize()
	else:
		vectan = VecNul
	return vectan

def curveVec(wire, index):
	veccurv = tangentVec(wire, index, "PreviousAndNext").cross(normalVec(wire, index))
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

def cutWire(wire, start, end):  # start and end are represent wire.Vertexes[start or end] and intermediate point in case of float
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
	return ptsleft, ptsright
	
def  intersecLinePlane(A,B, plane):
    """ Return the intersection between a line A,B and a planar face.
    """
    N = plane.normalAt(0,0)
    a, b, c = N.x, N.y, N.z
    p1 = plane.CenterOfMass
    d = -((a * p1.x) + (b * p1.y) + (c * p1.z))
    ax, ay, az = A.x, A.y, A.z
    bx, by, bz = B.x, B.y, B.z
    ux, uy, uz = bx - ax, by - ay, bz - az
    U = Vector(ux, uy, uz)
    
    if U.dot(N) == 0.0:
        # if A belongs to P : the full Line L is included in the Plane
        if (a * ax) + (b * ay) + (c * az) + d == 0.0:
            return A
        # if not the Plane and line are paralell without intersection
        else:
            return None
    else:
        if ( a * ux + b * uy + c *uz ) == 0.0:
            return None
        k = -1 * (a * ax + b * ay + c * az  + d) / ( a * ux + b * uy + c *uz )
        tx = ax + k * ux 
        ty = ay + k * uy
        tz = az + k * uz
        T = Vector(tx, ty, tz)
        return T
