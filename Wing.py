import os, re
from PySide import QtCore, QtGui
import FreeCAD, FreeCADGui, Part, Draft
from pivy import coin

ModeVerbose = True

if open.__module__ == '__builtin__':
	pythonopen = open

def msgCsl(message):
	if ModeVerbose:
		FreeCAD.Console.PrintMessage(message) # +"\n")

def FileProfil():
	# PySide returns a tuple (filename, filter) instead of just a string like in PyQt
	FileProfil, filefilter = QtGui.QFileDialog.getOpenFileName(QtGui.qApp.activeWindow(),'Open An Airfoil File',FreeCAD.ConfigGet("UserHomePath"),'*.dat')
#	if ModeVerbose:
	msgCsl(FileProfil+"\n")
	return  FileProfil

def NomFichier(filename):
	NomFichier = os.path.basename(filename)
#	_,NomFichier = os.path.split(filename)
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
	airfoilname = afile.readline().strip()
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

class Aile:
	def __init__(self, obj):
		msgCsl("class Aile, __init__" + "\n")
		#############################
		# Wing properties creation
		#############################
		obj.addProperty("App::PropertyFile","FichierEmplanture","Aile","Profil de l'emplanture").FichierEmplanture = FileProfil()
		obj.addProperty("App::PropertyFile","FichierSaumon","Aile","Profil du saumon").FichierSaumon = FileProfil()
		obj.addProperty("App::PropertyLength","EchelleSaumon", "Aile","Echelle saumon, soit la longueur du saumon").EchelleSaumon = 150.0
		obj.addProperty("App::PropertyLength","EchelleEmplanture", "Aile","Echelle emplanture, soit la longueur de l'emplanture").EchelleEmplanture = 300.0
		obj.addProperty("App::PropertyLength","Longueur", "Aile","Longueur de l'aile").Longueur = 500.0
		obj.addProperty("App::PropertyVectorList","points_saumon","Aile","Points du saumon")
		obj.addProperty("App::PropertyVectorList","points_emplanture","Aile","Points de l'emplanture")
		obj.Proxy = self

		#############################
		# Dwire creation
		#############################
		points=[]
		points = getPoints(obj.FichierSaumon)
		e = obj.getPropertyByName("EchelleSaumon")
		for p in points:
			p.x = p.x * e
			p.y = p.y * e
			p.z = obj.Longueur
		obj.points_saumon = points
		saumonP = Part.makePolygon(obj.points_saumon, True)
		saumon = Draft.makeWire(saumonP,True,False)
		saumon.Label = "Saumon"
		points=[]
		points = getPoints(obj.FichierEmplanture)
		e = obj.getPropertyByName("EchelleEmplanture")
		for p in points:
			p.x = p.x * e
			p.y = p.y * e
		obj.points_emplanture = points
		emplantureP = Part.makePolygon(obj.points_emplanture, True)
		emplanture = Draft.makeWire(emplantureP,True,False)
		emplanture.Label = "Emplanture"
		obj.addProperty("App::PropertyString","WireSaumon","Aile","Saumon de l'aile").WireSaumon = saumon.Name
		obj.addProperty("App::PropertyString","WireEmplanture","Aile","Emplanture de l'aile").WireEmplanture = emplanture.Name
		#############################
		# Wing's loft creation
		#############################
		AileBis = FreeCAD.ActiveDocument.addObject('Part::Loft','Loft')
		AileBis.Label = "Loft_Aile"
		obj.addProperty("App::PropertyString","NomLoft","Aile","Nom du lissage lie a l'aile").NomLoft = AileBis.Name
		AileBis.Sections = [FreeCAD.ActiveDocument.getObject(emplanture.Name),FreeCAD.ActiveDocument.getObject(saumon.Name)]
		AileBis.Solid = True
		AileBis.Ruled = False		
				
	def onChanged(self, fp, prop):
        # Do something when a property has changed
        	msgCsl("Change property: " + str(prop) + "\n")
		if prop == "FichierEmplanture":
			fp.points_emplanture = getPoints(fp.FichierEmplanture)
			self.updateWire(fp,fp.WireEmplanture,"points_emplanture","EchelleEmplanture")
		if prop == "FichierSaumon":
			fp.points_saumon= getPoints(fp.getPropertyByName("FichierSaumon"))
			self.updateWire(fp,fp.WireSaumon,"points_saumon","EchelleSaumon")
		if prop == "EchelleEmplanture":
			self.updateWire(fp,fp.WireEmplanture,"points_emplanture","EchelleEmplanture")
		if prop == "EchelleSaumon":
			self.updateWire(fp,fp.WireSaumon,"points_saumon","EchelleSaumon")
		if prop == "Longueur":
			self.updateWire(fp,fp.WireSaumon,"points_saumon","EchelleSaumon")			
				
	def execute(self, fp):
		msgCsl("class Aile, execute" + "\n")
		
	def updateWire(self, fp, oWire, fWire, Echelle):
		msgCsl("class Aile, updateWire, " + str(fWire) + "\n")
		oW = FreeCAD.ActiveDocument.getObject(oWire)
		eW = FreeCAD.ActiveDocument.getObject(fp.WireEmplanture)
		fW = fp.getPropertyByName(fWire)
		e = fp.getPropertyByName(Echelle)
		z = 0.0
		if fWire == "points_saumon" : z = fp.Longueur
		mPosition = FreeCAD.Vector(0,0,z)
		mRotation = FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0)
		mCenter = FreeCAD.Vector(0,0,1)
		mPlacement = FreeCAD.Placement(mPosition,mRotation,mCenter)
		mPlacement = eW.Placement.multiply(mPlacement)
		oW.Placement = mPlacement
		pts = []
		#pts = getPoints(fp.getPropertyByName(FichierProfil))
		for p in fW:
			pts.append(FreeCAD.Vector(p.x * e,p.y * e, 0))
		oW.Points = pts
		Gui.SendMsgToActiveView("ViewFit")

