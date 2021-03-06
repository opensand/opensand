#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#
# OpenSAND is an emulation testbed aiming to represent in a cost effective way a
# satellite telecommunication system for research and engineering activities.
#
#
# Copyright © 2017 TAS
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

# Author : Maxime POMPA

"""
graphical_parameter.py - Some graphical parameters for band configuration
"""

import gtk
import gobject

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas

from opensand_manager_core.carrier import Carrier
from opensand_manager_core.utils import get_conf_xpath, ROLL_OFF, CARRIERS_DISTRIB, \
        FMT_GROUPS, ID, BANDWIDTH, FMT_ID, FMT_GROUP, RATIO, SYMBOL_RATE, \
        CATEGORY, ACCESS_TYPE, CCM, VCM, DAMA, FORWARD_DOWN, RETURN_UP
from opensand_manager_core.my_exceptions import ModelException
from opensand_manager_gui.view.popup.modcod_dialog import ModcodParameter
from opensand_manager_gui.view.window_view import WindowView
from opensand_manager_gui.view.popup.infos import error_popup

class GraphicalParameter(WindowView):
    """ an band configuration window """
    def __init__(self, model, spot, gw, fmt_group,
                 carrier_arithmetic, manager_log,
                 update_cb, link):

        WindowView.__init__(self, None, 'band_configuration_dialog')

        self._dlg = self._ui.get_widget('band_configuration_dialog')
        self._dlg.set_keep_above(False)

        self._model = model
        self._spot = spot
        self._gw = gw
        self._bandwidth_total = 1
        self._log = manager_log
        self._enabled_button = []
        self._removed = []
        self._link = link
        self._update_cb = update_cb
        self._description = {}

        title = self._ui.get_widget('label_title_parameter')
        if self._link == FORWARD_DOWN:
            title.set_text(    "<b>Forward Band Configuration</b>")
        elif self._link == RETURN_UP:
            title.set_text(    "<b>Return Band Configuration</b>")
        title.set_use_markup(True)

        # Create graph in the window
        graph = self._ui.get_widget('scrolled_graph_parameter')
        self._figure = Figure()
        self._ax = self._figure.add_subplot(111)
        canvas = FigureCanvas(self._figure)
        canvas.set_size_request(400,400)
        graph.add_with_viewport(canvas)
        self._carrier_arithmetic = carrier_arithmetic

        self._list_carrier = self._carrier_arithmetic.get_list_carrier()
        self._nb_carrier = len(self._list_carrier)
        self._fmt_group = fmt_group

        self._vbox = self._ui.get_widget('vbox_band_parameter')
        self._vbox.show_all()


    def go(self):
        """ run the window """
        button_rolloff = self._ui.get_widget('spinbutton_rollof_parameter')
        button_rolloff.connect("value_changed", self.on_update_roll_off)

        button_add = self._ui.get_widget('button_add_carriers')
        button_add.get_image().show()
        button_add.connect("clicked", self.add_to_carrier_list)
        try:
            self.load()
        except ModelException, msg:
            error_popup(str(msg))
        self._dlg.set_title("Resources configuration - OpenSAND Manager")
        self._dlg.run()


    def load(self):
        """ load the hosts configuration """
        config = self._model.get_conf().get_configuration()

        carrier_id = 1
        for carrier in self._list_carrier:
            self.create_carrier_interface(carrier,
                                          carrier_id)
            carrier_id += 1

        xpath = get_conf_xpath(ROLL_OFF, self._link)
        self._ui.get_widget('spinbutton_rollof_parameter').set_value(
                            float(config.get_value(config.get(xpath))))
        self.trace()

    def clear_graph(self):
        """
        Clear the graphical representation
        """
        self._ax.cla()
        self._figure.canvas.draw()


    def clear_carrier_interface(self):
        """Clear the carrier menu """
        self._enabled_button = []
        table = self._ui.get_widget('vbox_carriers_list')
        for element in table.get_children():
            table.remove(element)

    def create_carrier_interface(self, carrier, carrier_id):
        """
        Add a new carrier
        One carrier is define by (symbol_rate, fmt, group,
        accesse type and delete button)
        """
        hbox_carrier = gtk.HBox(homogeneous=True, spacing=0)
        hbox_name_carrier = gtk.HBox(homogeneous=True, spacing=0)
        name_carrier = gtk.Label("Carrier" + str(carrier_id))

        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_DIALOG_INFO,
                           gtk.ICON_SIZE_MENU)

        hbox_name_carrier.pack_start(name_carrier, expand=False, fill=False)
        hbox_name_carrier.pack_start(img, expand=True, fill=False, padding=1)

        self._description[carrier_id] = img

        #Create Synbol rate
        ajustement1 = gtk.Adjustment(float(carrier.get_symbol_rate()) / 1E6,
                                     0, 10000, 1, 8)
        new_sr = gtk.SpinButton(ajustement1, digits=2)
        new_sr.set_numeric(True)
        new_sr.set_name("sr"+str(carrier_id))
        new_sr.connect("value-changed", self.on_update_sr, carrier_id)

        ajustement2 = gtk.Adjustment(int(carrier.get_nb_carriers()),
                                     1, 5, 1, 8)
        new_nb_carrier = gtk.SpinButton(ajustement2, digits=0)
        new_nb_carrier.set_numeric(True)
        new_nb_carrier.set_name("nb_carrier"+str(carrier_id))
        new_nb_carrier.connect("value-changed", self.on_update_nb_carrier, carrier_id)

        #Create Group spin button
        config = self._model.get_conf().get_configuration()
        category_type = config.get_simple_type("Category")

        comboBox = gtk.combo_box_new_text()
        if not category_type is None and not category_type["enum"] is None:
            for cat in category_type["enum"]:
                comboBox.append_text(cat)
        comboBox.set_active(carrier.get_category())
        comboBox.connect("changed", self.on_update_group, carrier_id)

        #Create MODCOD button
        button_modcod = gtk.Button(label="Configure")
        button_modcod.connect("clicked",
                              self.on_modcod_configuration_clicked,
                              carrier_id)

        hbox_button = gtk.HBox(homogeneous=True, spacing=0)
        #Create tooltips for button
        tooltip = gtk.Tooltips()
        #Copy button
        image_copy = gtk.Image()
        image_copy.set_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)
        button_copy = gtk.Button()
        button_copy.set_image(image_copy)
        button_copy.get_image().show()
        button_copy.connect("clicked", self.on_copy_carrier, carrier_id)
        tooltip.set_tip(button_copy, "Copy")

        #Delete button
        image_del = gtk.Image()
        image_del.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        button_del = gtk.Button()
        button_del.set_image(image_del)
        button_del.get_image().show()
        button_del.connect("clicked", self.on_remove_carrier, carrier_id)
        tooltip.set_tip(button_del, "Delete")
        self._enabled_button.append(button_del)
        if len(self._enabled_button) > 1:
            for button in self._enabled_button:
                button.set_sensitive(True)
        else:
            button_del.set_sensitive(False)

        hbox_button.pack_start(button_copy, expand=False, fill=False)
        hbox_button.pack_start(button_del, expand=False, fill=False)


        hbox_carrier.pack_start(hbox_name_carrier, expand=False, fill=False)
        hbox_carrier.pack_start(new_sr, expand=False, fill=False)
        hbox_carrier.pack_start(new_nb_carrier, expand=False, fill=False)
        hbox_carrier.pack_start(comboBox, expand=False, fill=False, padding=0)
        hbox_carrier.pack_start(button_modcod, expand=False, fill=False)
        hbox_carrier.pack_start(hbox_button, expand=False, fill=False)

        table = self._ui.get_widget('vbox_carriers_list')
        table.pack_start(hbox_carrier, expand=False, fill=False)

        self._vbox.show_all()


    def add_to_carrier_list(self, source=None, event=None):
        """Create a new carrier with default value """
        self._nb_carrier += 1
        fmt_grp = str(self._fmt_group.keys()[0])

        if self._link == FORWARD_DOWN:
            self._list_carrier.append(Carrier(symbol_rate=4E6,
                                              category=0,
                                              fmt_groups=fmt_grp,
                                              access_type=CCM))
        else:
            self._list_carrier.append(Carrier(symbol_rate=4E6,
                                              category=0,
                                              fmt_groups=fmt_grp,
                                              access_type=DAMA))
        self.create_carrier_interface(self._list_carrier[-1],
                                      self._nb_carrier)
        self.trace()

    def on_copy_carrier(self, source=None, id_carrier=None):
        """Copy a carrier identify by his ID"""
        self._nb_carrier += 1

        sr = self._list_carrier[id_carrier - 1].get_symbol_rate()
        nb = self._list_carrier[id_carrier - 1].get_nb_carriers()
        g = self._list_carrier[id_carrier - 1].get_category()
        ac = self._list_carrier[id_carrier - 1].get_access_type()
        fmt_grp = self._list_carrier[id_carrier - 1].get_str_fmt_grp()
        md = self._list_carrier[id_carrier - 1].get_str_modcod()
        ra = self._list_carrier[id_carrier - 1].get_str_ratio()

        self._list_carrier.append(Carrier(sr, nb, g, ac, fmt_grp, md, ra))

        self.create_carrier_interface(self._list_carrier[-1], self._nb_carrier)

        self.trace()


    def on_remove_carrier(self, source=None, id_carrier=None):
        """ Remove carrier in the list identify by his ID"""
        del self._list_carrier[id_carrier - 1]
        self._removed.append(id_carrier - 1)
        self._nb_carrier = self._nb_carrier - 1
        self.clear_carrier_interface()

        carrier_id = 1
        for carrier in self._list_carrier:
            self.create_carrier_interface(carrier, carrier_id)
            carrier_id += 1
        self.trace()

    def trace(self, source=None):
        """
        Draw in the graph area the graphical representation of the
        content in the carrier list
        """
        self.update_ratio()

        roll_off = float(self._ui.get_widget('spinbutton_rollof_parameter').get_value())

        carrier_id = 1
        self.clear_graph()
        self._carrier_arithmetic.update_graph(self._ax, roll_off);
        self._carrier_arithmetic.update_rates(self._fmt_group);

        for element in self._list_carrier :
            description = ''
            for (min_rate, max_rate) in element.get_rates():
                description += "Rate per carrier [%d, %d] kb/s\n" % (min_rate / 1000,
                                                                     max_rate / 1000)

            self._description[carrier_id].set_tooltip_text(description)
            carrier_id += 1

        bandwidth = self._carrier_arithmetic.get_bandwidth()
        self._figure.canvas.draw()
        self._ui.get_widget('bandwith_total').set_text(str(bandwidth) + " MHz")
        self._bandwidth_total = bandwidth

    def on_update_roll_off(self, source=None):
        # disable method calling twice at the fisrt time
        gobject.idle_add(self.trace)

    def on_update_sr(self, source = None, carrier_id = None):
        """Refresh the graph when the symbole rate change"""
        # disable method calling twice at the fisrt time
        gobject.idle_add(self.on_update_sr_callback,
                         source, carrier_id)

    def on_update_sr_callback(self, source=None, carrier_id=None):
        """Refresh the graph when the symbole rate change"""
        self._list_carrier[carrier_id-1].set_symbol_rate(source.get_value() * 1E6)
        self.trace()

    def on_update_nb_carrier(self, source = None, carrier_id = None):
        """Refresh the graph when the symbole rate change"""
        # disable method calling twice at the fisrt time
        gobject.idle_add(self.on_update_nb_carrier_callback,
                         source, carrier_id)

    def on_update_nb_carrier_callback(self, source=None, carrier_id=None):
        """Refresh the graph when the symbole rate change"""
        self._list_carrier[carrier_id-1].set_nb_carriers(int(source.get_value()))
        self.trace()

    def update_ratio(self):
        """Refresh ratio when the symbole rate change"""
        total_ratio_rs = 0
        total_ratio = 0
        roll_off = float(self._ui.get_widget('spinbutton_rollof_parameter').get_value())
        for carrier in self._list_carrier:
            total_ratio_rs += sum(carrier.get_ratio()) * \
                    carrier.get_symbol_rate() / 1E6
        for carrier in self._list_carrier:
            total_ratio += int(round(carrier.get_nb_carriers() * (1 + roll_off) /\
                                     self._bandwidth_total * total_ratio_rs ))

        for carrier in self._list_carrier:
            # bandwidth and bandwidth_total in Mhz
            ratio = int(round(carrier.get_nb_carriers() * (1 + roll_off) /\
                    self._bandwidth_total * total_ratio_rs / total_ratio *  100))
            ratios = carrier.get_ratio()
            old_ratios = list(ratios)
            ratio_str = ""
            index = 1
            for r in ratios:
                new_ratio = ratio * r / sum(old_ratios)
                if index != len(ratios):
                    ratio_str += str(new_ratio) + ";"
                else:
                    ratio_str += str(new_ratio)
                index += 1

            carrier.set_ratio(ratio_str)


    def on_update_group(self, source=None, id_carrier=None):
        """Refresh the graph with new color when the group change"""
        tree_iter = source.get_active_iter()
        if tree_iter != None:
            model = source.get_model()
            self._list_carrier[id_carrier - 1].set_category(model[tree_iter].path[0])
            self.trace()


    def on_modcod_configuration_clicked(self, widget, id_carrier=None, event=None):
        """Open the modcod configuration window """
        window = ModcodParameter(self._model,
                                 self._log,
                                 self._link,
                                 id_carrier,
                                 self._list_carrier,
                                 self.trace)
        ret = window.go()

        # adjust FMT Ids
        new_fmt_id = self._fmt_group.keys()[-1] + 1
        used_fmt_groups = []
        for carrier in self._list_carrier:
            fmt_groups = []
            carrier_fmt_groups = []
            if carrier.get_access_type() == VCM:
                carrier_fmt_groups = map(lambda x: str(x), carrier.get_modcod())
            else:
                carrier_fmt_groups = [carrier.get_str_modcod()]
            for carrier_fmt_group in carrier_fmt_groups:
                if carrier_fmt_group not in self._fmt_group.values():
                    fmt_groups.append(new_fmt_id)
                    used_fmt_groups.append(new_fmt_id)
                    self._fmt_group[new_fmt_id] = carrier_fmt_group
                    new_fmt_id += 1
                else:
                    for fmt_id in self._fmt_group.keys():
                        if self._fmt_group[fmt_id] == carrier_fmt_group:
                            fmt_groups.append(fmt_id)
                            used_fmt_groups.append(fmt_id)
                            break
            groups = ';'.join(str(fmt_grp_id) for fmt_grp_id in fmt_groups)
            carrier.set_fmt_groups(groups)

        # remove unused fmt_group, they could thus be re-used later
        # FIXME at the moment we only increment and don't reuse ID
        for fmt_id in self._fmt_group.keys():
            if fmt_id not in used_fmt_groups:
                del self._fmt_group[fmt_id]

    def on_band_configuration_dialog_save(self, source=None, event=None):
        #get the file xml
        config = self._model.get_conf().get_configuration()

        #save bandwidth
        xpath = get_conf_xpath(BANDWIDTH, self._link, self._spot, self._gw)
        bandwidth = self._ui.get_widget('bandwith_total').get_text().split(' ')
        config.set_value(bandwidth[0], xpath)

        #save roll_off
        xpath = get_conf_xpath(ROLL_OFF, self._link)
        roll_off = float(self._ui.get_widget('spinbutton_rollof_parameter').get_value())
        config.set_value(roll_off, xpath)

        #save carriers_distribution
        xpath = get_conf_xpath(CARRIERS_DISTRIB, self._link,
                               self._spot, self._gw)
        table = config.get(xpath)

        #Get the carrier number in xml
        carrier_line = []
        for element in config.get_table_elements(table):
            carrier_line.append(config.get_element_content(element))
        i = len(carrier_line)
        #Place the number of carrier in xml
        while i < len(self._list_carrier):
            config.add_line(config.get_path(table))
            i += 1
        table = config.get(xpath)

        # remove
        i = len(carrier_line)
        while i > len(self._list_carrier):
            config.remove_line(config.get_path(table), 0)
            table = config.get(xpath)
            i -= 1

        #Save all carrier element
        carrier_id = 0
        access_type_cat = {}
        for carrier in self._list_carrier:
            config.set_value(carrier.get_old_access_type(),
                             config.get_path(config.get_table_elements(table)[carrier_id]),
                             ACCESS_TYPE)
            config.set_value(carrier.get_old_category(config),
                             config.get_path(config.get_table_elements(table)[carrier_id]),
                             CATEGORY)
            config.set_value(carrier.get_str_ratio(),
                             config.get_path(config.get_table_elements(table)[carrier_id]),
                             RATIO)
            config.set_value(carrier.get_symbol_rate(),
                             config.get_path(config.get_table_elements(table)[carrier_id]),
                             SYMBOL_RATE)

            if carrier.get_old_category(config) not in access_type_cat.keys():
                access_type_cat[carrier.get_old_category(config)] = []
            access_type_cat[carrier.get_old_category(config)].append(carrier.get_old_access_type())

            groups = ';'.join(str(fmt_grp_id) for fmt_grp_id in
                              carrier.get_fmt_groups())
            config.set_value(groups,
                             config.get_path(config.get_table_elements(table)[carrier_id]),
                             FMT_GROUP)
            carrier_id += 1


        #save fmt
        xpath = get_conf_xpath(FMT_GROUPS, self._link, self._spot, self._gw)
        table = config.get(xpath)

        elmts = config.get_table_elements(table)
        if len(elmts) > len(self._fmt_group):
            for elm in elmts:
                config.del_element(config.get_path(elm));
                table = config.get(xpath)
                elmts = config.get_table_elements(table)
                if len(elmts) == len(self._fmt_group):
                    break
        #Create or delete to have the good number
        elif len(elmts) < len(self._fmt_group):
            for i in range(0, len(self._fmt_group) - len(elmts)):
                config.add_line(config.get_path(table))
                table = config.get(xpath)

        #Save all fmt element
        i = 0
        for grp_id in self._fmt_group:
            config.set_value(grp_id,
                             config.get_path(config.get_table_elements(table)[i]),
                             ID)
            config.set_value(self._fmt_group[grp_id],
                             config.get_path(config.get_table_elements(table)[i]),
                             FMT_ID)
            i += 1

        config.write()
        self._removed = []
        gobject.idle_add(self._update_cb)
        self._dlg.destroy()


    def on_band_configuration_dialog_destroy(self, source=None, event=None):
        """Close the window """
        gobject.idle_add(self._update_cb)
        self._dlg.destroy()

    def on_band_conf_delete_event(self, source=None, event=None):
        """Close the window """
        self._dlg.destroy()

    def get_list_carrier(self):
        return self._list_carrier

