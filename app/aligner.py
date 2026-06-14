import re

##
# OLEDにレイアウトを合わせるクラス
#
class Aligner:	
    #def __init__(self):
        
	##
	#
	#
	def formattedMsg(self, msg, display_length = 12):
		length = len(msg)
		
		if length >= display_length:
			return msg.replace('*', '')

		return re.sub(r'\*', ' ' * (display_length - length + 1), msg)
 
	##
	#
	#
	def rightMsg(self, msg, display_length = 12):
		length = len(msg)
		
		if length <=  display_length:
			return msg
	
		return msg[length - display_length:]

