import os, sys
sys.path.append("/usr/lib/freecad/lib/")
import WingDial, SectionsDial
import FreeCADGui, FreeCAD
from PySide import QtCore, QtGui
from WingLib import *
from Wing import Section, ViewProviderSection

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

__dir__ = os.path.dirname(__file__)
global iconPath
iconPath = __dir__ + '/Icons/'
global myDialog
myDialog = None
global mySectionsDialog
mySectionsDialog = None

# use "icons" as prefix which we used in the .ui file  
QtCore.QDir.addSearchPath("icons", iconPath) 

class WingDialog():
	def __init__(self):
		self.internal = False
		
		FCmw = FreeCADGui.getMainWindow()
		self.widget = QtGui.QDockWidget() # create a new dckwidget
		self.widget.ui = WingDial.Ui_DockWidget() # load the Ui script
		self.widget.ui.setupUi(self.widget) # setup the ui
		self.widget.setFeatures( QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetClosable )
		FCmw.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget) # add the widget to the main window
		self.widget.hide()
		
		self.connections_for_button_clicked = { 
							"Close_button"					: "Close",
							
							"CutWire_button_apply"			: "CutWire_button_apply",
							"CutWire_button_reset"			: "CutWire_button_reset",
							"CutWire_button_select_object"	: "CutWire_button_select_object",
							
							"Section_button_select_object"	: "SectionSelectObject", 
							"Section_button_apply"			: "SectionApply", 
							"Section_button_reset"			: "SectionReset"}
		self.connections_for_slider_changed = {
							"Section_horizontalSlider"		: "SectionSlider", 
							"Section_dial"					: "SectionDial",
							
							"CutWire_dial_end"				: "CutWireSliderDialEnd",
							"CutWire_dial_start"			: "CutWireSliderDialStart",
							"CutWire_horizontalSlider_end"	: "CutWireSliderDialEnd",
							"CutWire_horizontalSlider_start": "CutWireSliderDialStart"}
#		self.connections_for_text_changed = {
#							"object_value"					: "ValueText"}
		self.connections_for_doubleSpin_changed = {
							"Section_doubleSpinBox"			: "SectionDbleSpin", 
							
							"CutWire_doubleSpinBox_end"		: "CutWireDbleSpinBoxEnd",
							"CutWire_doubleSpinBox_start"	: "CutWireDbleSpinBoxStart"}
#		self.connections_for_combobox_changed = {
#							"CutWire_comboBox"				: "CutWire_comboBox"}
		self.connections_for_radiobutton_clicked = {
							"Section_radioButton_XY"		: "SectionChangeDirection",
							"Section_radioButton_XZ"		: "SectionChangeDirection",
							"Section_radioButton_YZ"		: "SectionChangeDirection"}
		
		for m_key, m_val in self.connections_for_button_clicked.items():
			#msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("clicked()"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_slider_changed.items():
			#msgCsl( "Connecting : " + str(getattr(self.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(int)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_doubleSpin_changed.items():
			#msgCsl( "Connecting : " + str(getattr(self.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(double)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_radiobutton_clicked.items():
			#print_msg( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL(_fromUtf8("clicked(bool)")),getattr(self, str(m_val)))
#		for m_key, m_val in self.connections_for_combobox_changed.items():
#			#msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )                            
#			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL(_fromUtf8("currentIndexChanged(QString)")),getattr(self, str(m_val)))                      
#		for m_key, m_val in self.connections_for_text_changed.items():
#			#msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
#			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL(_fromUtf8("textChanged(QString)")),getattr(self, str(m_val)))   

	def Close(self):
		self.widget.hide()
		return None

	def updateSliderDial(self, value, slider, dial):
		slider.setValue(int(value))
		fract = int((round(value,2) - int(value))*100)
		dial.setValue(fract)

	def updateDbleSpin(self, dblespin, slider, dial):
		dblespin.setValue(float(slider.value()) + float(dial.value()) / 100.0)
		
	def SectionSelectObject(self):
		sl = FreeCADGui.Selection.getSelectionEx()
		if len(sl) > 0:
			wobj = sl[0].Object
			if wobj.Proxy.__class__.__name__ == "Section":
				msgCsl("Section object found")
				self.SectionObj = wobj
				self.widget.ui.Section_info_selected_object.setText(wobj.Label + "(" + wobj.Name + ")")
				self.SectionUpdateParam()
				self.SectionDbleSpin()

	def SectionUpdateParam(self):
		if self.SectionObj.RefPlane == "XY": self.widget.ui.Section_radioButton_XY.setChecked(True)
		if self.SectionObj.RefPlane == "XZ": self.widget.ui.Section_radioButton_XZ.setChecked(True)
		if self.SectionObj.RefPlane == "YZ": self.widget.ui.Section_radioButton_YZ.setChecked(True)
		if self.widget.ui.Section_radioButton_XY.isChecked():
			max = self.SectionObj.SlicedObject.Shape.BoundBox.ZLength
		elif self.widget.ui.Section_radioButton_XZ.isChecked():
			max = self.SectionObj.SlicedObject.Shape.BoundBox.YLength
		elif self.widget.ui.Section_radioButton_YZ.isChecked():
			max = self.SectionObj.SlicedObject.Shape.BoundBox.XLength
		self.widget.ui.Section_doubleSpinBox.setMaximum(max)
		self.widget.ui.Section_horizontalSlider.setMaximum(int(max))
		self.widget.ui.Section_doubleSpinBox.setValue(self.SectionObj.Offset)

	def SectionChangeDirection(self):
		if self.widget.ui.Section_radioButton_XY.isChecked():
			self.SectionObj.RefPlane = "XY"
		elif self.widget.ui.Section_radioButton_XZ.isChecked():
			self.SectionObj.RefPlane = "XZ"
		elif self.widget.ui.Section_radioButton_YZ.isChecked():
			self.SectionObj.RefPlane = "YZ"
		self.SectionUpdateParam()
		FreeCAD.ActiveDocument.recompute()

	def SectionApply(self):
		if hasattr(self, "SectionObj"):
			self.SectionObj.Offset = self.widget.ui.Section_doubleSpinBox.value()
			FreeCAD.ActiveDocument.recompute()

	def SectionSlider(self, value):
		if self.internal: return
		if hasattr(self, "SectionObj"):
			newvalue = float(value) + float(self.widget.ui.Section_dial.value()) / 100.0
			self.SectionObj.Proxy.updatePlane(self.SectionObj, newvalue) # * self.maxValue / 100)
			self.widget.ui.Section_doubleSpinBox.setValue(newvalue) # * self.maxValue / 100)

	def SectionDial(self, value):
		if self.internal: return
		if hasattr(self, "SectionObj"):
			newvalue = float(self.widget.ui.Section_horizontalSlider.value()) + float(value) / 100.0
#			msgCsl("Section dial newvalue: " + str(newvalue))
			self.SectionObj.Proxy.updatePlane(self.SectionObj, newvalue) # * self.maxValue / 100)
			self.widget.ui.Section_doubleSpinBox.setValue(newvalue) # * self.maxValue / 100)

	def SectionDbleSpin(self, value):
		if hasattr(self, "SectionObj"):
			self.SectionObj.Proxy.updatePlane(self.SectionObj, value)
			self.internal = True
			self.widget.ui.Section_horizontalSlider.setValue(value)
			fract = int((round(value,2) - int(value))*100)
			self.widget.ui.Section_dial.setValue(fract)
			self.internal = False
			
	def SectionReset(self):
		if hasattr(self, "SectionObj"):
			self.widget.ui.Section_doubleSpinBox.setValue(self.SectionObj.Offset)
			self.SectionDbleSpin()

	def CutWire_button_select_object(self):
		sl = FreeCADGui.Selection.getSelectionEx()
		if len(sl) > 0:
			wobj = sl[0].Object
			if wobj.Proxy.__class__.__name__ == "CutWire":
				msgCsl("CutWire object found")
				self.CutWireObj = wobj
				self.widget.ui.CutWire_info_selected_object.setText(wobj.Label + "(" + wobj.Name + ")")
				max = len(wobj.Wire.Points)
				self.widget.ui.CutWire_doubleSpinBox_start.setMaximum(max)
				self.widget.ui.CutWire_horizontalSlider_start.setMaximum(int(max))
				self.widget.ui.CutWire_doubleSpinBox_end.setMaximum(max)
				self.widget.ui.CutWire_horizontalSlider_end.setMaximum(int(max))
				self.widget.ui.CutWire_doubleSpinBox_start.setValue(wobj.StartPoint)
				self.widget.ui.CutWire_doubleSpinBox_end.setValue(wobj.EndPoint)
				self.widget.ui.CutWire_doubleSpinBox_gap.setValue(max(wobj.EndPoint - wobj.StartPoint, 0.0))
				self.widget.ui.CutWire_comboBox.setCurrentIndex(self.widget.ui.CutWire_comboBox.findText(wobj.CutType))
				self.CutWire_doubleSpinBox()

	def CutWireUpdatePoints(self):
		'''update the position of the cutting points in the FreeCAD view'''
		value = self.widget.ui.CutWire_doubleSpinBox_start.value()
		setPointCoord(self.CutWireObj.StartPointObj, DiscretizedPoint(self.CutWireObj.Wire, value))
		value = self.widget.ui.CutWire_doubleSpinBox_end.value()
		setPointCoord(self.CutWireObj.EndPointObj, DiscretizedPoint(self.CutWireObj.Wire, value))
		FreeCAD.ActiveDocument.recompute()

	def CutWire_button_apply(self):
		if hasattr(self, "CutWireObj"):
			self.CutWireObj.StartPoint = self.widget.ui.CutWire_doubleSpinBox_start.value()
			self.CutWireObj.EndPoint = self.widget.ui.CutWire_doubleSpinBox_end.value()
			self.CutWireObj.CutType = self.widget.ui.CutWire_comboBox.currentText()
			FreeCAD.ActiveDocument.recompute()

	def CutWireUpdateDbleSpin(self):
		if hasattr(self, "CutWireObj"):
			self.updateDbleSpin(self.widget.ui.CutWire_doubleSpinBox_start, self.widget.ui.CutWire_horizontalSlider_start, self.widget.ui.CutWire_dial_start)
			self.updateDbleSpin(self.widget.ui.CutWire_doubleSpinBox_end, self.widget.ui.CutWire_horizontalSlider_end, self.widget.ui.CutWire_dial_end)

	def CutWireSliderDialStart(self):
		if self.internal: return
		if hasattr(self, "CutWireObj"):
			self.updateDbleSpin(self.widget.ui.CutWire_doubleSpinBox_start, self.widget.ui.CutWire_horizontalSlider_start, self.widget.ui.CutWire_dial_start)
			self.CutWireDbleSpinBoxStart()

	def CutWireSliderDialEnd(self):
		if self.internal: return
		if hasattr(self, "CutWireObj"):
			self.updateDbleSpin(self.widget.ui.CutWire_doubleSpinBox_end, self.widget.ui.CutWire_horizontalSlider_end, self.widget.ui.CutWire_dial_end)
			self.CutWireDbleSpinBoxEnd()

	def CutWireDbleSpinBoxStart(self):
		if hasattr(self, "CutWireObj"):
			startvalue = self.widget.ui.CutWire_doubleSpinBox_start.value()
			endvalue = self.widget.ui.CutWire_doubleSpinBox_end.value()
			max = self.widget.ui.CutWire_doubleSpinBox_end.maximum()
			gap = self.widget.ui.CutWire_doubleSpinBox_gap.value()
			self.internal = True
			if self.widget.ui.CutWire_CheckBox_gap.isChecked():
				if (startvalue + gap) > max:
					return
				else:
					self.widget.ui.CutWire_doubleSpinBox_end.setValue(startvalue + gap)
			else:
				if startvalue >= endvalue:
					self.widget.ui.CutWire_doubleSpinBox_end.setValue(min(startvalue + 1, self.widget.ui.CutWire_doubleSpinBox_end.maximum()))
				self.widget.ui.CutWire_doubleSpinBox_gap.setValue(self.widget.ui.CutWire_doubleSpinBox_end.value() - startvalue)
			self.CutWireSpinBox2()
			self.internal = False

	def CutWireDbleSpinBoxEnd(self):
		if hasattr(self, "CutWireObj"):
			startvalue = self.widget.ui.CutWire_doubleSpinBox_start.value()
			endvalue = self.widget.ui.CutWire_doubleSpinBox_end.value()
			gap = self.widget.ui.CutWire_doubleSpinBox_gap.value()
			self.internal = True
			if self.widget.ui.CutWire_CheckBox_gap.isChecked():
				if (endvalue - gap) < 0:
					return
				else:
					self.widget.ui.CutWire_doubleSpinBox_start.setValue(endvalue - gap)
			else:
				if startvalue >= endvalue:
					self.widget.ui.CutWire_doubleSpinBox_start.setValue(max(endvalue - 1, 0))
				self.widget.ui.CutWire_doubleSpinBox_gap.setValue(endvalue - self.widget.ui.CutWire_doubleSpinBox_start.value())
			self.CutWireSpinBox2()
			self.internal = False

	def CutWireSpinBox2(self):
		if hasattr(self, "CutWireObj"):
			self.CutWireUpdatePoints()
			self.updateSliderDial(self.widget.ui.CutWire_doubleSpinBox_start.value(), self.widget.ui.CutWire_horizontalSlider_start, self.widget.ui.CutWire_dial_start)
			self.updateSliderDial(self.widget.ui.CutWire_doubleSpinBox_end.value(), self.widget.ui.CutWire_horizontalSlider_end, self.widget.ui.CutWire_dial_end)

	def CutWire_button_reset(self):
		if hasattr(self, "CutWireObj"):
			self.widget.ui.CutWire_doubleSpinBox_gap.setValue(max(self.CutWireObj.EndPoint - self.CutWireObj.StartPoint, 0.0))
			self.widget.ui.CutWire_doubleSpinBox_start.setValue(self.CutWireObj.StartPoint)
			self.widget.ui.CutWire_doubleSpinBox_end.setValue(self.CutWireObj.EndPoint)
			self.widget.ui.CutWire_comboBox.setCurrentIndex(self.widget.ui.CutWire_comboBox.findText(self.CutWireObj.CutType))



class CommandWingDialog:
	"""Display a wing toolkit dialog to modify objects"""
	
	def GetResources(self):
		icon = os.path.join( iconPath , 'WingDial.svg')
		return {'Pixmap'  : icon , # the name of a svg file available in the resources
			'MenuText': "Wing toolkit dialog" ,
			'ToolTip' : "Open a dialog to modify wing parts"}

	def Activated(self):
		global myDialog
		if myDialog == None:
			msgCsl("Creating wing toolkit dialog")
			myDialog = WingDialog()
			myDialog.widget.show()
		elif myDialog.widget.isHidden():
			myDialog.widget.show()
		else:
			myDialog.widget.hide()
		return

	def IsActive(self):
		return True

class SectionsDialog():
	
	def __init__(self):
		self.internal = False		
		self.bboxOrigin = VecNul
		self.bboxAxisZ = VecNul
		self.bboxAxisY = VecNul
		self.bboxAxisX = VecNul
		self.planeToX = VecNul
		self.planeToNormal = VecNul
		self.planeLength = 0.0
		self.planeWidth = 0.0
		self.bboxLength = 0.0
		self.bboxXlength = 0.0
		self.bboxYlength = 0.0
		self.bboxZlength = 0.0
		self.placement = FreeCAD.Placement()
		self.maxDist = 0.0
		self.PlanesList = []
		self.obj = None
		
		FCmw = FreeCADGui.getMainWindow()
		self.widget = QtGui.QDockWidget() # create a new dckwidget
		self.widget.ui = SectionsDial.Ui_Sections_DockWidget() # load the Ui script
		self.widget.ui.setupUi(self.widget) # setup the ui
		self.widget.setFeatures( QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetClosable )
		FCmw.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget) # add the widget to the main window
		self.widget.hide()
		
		self.connections_for_button_clicked = { 
							"SectionsDial_button_select_object"			: "SectionsDial_button_select_object",
							"SectionsDial_button_OK"					: "SectionsDial_button_OK"}
		self.connections_for_spin_changed = {
							"SectionsDial_spinBox_Number"				: "SectionsDial_spinBox_Number"}
		self.connections_for_radiobutton_clicked = {
							"SectionsDial_radioButton_XY"				: "calculateParam",
							"SectionsDial_radioButton_XZ"				: "calculateParam",
							"SectionsDial_radioButton_YZ"				: "calculateParam"}
		self.connections_for_doubleSpin_changed = {
							"SectionsDial_doubleSpinBox_StartOffset"	: "SectionsDial_doubleSpinBox_StartOffset",
							"SectionsDial_doubleSpinBox_Distance"		: "SectionsDial_doubleSpinBox_Distance"}
#		self.connections_for_checkbox_toggled = {
#							"SectionsDial_checkBox_Distance"			: "SectionsDial_checkBox_Distance",
#							"SectionsDial_radioButton_Number"			: "SectionsDial_radioButton_Number"}
		self.widget.visibilityChanged.connect(self.Close)
		
		for m_key, m_val in self.connections_for_button_clicked.items():
			#msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("clicked()"),getattr(self, str(m_val)))
#		for m_key, m_val in self.connections_for_slider_changed.items():
#			#msgCsl( "Connecting : " + str(getattr(self.widget.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
#			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(int)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_doubleSpin_changed.items():
			#msgCsl( "Connecting : " + str(getattr(self.widget.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(double)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_spin_changed.items():
			#msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(int)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_radiobutton_clicked.items():
			#print_msg( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL(_fromUtf8("clicked(bool)")),getattr(self, str(m_val)))

		if self.widget.ui.SectionsDial_spinBox_Number.value() == 0: self.widget.ui.SectionsDial_spinBox_Number.setValue(1)
		self.widget.ui.SectionsDial_radioButton_XY.setChecked(True)

	def Close(self, visible):
		if not visible:
			self.obj = None
			self.bboxXlength = 0.0
			self.bboxYlength = 0.0
			self.bboxZlength = 0.0
			self.widget.ui.SectionsDial_doubleSpinBox_Distance.setValue(0.01)
			self.widget.ui.SectionsDial_spinBox_Number.setValue(1)
			self.widget.ui.SectionsDial_doubleSpinBox_StartOffset.setValue(0)
			self.removePlanes()
			self.widget.hide()
#			self.SectionsDial_button_OK()

	def SectionsDial_button_select_object(self):
		sl = FreeCADGui.Selection.getSelectionEx()
		if len(sl) > 0:
			obj = sl[0].Object
			if hasattr(obj, "Shape"):
				if obj.Shape.Volume > 0.001 :
					bbox = obj.Shape.BoundBox
					self.obj = obj
					self.widget.ui.SectionsDial_info_selected_object.setText(obj.Label + "(" + obj.Name + ")")
					self.bboxOrigin = FreeCAD.Vector(bbox.XMin, bbox.YMin, bbox.ZMin)
					self.bboxAxisX = PtsToVec(self.bboxOrigin, FreeCAD.Vector(bbox.XMax, bbox.YMin, bbox.ZMin))
					self.bboxAxisY = PtsToVec(self.bboxOrigin, FreeCAD.Vector(bbox.XMin, bbox.YMax, bbox.ZMin))
					self.bboxAxisZ = PtsToVec(self.bboxOrigin, Vector(bbox.XMin, bbox.YMin, bbox.ZMax))
					self.bboxXlength = bbox.XLength
					self.bboxYlength = bbox.YLength
					self.bboxZlength = bbox.ZLength
					self.calculateParam()
				else:
					usrMsg("The shape is not a volume")

	def calculateParam(self):
		self.removePlanes()
		i = 1
		if self.widget.ui.SectionsDial_radioButton_XY.isChecked():
			msgCsl("radiobutton XY checked")
			self.bboxLength = self.bboxZlength
			self.planeToX = self.bboxAxisX
			self.planeToNormal = self.bboxAxisZ
			self.planeLength = self.bboxXlength
			self.planeWidth = self.bboxYlength
		elif self.widget.ui.SectionsDial_radioButton_XZ.isChecked():
			msgCsl("radiobutton XZ checked")
			self.bboxLength = self.bboxYlength
			self.planeToX = self.bboxAxisX
			self.planeToNormal = self.bboxAxisY
			self.planeLength = self.bboxXlength
			self.planeWidth = self.bboxZlength
			i = -1
		elif self.widget.ui.SectionsDial_radioButton_YZ.isChecked():
			msgCsl("radiobutton YZ checked")
			self.bboxLength = self.bboxXlength
			self.planeToX = self.bboxAxisY
			self.planeToNormal = self.bboxAxisX
			self.planeLength = self.bboxYlength
			self.planeWidth = self.bboxZlength
		mrot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), self.planeToX)
		mplacement = FreeCAD.Placement(VecNul, mrot)
		mrot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, i * 1), self.planeToNormal)
		mplacement = FreeCAD.Placement(self.bboxOrigin, mrot).multiply(mplacement)
		self.placement = mplacement
		distance = self.bboxLength / 10.0
		self.widget.ui.SectionsDial_doubleSpinBox_Distance.setMaximum(self.bboxLength)
		self.widget.ui.SectionsDial_doubleSpinBox_Distance.setValue(distance)
		self.widget.ui.SectionsDial_doubleSpinBox_StartOffset.setMaximum(self.bboxLength)
		self.PlanesUpate()

	def calculateDistance(self):
		if self.widget.ui.SectionsDial_spinBox_Number.value() > 1:
			distance = (self.bboxLength - self.widget.ui.SectionsDial_doubleSpinBox_StartOffset.value()) / (self.widget.ui.SectionsDial_spinBox_Number.value() - 1)
			return distance
		else:
			return self.widget.ui.SectionsDial_doubleSpinBox_Distance.value()

	def calculateNumber(self):
		number = int((self.bboxLength - self.widget.ui.SectionsDial_doubleSpinBox_StartOffset.value())
						/ self.widget.ui.SectionsDial_doubleSpinBox_Distance.value()) + 1
		return number

	def PlanesUpate(self):
		nbplane = len(self.PlanesList)
		while nbplane > self.widget.ui.SectionsDial_spinBox_Number.value():
			if self.PlanesList[nbplane - 1] != None:
				FreeCAD.ActiveDocument.removeObject(self.PlanesList[nbplane - 1].Name)
			self.PlanesList.remove(self.PlanesList[nbplane - 1])
			nbplane = len(self.PlanesList)
		while nbplane < self.widget.ui.SectionsDial_spinBox_Number.value():
			mplane = FreeCAD.ActiveDocument.addObject("Part::Plane","Plane")
			mplane.ViewObject.ShapeColor = (0.33,0.67,1.00)
			mplane.ViewObject.LineColor = (1.00,0.4,0.00)
			mplane.ViewObject.LineWidth = 1.00
			mplane.ViewObject.Transparency = 50
			self.PlanesList.append(mplane)
			nbplane = len(self.PlanesList)
			mplane.Length = self.planeLength
			mplane.Width = self.planeWidth
		distance = self.widget.ui.SectionsDial_doubleSpinBox_Distance.value()
		i = 0
		for mplane in self.PlanesList:
			mplane.Placement = self.placement
			self.planeToNormal.normalize()
#			msgCsl("self.planeToNormal: " + format(self.planeToNormal))
			translation = self.widget.ui.SectionsDial_doubleSpinBox_StartOffset.value() + i * distance
			if translation > 0: mplane.Placement.move(self.planeToNormal.multiply(translation))
			i += 1

	def removePlanes(self):
		nbplane = len(self.PlanesList)
		while nbplane > 0:
			if self.PlanesList[nbplane - 1] != None:
				FreeCAD.ActiveDocument.removeObject(self.PlanesList[nbplane - 1].Name)
			self.PlanesList.remove(self.PlanesList[nbplane - 1])
			nbplane = len(self.PlanesList)

	def SectionsDial_button_OK(self):
		if self.widget.ui.SectionsDial_radioButton_XY.isChecked():
			refplane = "XY"
		elif self.widget.ui.SectionsDial_radioButton_XZ.isChecked():
			refplane = "XZ"
		elif self.widget.ui.SectionsDial_radioButton_YZ.isChecked():
			refplane = "YZ"
		distance = self.widget.ui.SectionsDial_doubleSpinBox_Distance.value()
		offset = self.widget.ui.SectionsDial_doubleSpinBox_StartOffset.value()
		for i in range(0, len(self.PlanesList), +1):
			obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Section")
			Section(obj)  # imported from Wing
			ViewProviderSection(obj.ViewObject, 'Section.svg')  # imported from Wing
			obj.RefPlane = refplane
			obj.Offset = offset + i * distance
			obj.SlicedObject = self.obj
		self.removePlanes()
		self.widget.hide()
		FreeCAD.ActiveDocument.recompute()

	def SectionsDial_spinBox_Number(self, value):
		if self.internal: return
		self.internal = True
		distance = self.calculateDistance()
		if self.widget.ui.SectionsDial_checkBox_Number.isChecked() and self.widget.ui.SectionsDial_checkBox_Distance.isChecked():
			self.widget.ui.SectionsDial_doubleSpinBox_Distance.setValue(distance)
		elif (not self.widget.ui.SectionsDial_checkBox_Number.isChecked()) and self.widget.ui.SectionsDial_checkBox_Distance.isChecked():
			self.widget.ui.SectionsDial_doubleSpinBox_Distance.setValue(distance)
		elif (not self.widget.ui.SectionsDial_checkBox_Number.isChecked()) and (not self.widget.ui.SectionsDial_checkBox_Distance.isChecked()):
			maxNumber = self.calculateNumber()
			if value > maxNumber:
				self.widget.ui.SectionsDial_spinBox_Number.setValue(maxNumber)
		else:
			return
		self.PlanesUpate()
		self.internal = False

	def SectionsDial_doubleSpinBox_StartOffset(self, value):
		if self.internal: return
		distance = self.widget.ui.SectionsDial_doubleSpinBox_Distance.value()
		number = self.widget.ui.SectionsDial_spinBox_Number.value()
		if self.widget.ui.SectionsDial_checkBox_Number.isChecked() and self.widget.ui.SectionsDial_checkBox_Distance.isChecked():
			self.SectionsDial_spinBox_Number(number)
		elif (not self.widget.ui.SectionsDial_checkBox_Number.isChecked()) and self.widget.ui.SectionsDial_checkBox_Distance.isChecked():
			self.SectionsDial_spinBox_Number(number)
		elif self.widget.ui.SectionsDial_checkBox_Number.isChecked() and (not self.widget.ui.SectionsDial_checkBox_Distance.isChecked()):
			self.SectionsDial_doubleSpinBox_Distance(distance)
		else:
#			distance = self.widget.ui.SectionsDial_doubleSpinBox_Distance.value()
#			number = self.widget.ui.SectionsDial_spinBox_Number.value()
			if (value + (number - 1) * distance) > self.bboxLength:
#				self.internal = True
				self.widget.ui.SectionsDial_doubleSpinBox_StartOffset.setValue(self.bboxLength - (number - 1) * distance)
#				self.internal = False
			self.PlanesUpate()

	def SectionsDial_doubleSpinBox_Distance(self, value):
		if self.internal: return
		self.internal = True
		number = self.calculateNumber()
		if self.widget.ui.SectionsDial_checkBox_Number.isChecked() and self.widget.ui.SectionsDial_checkBox_Distance.isChecked():
			self.widget.ui.SectionsDial_spinBox_Number.setValue(number)
		elif self.widget.ui.SectionsDial_checkBox_Number.isChecked() and (not self.widget.ui.SectionsDial_checkBox_Distance.isChecked()):
			self.widget.ui.SectionsDial_spinBox_Number.setValue(number)
		elif (not self.widget.ui.SectionsDial_checkBox_Number.isChecked()) and (not self.widget.ui.SectionsDial_checkBox_Distance.isChecked()):
			distance = self.calculateDistance()
			if value > distance: self.widget.ui.SectionsDial_doubleSpinBox_Distance.setValue(distance)
		else:
			return
		self.PlanesUpate()
		self.internal = False


class CommandSectionsDialog:
	"""Display a dialog to create sections"""
	
	def GetResources(self):
		icon = os.path.join( iconPath , 'Sections.svg')
		return {'Pixmap'  : icon , # the name of a svg file available in the resources
			'MenuText': "Sections dialog" ,
			'ToolTip' : "Open a dialog to create sections"}

	def Activated(self):
		global mySectionsDialog
		if mySectionsDialog == None:
			msgCsl("Creating sections dialog")
			mySectionsDialog = SectionsDialog()
			mySectionsDialog.widget.show()
		elif mySectionsDialog.widget.isHidden():
			mySectionsDialog.widget.show()
		else:
			mySectionsDialog.widget.hide()
		return

	def IsActive(self):
		return True

