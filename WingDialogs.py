import os, sys
sys.path.append("/usr/lib/freecad/lib/")
import WingSlider
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

class WingDialog():
	def __init__(self):
		self.internal = False
		FCmw = FreeCADGui.getMainWindow()

		self.widget = QtGui.QDockWidget() # create a new dckwidget
#		self.frame = QtGui.QWidget() # create a new dckwidget
		msgCsl("QDockWidget created")
#		self.frame.ui = WingSlider.Ui_Form() # load the Ui script
		self.widget.ui = WingSlider.Ui_DockWidget() # load the Ui script
		msgCsl("Ui_Form created")
		self.widget.ui.setupUi(self.widget) # setup the ui
		msgCsl("Ui_Form set up")
		self.widget.setFeatures( QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetClosable )
#		self.widget.setWidget(self.frame)
		FCmw.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget) # add the widget to the main window
		msgCsl("QDockWidget added")
#		self.widget.setFloating(True)
		self.widget.hide()
		self.widget.ui.horizontalSlider_value.setMaximum(600)
		
		self.connections_for_button_clicked = { 
							"button_value_ok"				: "Validation", 
							"button_value_select_object"	: "SelectObject", 
							"button_value_apply"			: "Apply", 
							"button_value_cancel"			: "Cancel"}
		self.connections_for_slider_changed = {
							"horizontalSlider_value"		: "ValueSlide"}
							
		self.connections_for_text_changed = {
							"object_value"					: "ValueText"}
		for m_key, m_val in self.connections_for_button_clicked.items():
			#print_msg( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("clicked()"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_slider_changed.items():
			#print_msg( "Connecting : " + str(getattr(self.ui, str(m_key))) + " and " + str(getattr(self.obj, str(m_val))) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL("valueChanged(int)"),getattr(self, str(m_val)))
		for m_key, m_val in self.connections_for_text_changed.items():
			#print_msg( "Connecting : " + str(m_key) + " and " + str(m_val) )
			QtCore.QObject.connect(getattr(self.widget.ui, str(m_key)), QtCore.SIGNAL(_fromUtf8("textChanged(QString)")),getattr(self, str(m_val)))   

	def Validation(self):
		self.Apply()
		self.widget.hide()
		return None
		
	def SelectObject(self):
		sel = FreeCADGui.Selection.getSelectionEx()
		if len(sel) > 0:
#			msgCsl("Wing found for linking Rod")
			wobj = sel[0].Object
			if wobj.Proxy.__class__.__name__ == "Section":
#				msgCsl("Wing type found in selection")
				self.obj = wobj
				self.widget.ui.info_select_object.setText(wobj.Label + "(" + wobj.Name + ")")
				msgCsl("object bounbox ZLength: " + str(self.obj.Shape.BoundBox.ZLength))
				self.widget.ui.object_value.setText(str(self.obj.Offset))
				max = int(self.obj.Shape.BoundBox.ZLength)
				self.widget.ui.horizontalSlider_value.setMaximum(max)
				self.Apply()

	def Apply(self):
		if hasattr(self, "obj"):
			value = float(self.widget.ui.object_value.text())
			self.obj.Offset = value
			FreeCAD.ActiveDocument.recompute()

	def ValueSlide(self, value):
		# If the value was changed internally, ignore event.
		if self.internal:
			return
		if hasattr(self, "obj"):
			self.obj.Proxy.updatePlane(self.obj, value)
			self.widget.ui.object_value.setText(str(value))

	def ValueText(self):
		if hasattr(self, "obj"):
			# Update the slider by internal update
			value = float(self.widget.ui.object_value.text())
			self.obj.Proxy.updatePlane(self.obj, value)
			self.internal = True
			self.widget.ui.horizontalSlider_value.setValue(value)
			self.internal = False
			
	def Cancel(self):
		self.widget.ui.info_select_object.setText("")
		self.widget.ui.object_value.setText("")
		self.widget.ui.horizontalSlider_value.setValue(0)
		if hasattr(self, "obj"):
			self.obj.Proxy.updatePlane(self.obj, self.obj.Offset)
			self.obj = None
		self.widget.hide()

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
