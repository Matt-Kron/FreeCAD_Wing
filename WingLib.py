import os, re, math
import FreeCAD
#import DraftGeomUtils
from PySide import QtGui
from FreeCAD import Vector

ModeVerbose = True
VecNul = FreeCAD.Vector(0,0,0)
global verbose
verbose=0

if open.__module__ == '__builtin__':
	pythonopen = open

def msgCsl(message):
	if ModeVerbose:
		FreeCAD.Console.PrintMessage(message + "\n")

def userMsg(message):
	FreeCAD.Console.PrintMessage(message + "\n")

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
	nbpts = len(wire.Points)
	if nbpts >= 3:
		vectan = PtsToVec(wire.Shape.Vertexes[(index - i) % nbpts].Point, wire.Shape.Vertexes[(index + j) % nbpts].Point)
		vectan.normalize()
	elif nbpts == 2:
		vectan = PtsToVec(wire.Shape.Vertexes[index % nbpts].Point, wire.Shape.Vertexes[(index - 1) % nbpts].Point)
		vectan.normalize()
	else:
		vectan = VecNul
	return vectan

def curveVec(wire, index, mtype):
	veccurv = tangentVec(wire, index, mtype).cross(normalVec(wire, index))
	return veccurv
	
def DiscretizedPoint(wire, value):
	medge = wire.Shape.Edges[int(value)]
	fract = abs(int((round(value,2) - int(value))*100))
	if fract > 0:
		ptsdis = medge.discretize(101)
		pt = ptsdis[fract]
	else:
		pt = wire.Shape.Vertexes[int(value)].Point
	return pt	

def cutWire(wire, start, end, type):  # start and end are represent wire.Vertexes[start or end] and intermediate point in case of float
	intstart = int(start)
	fracstart = int((round(start, 2) - int(start))*100)
	intend = int(end)
	fracend = int((round(end, 2) - int(end))*100)
	ptsright = []
	if type in ["Right", "Both"]:
		ptsright.append(DiscretizedPoint(wire, start)) # first point is 'start' or intermediate point of 'first' edge
		for i in range(intstart + 1, intend + 1, + 1):  # second point is always 'start' + 1
			ptsright.append(wire.Shape.Vertexes[i].Point)
		if fracend > 0:   # if 'end' point has decimal, one should add the intermediate point of 'last' edge
			ptsright.append(DiscretizedPoint(wire, end))
	ptsleft = []
	if type in ["Left", "Both"]:
		for i in range(0, intstart + 1, + 1):
			ptsleft.append(wire.Shape.Vertexes[i].Point)
		if fracstart > 0:   # if 'start' point has decimal, one should add the intermediate point of 'first' edge
			ptsleft.append(DiscretizedPoint(wire, start))
		ptsleft.append(DiscretizedPoint(wire, end))  # next point is 'end' point or the intermediate point of 'last' edge
		for i in range(intend + 1, len(wire.Shape.Vertexes), + 1):  # first point of the loop is always the following point of 'end' point
			ptsleft.append(wire.Shape.Vertexes[i].Point)
	return ptsleft, ptsright
	
def intersecLinePlane(A,B, plane):
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

def intersecPerpendicularLine(A, B, C, info=0):
    """ Return the intersection between the Line L defined by A and B
    and the Line perpendicular crossing the point C.
    """
    if A == B:
        return None
    ax, ay, az = A.x, A.y, A.z
    bx, by, bz = B.x, B.y, B.z
    cx, cy, cz = C.x, C.y, C.z
    ux, uy, uz = bx - ax, by - ay, bz - az
    if (ux*ux + uy*uy + uz*uz) == 0.0:
        return None
    k = (ux*cx + uy*cy + uz*cz - ux*ax - uy*ay - uz*az)/(ux*ux + uy*uy + uz*uz)   
    tx = ax + k * ux 
    ty = ay + k * uy
    tz = az + k * uz
    T = Vector(tx, ty, tz)
    vx, vy, vz = tx - cx, ty - cy, tz - cz
    V = Vector(vx, vy, vz)
    distance = math.sqrt(V.dot(V))
#    Tprime = T + V
    if info == 1:
        msgCsl("Intersection Point at distance of " +
                    str(distance) + " is : " + format(T))
    return T #, distance, Tprime

def plot_2LinesPoint(edge1, edge2):
	""" Point(s)=(Line(s),Line(s)):
	Plot one or two Point(s) at minimum distance of two Lines
	Create a unique Point at intersection of 2 crossing Lines.

	First
	- Select two or more Line/Edge(s) and
	- Then Click on the button

	Plot the point A on the first Line given and the point  B on the second Line.
	The Vector AB perpendicular to the first and second Line.

	"""
	msg=verbose 
#	msg=1

	error_msg = """Unable to create (Line,Line) Intersection(s) :
	First
	- Select two or more Line/Edge(s) and
	- Then Click on the button
	but at least select two different Lines !"""
	result_msg = " : (Line,Line) Intersection(s) are created !"

	try:
		Edge_List = [edge1, edge2]
		Number_of_Edges = len(Edge_List)
		if msg != 0:        
			msgCsl("Number_of_Edges=" + str(Number_of_Edges))        

		if Number_of_Edges >= 2:
			for i in range( Number_of_Edges -1 ):
				f1 = Edge_List[i]
				f2 = Edge_List[i+1]
				#msgCsl(str(f1))
				#msgCsl(str(f2))
				d = f1.distToShape(f2)
				msgCsl(str(d))
				Distance = d[0]
				Vector_A = d[1][0][0]
				#print_point(Vector_A,"Vector_A is : ")
#				Vector_B = d[1][0][1]
				if abs(Distance) <= 1.e-14: 
#					Center_User_Name = plot_point(Vector_A, part, name, str(m_dir))
					msgCsl(str(Vector_A) + result_msg )
					return Vector_A
				else:
#					Center_User_Name = plot_point(Vector_A, part, name, str(m_dir))
#					print_point(Vector_A,str(Center_User_Name) + result_msg + " at :")
#					Center_User_Name = plot_point(Vector_B, part, name, str(m_dir))
#					print_point(Vector_B,str(Center_User_Name) + result_msg + " at :")
					msgCsl(" Distance between the points is : " + str(Distance))
		else:
			msgCsl(error_msg)

	except:
		msgCsl(error_msg)

def DeleteLoop(wire):
	if len(wire.Points) > 3:
#		start = wire.Points[0]
		nbpts = len(wire.Points)
#		end = wire.Points[nbpts - 1]
		i = 0
		j = 0
		test = True
		beginpts = []
		endpts = []
		turn = True
		while i + 1 < nbpts - j - 2 and test:
			start = wire.Points[i]
			beginpts.append(start)
			end = wire.Points[nbpts - j - 1]
			endpts.append(end)
			starti = wire.Points[i + 1]
			endi = wire.Points[nbpts - j - 2]
			mid = middle(starti, endi)
#			msgCsl("start: " + format(start) + " mid: " + format(mid) + " end: " + format(end))
			midp = intersecPerpendicularLine(start, end, mid)
#			msgCsl("starti: " + format(starti) + " midp: " + format(midp) + " endi: " + format(endi))
			startip = intersecPerpendicularLine(start, end, starti)
#			msgCsl("startip: " + format(startip))
#			msgCsl("i: " + str(i) + " j: " + str(j))
			msgCsl(str(PtsToVec(start, midp).dot(PtsToVec(midp, startip))))
			if PtsToVec(start, midp).dot(PtsToVec(midp, startip)) > 0:
#				msgCsl(str(plot_2LinesPoint(wire.Shape.Edges[i], wire.Shape.Edges[nbpts - j - 1])))
				pt = plot_2LinesPoint(wire.Shape.Edges[i], wire.Shape.Edges[nbpts - j - 2])
				if pt != None:
					beginpts.append(pt)
					test = False
			if turn:
				turn = False
				i += 1
			else:
				turn = True
				j += 1
		if not test:
			pts = []
			for pt in beginpts:
				pts.append(pt)
			for i in range(len(endpts) - 1, -1, -1):
				pts.append(endpts[i])
			wire.Points = pts

def getVec(vector):
	return Vector(vector[0], vector[1], vector[2])

def setVec(Vector):
	return [Vector.x, Vector.y, Vector.z]

def setPointCoord(pointobj, vector):
	''' set Draft Point coordinates to the vector values '''
	pointobj.X = vector.x
	pointobj.Y = vector.y
	pointobj.Z = vector.z
