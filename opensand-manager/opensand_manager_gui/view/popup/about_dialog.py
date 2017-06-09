#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
#
# OpenSAND is an emulation testbed aiming to represent in a cost effective way a
# satellite telecommunication system for research and engineering activities.
#
#
# Copyright © 2016 TAS
#
#
# This file is part of the OpenSAND testbed.
#
#
# OpenSAND is free software : you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.
#
#

# Author: Vincent Duvert / Viveris Technologies <vduvert@toulouse.viveris.com>


"""
about_dialog.py - The about dialog
"""

import gtk.gdk

from opensand_manager_gui.view.window_view import WindowView

LOGO='/usr/share/icons/hicolor/48x48/apps/opensand-manager.png'

class AboutDialog(WindowView):
    """ the about window """
    def __init__(self):
        WindowView.__init__(self, None, 'about_dialog')
        self._dlg = self._ui.get_widget('about_dialog')
        self._dlg.set_icon_name('opensand-manager')
        logo = gtk.gdk.pixbuf_new_from_file(LOGO)
        self._dlg.set_logo(logo)

    def run(self):
        """ run the about dialog """
        self._dlg.run()

    def close(self):
        """ close the window """
        self._dlg.destroy()

    def on_about_dialog_delete_event(self, source=None, event=None):
        """ delete-event on window """
        self.close()

