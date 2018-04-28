import os, sys
sys.path.append("/usr/lib/freecad/lib/")
import WingDial
import FreeCADGui, FreeCAD
from PySide import QtCore, QtGui
from WingLib import msgCsl

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
#		self.frame = QtGui.QWidget() # create a new dckwidget
#		msgCsl("QDockWidget created")
#		self.frame.ui = WingSlider.Ui_Form() # load the Ui script
		self.widget.ui = WingDial.Ui_DockWidget() # load the Ui script
#		msgCsl("Ui_Form created")
		self.widget.ui.setupUi(self.widget) # setup the ui
#		msgCsl("Ui_Form set up")
		self.widget.setFeatures( QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetClosable )
#		self.widget.setWidget(self.frame)
		FCmw.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget) # add the widget to the main window
#		msgCsl("QDockWidget added")
#		self.widget.setFloating(True)
		self.widget.hide()
#		self.widget.ui.horizontalSlider_value.setMaximum(600)
		
		self.connections_for_button_clicked = { 
							"Close_button"					: "Close", 
							"Section_button_select_object"	: "SectionSelectObject", 
							"Section_button_apply"			: "SectionApply", 
							"Section_button_reset"			: "SectionReset"}
		self.connections_for_slider_changed = {
							"Section_horizontalSlider"		: "SectionSlider", 
							"Section_dial"					: "SectionDial"}
							
#		self.connections_for_text_changed = {
#							"object_value"					: "ValueText"}
		self.connections_for_doubleSpin_changed = {
							"Section_doubleSpinBox"			: "SectionDbleSpin"}
		for m_key, m_val in self.connections_for_button_clicked.items():
			#print_msg( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("clicked()"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_slider_changed.items():
			#print_msg( "Connecting : " + str(getattr(self.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(int)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_doubleSpin_changed.items():
			#print_msg( "Connecting : " + str(getattr(self.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(double)"),getattr(self, str(m_val)))
#		for m_key, m_val in self.connections_for_text_changed.items():
#			#print_msg( "Connecting : " + str(m_key) + " and " + str(m_val) )
#			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL(_fromUtf8("textChanged(QString)")),getattr(self, str(m_val)))   

	def Close(self):
		self.widget.hide()
		return None
		
	def SectionSelectObject(self):
		sel = FreeCADGui.Selection.getSelectionEx()
		if len(sel) > 0:
#			msgCsl("Wing found for linking Rod")
			wobj = sel[0].Object
			if wobj.Proxy.__class__.__name__ == "Section":
				msgCsl("Section object found")
				self.obj = wobj
				self.widget.ui.Section_info_selected_object.setText(wobj.Label + "(" + wobj.Name + ")")
				msgCsl("object bounbox ZLength: " + str(wobj.SlicedObject.Shape.BoundBox.ZLength))
#				self.widget.ui.object_value.setText(str(self.obj.Offset))
#				self.maxValue = wobj.SlicedObject.Shape.BoundBox.ZLength
				max = wobj.SlicedObject.Shape.BoundBox.ZLength
				self.widget.ui.Section_doubleSpinBox.setMaximum(max)
				self.widget.ui.Section_horizontalSlider.setMaximum(int(max))
				self.widget.ui.Section_doubleSpinBox.setValue(self.obj.Offset)
				self.SectionDbleSpin()

	def SectionApply(self):
		if hasattr(self, "obj"):
#			value = float(self.widget.ui.object_value.text())
			self.obj.Offset = self.widget.ui.Section_doubleSpinBox.value()
			FreeCAD.ActiveDocument.recompute()

	def SectionSlider(self, value):
		# If the value was changed internally, ignore event.
		if self.internal:
			return
		if hasattr(self, "obj"):
			self.obj.Proxy.updatePlane(self.obj, value) # * self.maxValue / 100)
#			self.widget.ui.object_value.setText(str(value))
			self.widget.ui.Section_doubleSpinBox.setValue(value) # * self.maxValue / 100)

	def SectionDial(self, value):
		# If the value was changed internally, ignore event.
		if self.internal:
			return
		if hasattr(self, "obj"):
			newvalue = float(int(self.widget.ui.Section_doubleSpinBox.value())) + float(value) / 100.0
#			msgCsl("Section dial newvalue: " + str(newvalue))
			self.obj.Proxy.updatePlane(self.obj, newvalue) # * self.maxValue / 100)
#			self.widget.ui.object_value.setText(str(value))
			self.widget.ui.Section_doubleSpinBox.setValue(newvalue) # * self.maxValue / 100)

	def SectionDbleSpin(self, value):
		if hasattr(self, "obj"):
			# Update the slider by internal update
#			value = self.widget.ui.Section_doubleSpinBox.value()
			self.obj.Proxy.updatePlane(self.obj, value)
			self.internal = True
			self.widget.ui.Section_horizontalSlider.setValue(value) # * 100 / self.maxValue))
			fract = int((round(value,2) - int(value))*100)
			self.widget.ui.Section_dial.setValue(fract)
			self.internal = False
			
	def SectionReset(self):
#		self.widget.ui.Section_info_selected_object.setText("")
#		self.widget.ui.Section_doubleSpinBox.setValue(0)
#		self.widget.ui.Section_horizontalSlider.setValue(0)
		if hasattr(self, "obj"):
			self.widget.ui.Section_doubleSpinBox.setValue(self.obj.Offset)
			self.SectionDbleSpin()

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
