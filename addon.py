import xbmc
import os
import sys
import xbmcaddon
import xbmcgui
import time
import subprocess

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )
sys.path.append(os.path.join( addon_dir, 'resources', 'lib' ) )
import HyperPyCon 

line1 = "Welcome!"
line2 = "We are about to prepare your hyperion config file in this step-by-step wizard."
line3 = "You must complete all steps to have the config file generated. Let\'s start!"

xbmcgui.Dialog().ok(addonname, line1, line2 + line3)

try:

	device_versions = [ HyperPyCon.HyperPyCon.ws2801 , HyperPyCon.HyperPyCon.adalight, HyperPyCon.HyperPyCon.apa102]
	selected_device = xbmcgui.Dialog().select("Select your led device:",device_versions)
	if selected_device == 0:	
		if "spidev" not in subprocess.check_output(['ls','/dev']):
			xbmcgui.Dialog().ok(addonname, "We have detected that your system does not have spi enabled. You can still continue, but leds may not work if you're using GPIO/SPI connection")

	xbmcgui.Dialog().ok(addonname, "In next two steps please provovide number of leds at the top edge of tv (horizontally)" +
		"  and number of leds at the side of your tv (count leds at single side only) - horizontally")

	nol_horizontal = xbmcgui.Dialog().input("Select number of leds horizontally","29",xbmcgui.INPUT_NUMERIC)
	nol_vertical = xbmcgui.Dialog().input("Select number of leds vertically","16",xbmcgui.INPUT_NUMERIC)

	hyperion_configuration = HyperPyCon.HyperPyCon(int(nol_horizontal), int(nol_vertical))
	hyperion_configuration.set_device_type(device_versions[selected_device])
	hyperion_configuration.set_device_rate(int(addon.getSetting("rate")))
	hyperion_configuration.set_color_values(float(addon.getSetting("redThreshold")), float(addon.getSetting("redGamma")),float(addon.getSetting("redBlacklevel")),float(addon.getSetting("redWhitelevel")),"RED")
	hyperion_configuration.set_color_values(float(addon.getSetting("greenThreshold")), float(addon.getSetting("greenGamma")),float(addon.getSetting("greenBlacklevel")),float(addon.getSetting("greenWhitelevel")),"GREEN")
	hyperion_configuration.set_color_values(float(addon.getSetting("blueThreshold")), float(addon.getSetting("blueGamma")),float(addon.getSetting("blueBlacklevel")),float(addon.getSetting("blueWhitelevel")),"BLUE")
	hyperion_configuration.set_smoothing(addon.getSetting("smoothingType"),int(addon.getSetting("smoothingTime")),int(addon.getSetting("smoothingFreq")))
	hyperion_configuration.set_blackborderdetection((addon.getSetting("bbdEnabled") == "true"), float(addon.getSetting("bbdThreshold")))
	
	options = ["Right/bottom corner and goes up","Left/bottom corner and goes up","Center/bottom and goes right","Center/bottom and goes left"]
	selected_index = xbmcgui.Dialog().select("Select where the led chain starts:",options)

	if selected_index == 1:
		hyperion_configuration.led_chain.reverse_direction()
		hyperion_configuration.led_chain.set_offset(int(nol_horizontal))
	elif selected_index == 2 or selected_index == 3:
		offset = xbmcgui.Dialog().input("How many leds from the center to the corner or the screen?","15",xbmcgui.INPUT_NUMERIC)
		if selected_index == 2:
			hyperion_configuration.led_chain.set_offset((-1)*int(offset))
		else:
			hyperion_configuration.led_chain.reverse_direction()
			hyperion_configuration.led_chain.set_offset(int(offset))

	grabber = ""
	lsusb_output = subprocess.check_output('lsusb')

	if "1b71:3002" in lsusb_output:
		grabber = "utv007"
	elif "05e1:0408" in lsusb_output:
		grabber = "stk1160"

	if grabber != "":
		if "video0" in subprocess.check_output(['ls','/dev']):
			if xbmcgui.Dialog().yesno(addonname, "Compatible video grabber has been detected. Do you want to enable video grabber in hyperion?"):
				hyperion_configuration.config_grabber(grabber)
		else:
			xbmcgui.Dialog().ok(addonname, "Video grabber has been detected but video0 does not exist. Please install drivers or use different disto")
	else:
		xbmcgui.Dialog().ok(addonname, "We have not detected the grabber. Grabber-v4l2 section will not be added to the config file.")

	xbmcgui.Dialog().ok(addonname, "That's all! Now we will attempt to restart hyperion...")
	hyperion_configuration.save_config_file(hyperion_configuration.create_config(grabber),"/storage/.config/","hyperion.config.new")
	hyperion_configuration.restart_hyperion("hyperion.config.new")
	if not xbmcgui.Dialog().yesno(addonname, "Have you seen the rainbow swirl?"):
		xbmcgui.Dialog().ok(addonname, "Something went wrong... Please try running hyperion from command line to see the error... (on openelec: /storage/hyperion/bin/hyperiond.sh /storage/.config/hyperion.config.new)")
		sys.exit()
	else:
		xbmcgui.Dialog().ok(addonname, "For the next 10 seconds you will see test image and leds should adjust to that image. Check if the leds are showing the right colors in the right places."+
			" If not, start this wizard again and provide correct numbers of leds horizontally and vertically.")
		#hyperion_configuration.test_corners(10)
		okno = xbmcgui.WindowDialog(xbmcgui.getCurrentWindowId())
		#obrazek = xbmcgui.ControlImage(0,0,okno.getWidth(),okno.getHeight(),addon_dir+"/test_picture.png")
		obrazek = xbmcgui.ControlImage(0,0,1280,720,addon_dir+"/test_picture.png")
		okno.addControl(obrazek)
		okno.show()
		obrazek.setVisible(True)
		hyperion_configuration.show_test_image(addon_dir+"/test_picture.png")
		time.sleep(10)
		okno.close()
		hyperion_configuration.clear_leds()

	if xbmcgui.Dialog().yesno(addonname, "Do you want us to save this config as your default one?","(if No, changes will be lost after hyperion/system restart)"):
		hyperion_configuration.overwrite_default_config()
	elif xbmcgui.Dialog().yesno(addonname, "Hyperion is now running with the newly created config. Would you like to restart hyperion with previous config?"):
		hyperion_configuration.restart_hyperion("hyperion.config.json")

	xbmcgui.Dialog().ok(addonname, "That\'s all Folks! :) . Enjoy!", "If you'd like to fine tune advanced parameters, please modify addon settings before running it")

except Exception, e:
        xbmcgui.Dialog().ok(addonname, repr(e),"Please report an error at github issue list")

