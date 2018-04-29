import os, sys
sys.path.append("/usr/lib/freecad/lib/")
import WingDial
import FreeCADGui, FreeCAD
from PySide import QtCore, QtGui
from WingLib import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

__dir__ = os.path.dirname(__file__)
global iconPath
iconPath = __dir__ + '/Icons/'
global myDialog
myDialog = None

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
		
		for m_key, m_val in self.connections_for_button_clicked.items():
			#msgCsl( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("clicked()"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_slider_changed.items():
			#msgCsl( "Connecting : " + str(getattr(self.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(int)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_doubleSpin_changed.items():
			#msgCsl( "Connecting : " + str(getattr(self.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(double)"),getattr(self, str(m_val)))
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
				max = wobj.SlicedObject.Shape.BoundBox.ZLength
				self.widget.ui.Section_doubleSpinBox.setMaximum(max)
				self.widget.ui.Section_horizontalSlider.setMaximum(int(max))
				self.widget.ui.Section_doubleSpinBox.setValue(wobj.Offset)
				self.SectionDbleSpin()

	def SectionApply(self):
		if hasattr(self, "SectionObj"):
			self.SectionObj.Offset = self.widget.ui.Section_doubleSpinBox.value()
			FreeCAD.ActiveDocument.recompute()

	def SectionSlider(self, value):
		if hasattr(self, "SectionObj"):
			newvalue = float(value) + float(self.widget.ui.Section_dial.value()) / 100.0
			self.SectionObj.Proxy.updatePlane(self.SectionObj, newvalue) # * self.maxValue / 100)
			self.widget.ui.Section_doubleSpinBox.setValue(newvalue) # * self.maxValue / 100)

	def SectionDial(self, value):
		if hasattr(self, "SectionObj"):
			newvalue = float(self.widget.ui.Section_horizontalSlider.value()) + float(value) / 100.0
#			msgCsl("Section dial newvalue: " + str(newvalue))
			self.SectionObj.Proxy.updatePlane(self.SectionObj, newvalue) # * self.maxValue / 100)
			self.widget.ui.Section_doubleSpinBox.setValue(newvalue) # * self.maxValue / 100)

	def SectionDbleSpin(self, value):
		if hasattr(self, "SectionObj"):
			self.SectionObj.Proxy.updatePlane(self.SectionObj, value)
			self.widget.ui.Section_horizontalSlider.setValue(value)
			fract = int((round(value,2) - int(value))*100)
			self.widget.ui.Section_dial.setValue(fract)
			
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
		if hasattr(self, "CutWireObj"):
			self.updateDbleSpin(self.widget.ui.CutWire_doubleSpinBox_start, self.widget.ui.CutWire_horizontalSlider_start, self.widget.ui.CutWire_dial_start)
			self.CutWireDbleSpinBoxStart()

	def CutWireSliderDialEnd(self):
		if hasattr(self, "CutWireObj"):
			self.updateDbleSpin(self.widget.ui.CutWire_doubleSpinBox_end, self.widget.ui.CutWire_horizontalSlider_end, self.widget.ui.CutWire_dial_end)
			self.CutWireDbleSpinBoxEnd()

	def CutWireDbleSpinBoxStart(self):
		if hasattr(self, "CutWireObj"):
			startvalue = self.widget.ui.CutWire_doubleSpinBox_start.value()
			endvalue = self.widget.ui.CutWire_doubleSpinBox_end.value()
			max = self.widget.ui.CutWire_doubleSpinBox_end.maximum()
			gap = self.widget.ui.CutWire_doubleSpinBox_gap.value()
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

	def CutWireDbleSpinBoxEnd(self):
		if hasattr(self, "CutWireObj"):
			startvalue = self.widget.ui.CutWire_doubleSpinBox_start.value()
			endvalue = self.widget.ui.CutWire_doubleSpinBox_end.value()
			gap = self.widget.ui.CutWire_doubleSpinBox_gap.value()
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


#myDialog = WingDialog()

class CommandWingDialog:
	"""Dislay a wing toolkit dialog to modify objects"""
	
	def GetResources(self):
		msgCsl("Getting resources\n")
		icon = os.path.join( iconPath , 'WingDial.svg')
		return {'Pixmap'  : icon , # the name of a svg file available in the resources
			'MenuText': "Wing toolkit dialog" ,
			'ToolTip' : "Open a dialog to modify wing parts"}

	def Activated(self):
		global myDialog
		if myDialog == None:
			msgCsl("creating dialog")
			myDialog = WingDialog()
			myDialog.widget.show()
		elif myDialog.widget.isHidden():
			myDialog.widget.show()
		else:
			myDialog.widget.hide()
		return

	def IsActive(self):
		return True

#FreeCADGui.addCommand("WingDialog", CommandWingDialog())

#def showWingDialog():
#	if myDialog.isHidden():
#		myDialog.show()
#	else:
#		myDialog.hide()
#	return

#if __name__ == '__main__':
#    myDialog = SectionDialog()
