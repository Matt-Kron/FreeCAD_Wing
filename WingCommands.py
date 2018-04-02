import FreeCAD, FreeCADGui
import Nervures, math

def createNervures():
#	DOC = FreeCAD.ActiveDocument.Name
#	NB_NERVURES = 10
#	ECARTEMENT_NERVURE = 50
#	OBJ = "Loft"
#	NOM_SECTION = "Nervure_"
#	Longueur = 2.00
#	ANGLE = 1.14  # en degres
#	Normale = FreeCAD.Base.Vector(0,math.sin(ANGLE/180.00*math.pi),math.cos(ANGLE/180.00*math.pi))

#	Nervures.Sections(DOC,OBJ,NB_NERVURES,ECARTEMENT_NERVURE,NOM_SECTION,Normale)
#	Nervures.Extruder(DOC,OBJ,NB_NERVURES,NOM_SECTION,Normale,Longueur)
	a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Nervures")
	Nervures.Nervures(a)
	a.SlicedObject = FreeCAD.ActiveDocument.Wing
	Nervures.ViewProviderNervures(a.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	FreeCADGui.SendMsgToActiveView("ViewFit")
	
