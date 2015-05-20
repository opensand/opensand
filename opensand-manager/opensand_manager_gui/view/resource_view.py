#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
#
# OpenSAND is an emulation testbed aiming to represent in a cost effective way a
# satellite telecommunication system for research and engineering activities.
#
#
# Copyright © 2014 TAS
# Copyright © 2015 CNES
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

# Author: Bénédicte Motto / <bmotto@toulouse.viveris.com>

"""
resource_view.py - the configuration tab view
"""

import gtk
import gobject

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas

from opensand_manager_core.carrier import Carrier

from opensand_manager_core.utils import get_conf_xpath, FORWARD_DOWN, RETURN_UP, \
        ROLL_OFF, CARRIERS_DISTRIB, BANDWIDTH, TAL_AFFECTATIONS, TAL_DEF_AFF, \
        TAL_ID, SYMBOL_RATE, ACCESS_TYPE, CATEGORY, ST, SPOT, ID, GW, RETURN_UP_BAND
from opensand_manager_gui.view.utils.config_elements import SpotTree
from opensand_manager_gui.view.window_view import WindowView


class ResView(WindowView):
    """ Element for the resouces configuration tab """

    def __init__(self, parent, model, manager_log):
        WindowView.__init__(self, parent)

        self._init = True
        self._log = manager_log
        self._model = model
        self._spot = None
        self._gw = None
        self._tree_element = []

        #Add graph froward
        self._graphe_forward = self._ui.get_widget('scrolledwindow_forward_graph')
        self._figure_forward = Figure()
        self._ax_forward = self._figure_forward.add_subplot(111)
        canvas = FigureCanvas(self._figure_forward)
        canvas.set_size_request(200,200)
        self._graphe_forward.add_with_viewport(canvas)
        #Add graph froward
        self._graphe_return = self._ui.get_widget('scrolledwindow_return_graph')
        self._figure_return = Figure()
        self._ax_return = self._figure_return.add_subplot(111)
        canvas = FigureCanvas(self._figure_return)
        canvas.set_size_request(200,200)
        self._graphe_return.add_with_viewport(canvas)
        #Update graph
        
        #St allocation
        self._st_forward = self._ui.get_widget('vbox_forward_st_assignment')
        self._st_return = self._ui.get_widget('vbox_return_st_assignment')

        treeview = self._ui.get_widget('resource_tree')
        self._tree = SpotTree(treeview, "Spot", self.on_selection)

        # update view from model
        # do not load it in gobject.idle_add because we won't be able to catch
        # the exception
        # show first child
        self.update_view()


    def on_selection(self, path):
        (tree, iterator) = path.get_selected()
        self._spot = None
        self._gw = None
        
        # select first child
        if len(path.get_selected_rows()[1][0]) < 2 :
            iterator = tree.iter_children(iterator)
            self._tree.select_path(tree.get_path(iterator))

        if tree.get_value(iterator, 0).lower().startswith(GW):
            self._gw = tree.get_value(iterator, 0).lower().split(GW)[1]
            if tree.get_value(tree.iter_parent(iterator),\
                              0).lower().startswith(SPOT):
                self._spot = tree.get_value(tree.iter_parent(iterator),\
                                            0).lower().split(SPOT)[1]
                

        self.update_view()
        pass

    def update_tree(self):
        """ update the tools tree """
        config = self._model.get_conf().get_configuration()
        xpath = "//" + RETURN_UP_BAND
        for element in config.get(xpath) :
            if element.tag == SPOT:
                spot =  SPOT + element.get(ID)
                gw =  GW + element.get(GW)
                if spot not in self._tree_element:
                    gobject.idle_add(self._tree.add_spot, spot)
                    self._tree_element.append(spot)
                
                if spot + gw not in self._tree_element: 
                    list_parent = []
                    list_parent.append(spot)
                    gobject.idle_add(self._tree.add_child, GW + element.get(GW),
                                     list_parent, True)
                    self._tree_element.append(spot + gw)

        
        if self._init:
            first_child_path = (0,0)
            gobject.idle_add(self._tree.select_path, first_child_path)
            self._init = False
        # continue to refresh
        return True


    def update_view(self):
        self.update_tree()
        if self._spot is not None and self._gw is not None:
            self.update_graph(FORWARD_DOWN)
            self.update_graph(RETURN_UP)
            self.update_st_assignment(FORWARD_DOWN)
            self.update_st_assignment(RETURN_UP)
            self._ui.get_widget('vbox_resources').show_all()
        else:
            self._ui.get_widget('vbox_return').hide()
            self._ui.get_widget('vbox_forward').hide()
            self._ui.get_widget('vbox_resources').show()

    def clear_graph(self, link):
        """Clear all the representaion"""
        if link == FORWARD_DOWN:
            self._ax_forward.cla()
            self._figure_forward.canvas.draw()
        else:
            self._ax_return.cla()
            self._figure_return.canvas.draw()
        
        
    def update_graph(self, link):
        """Display on the graph the carrier representation"""
        #get the xml config
        config=self._model.get_conf()._configuration
        
        #get all carriers
        list_carrier=[]
        color={1:'b-', 2:'g-', 3:'c-', 4:'m-', 5:'y-', 6:'k-', 7:'r-'}
        xpath = get_conf_xpath(CARRIERS_DISTRIB, link, self._spot, self._gw)
        for carrier in config.get_table_elements(config.get(xpath)):
            content = config.get_element_content(carrier)
            list_carrier.append(Carrier(float(content[SYMBOL_RATE])/1000000,
                                        content[CATEGORY], 
                                        content[ACCESS_TYPE]))
        
        #get the roll off
        xpath = get_conf_xpath(ROLL_OFF, link)
        roll_off = float(config.get_value(config.get(xpath)))
        #display roll off
        if link == FORWARD_DOWN:
            self._ui.get_widget('label_forward_rolloff').set_text(
                                        'Roll_off : ' + str(roll_off))
        elif link == RETURN_UP:
            self._ui.get_widget('label_return_rolloff').set_text(
                                        'Roll_off : ' + str(roll_off))
        off_set = 0
        self.clear_graph(link)
        #Trace the graphe
        if link == FORWARD_DOWN:
            for element in list_carrier :
                element.calculateXY(roll_off, off_set)
                self._ax_forward.plot(element.getX(), 
                                      element.getY(), 
                                      color[element.getGroup()])
                off_set = off_set + element.getBandwidth(roll_off)
            if off_set != 0:
                self._ax_forward.axis([float(-off_set)/6, 
                                      off_set + float(off_set)/6,
                                      0, 1.5])
            bp, = self._ax_forward.plot([0, 0, off_set, off_set], 
                                        [0,1,1,0], 'r-', 
                                        label = BANDWIDTH, 
                                        linewidth = 3.0)
            self._ax_forward.legend([bp],[BANDWIDTH])
            self._ax_forward.grid(True)
            self._figure_forward.canvas.draw()
        elif link == RETURN_UP:
            for element in list_carrier :
                element.calculateXY(roll_off, off_set)
                self._ax_return.plot(element.getX(), 
                                     element.getY(), 
                                     color[element.getGroup()])
                off_set = off_set + element.getBandwidth(roll_off)
            if off_set != 0:
                self._ax_return.axis([float(-off_set)/6, 
                                     off_set + float(off_set)/6, 
                                     0, 1.5])
            bp, = self._ax_return.plot([0, 0, off_set, off_set], 
                                       [0,1,1,0], 'r-', 
                                       label = BANDWIDTH, 
                                       linewidth = 3.0)
            self._ax_return.legend([bp],[BANDWIDTH])
            self._ax_return.grid(True)
            self._figure_return.canvas.draw()

        #Display Bandwidth
        if link == FORWARD_DOWN:
            self._ui.get_widget('label_forward_bandwidth').set_text(
                                'Bandwidth : ' + str(off_set) + ' MHz')
        elif link == RETURN_UP:
            self._ui.get_widget('label_return_bandwidth').set_text(
                                'Bandwidth : ' + str(off_set) + ' MHz')
    
    
    def update_st_assignment(self, link):
        """Refresh the list of st assignment """
        group_list = []
        terminal_list = {}
        color = {0:'blue', 
                 1:'green', 
                 2:'cyan', 
                 3:'magenta', 
                 4:'yellow', 
                 5:'black', 
                 6:'red'}
        category = {0:'Standard',
                    1:'Premium',
                    2:'Pro'}
        config = self._model.get_conf().get_configuration()
        host_list = self._model.get_hosts_list()
        
        if link == FORWARD_DOWN:
            for element in self._st_forward.get_children():
                self._st_forward.remove(element)
        elif link == RETURN_UP:
            for element in self._st_return.get_children():
                self._st_return.remove(element)

        #Get number of Group
        xpath = get_conf_xpath(TAL_AFFECTATIONS, link, self._spot, self._gw)
        defaulf_grp_path = get_conf_xpath(TAL_DEF_AFF, link,
                                          self._spot, self._gw)
        default_grp = config.get_value(config.get(defaulf_grp_path))
        default_cat = default_grp + " (default)"

        
        for terminal in config.get_table_elements(config.get(xpath)):
                content = config.get_element_content(terminal)
                if content[CATEGORY] != default_grp:
                    group_list.append(content[CATEGORY])
                    terminal_list[content[TAL_ID]] = content[CATEGORY]

        host_list = self._model.get_hosts_list()  
        for host in host_list:
            if not host.get_name().lower().startswith(ST):
                continue
            if host.get_spot_id() != self._spot:
                continue
            if host.get_instance() not in terminal_list.keys():
                group_list.append(default_cat)
                terminal_list[host.get_instance()] = default_cat

                    
        present = {k: group_list.count(k) for k in set(group_list)}
        for group in present:
            #create group field
            hbox_gr = gtk.HBox()
            #Create field for group title
            hbox_gr_title = gtk.HBox()
            hbox_gr.pack_start(hbox_gr_title, expand=False, fill=False)
            #Color for the group
            color_id = 6
            for key, value in category.items():
                if group.startswith(value):
                    color_id = key
                    break
            label_color = gtk.Label("<span background='%s'>     </span>" %
                                    color[color_id])
            label_color.set_use_markup(True)
            #Name of the group
            label_gr = gtk.Label("<b>Category %s</b>" % group)
            label_gr.set_use_markup(True)
            hbox_gr_title.pack_start(label_color, 
                                     expand=False, 
                                     fill=False, 
                                     padding=10)
            hbox_gr_title.pack_start(label_gr, 
                                     expand=False, 
                                     fill=False, 
                                     padding=10)
            #Add all the host with the same group
            for host in host_list:
                if not host.get_name().lower().startswith(ST):
                    continue
                if host.get_instance() in terminal_list.keys() and \
                   terminal_list[host.get_instance()] == group:
                    label_st = gtk.Label(host.get_name().upper())
                    hbox_gr.pack_start(label_st, 
                                       expand=False, 
                                       fill=False, 
                                       padding=10)
            #Add the new group in window
            if link == FORWARD_DOWN:
                self._st_forward.pack_start(hbox_gr, 
                                            expand=False, 
                                            fill=False)
            elif link == RETURN_UP:
                self._st_return.pack_start(hbox_gr, 
                                           expand=False, 
                                           fill=False)
        self._ui.get_widget('vbox_resources').show_all()
    

    def is_modified(self):
        """ check if the configuration was modified by user
            (used in callback so no need to use locks) """
        try:
            if self._update_spot:
                return True

            config = self._model.get_conf()
            # payload_type
            widget = self._ui.get_widget(config.get_payload_type())
            if not widget.get_active():
                return True
            # emission_std
            widget = self._ui.get_widget(config.get_emission_std())
            if not widget.get_active():
                return True

            # return_up_encap
            if self._out_stack.get_stack() != config.get_return_up_encap():
                return True

            # forward_down_encap
            if self._in_stack.get_stack() != config.get_forward_down_encap():
                return True

        except:
            raise

        return False

    def on_stack_modif(self, source=None, event=None):
        """ 'changed' event on a combobox from the stack """
        self.enable_conf_buttons()

    def on_lan_stack_modif(self, source=None, event=None):
        """ 'changed' event on a combobox from the stack """
        # we need to check because buttons are modified when loading stack
        if self.is_lan_adapt_stack_modif():
            self.enable_conf_buttons()

