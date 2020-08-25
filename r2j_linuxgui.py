#!/usr/bin/env python3

# Requirement: python-gobject
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from threading import Thread
import io
import os
import signal
import subprocess


arguments = {
    '--archive' : 'archives/copies all RAW-files (recursive, maintains folder structure)',
    '--enhance' : 'remove bad pixels',
    '--force' : 'force conversion and overwrite existing files',
    '--group-enhance' : 'remove bad pixels by comparing different images with the same light setting (overwrites -e)',
    '--quiet' : 'do not show any output',
    '--recursive' : 'convert files in subfolders recursively',
    '--stupid' : 'turns on stupid mode - other files do not get copied automatically',
    '--tiff' : 'converts into tiffs instead of jpgs',
    '--auto-wb' : 'uses automatic white balance instead of the cameras white balance',
}

class Application(Gtk.Window):
    def __init__(self, binpath='raw-to-jpg'):
        super().__init__()
        Gtk.Window.__init__(self, title='raw2jpg')
        self.set_border_width(10)
        self.connect('delete-event', quit_application)

        self.input_path = self.output_path = None
        self.output_buffer = ''
        self.binpath = binpath
        self.subproc = None

        header = Gtk.HeaderBar(title='RAW2JPG')
        header.set_subtitle('Convert RAW to JPG')
        header.props.show_close_button = True
        self.set_titlebar(header)

        # Create UI elements
        self.main_box = Gtk.ListBox()
        self.input_button = Gtk.Button(label='Select files to convert')
        self.output_button = Gtk.Button(label='Select output destination')
        self.confirm_button = Gtk.Button(label='Let\'s go...')
        self.button_box = Gtk.Box(spacing=5)
        self.flag_box = Gtk.FlowBox()
        self.create_flag_box()
        self.output_label = Gtk.Label()
        self.scrolled_window = Gtk.ScrolledWindow()

        self.main_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flag_box.set_valign(Gtk.Align.START)
        self.flag_box.set_max_children_per_line(30)
        self.flag_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.output_label.set_justify(Gtk.Justification.LEFT)
        self.output_label.set_halign(Gtk.Align.START)
        self.output_label.set_use_markup(False)
        self.scrolled_window.set_min_content_height(500)

        # Connect events
        self.input_button.connect('clicked', self.on_button_clicked)
        self.output_button.connect('clicked', self.on_button_clicked)
        self.confirm_button.connect('clicked', self.on_button_clicked)

        # Compose UI
        self.button_box.pack_start(self.input_button, True, True, 0)
        self.button_box.pack_start(self.output_button, True, True, 0)
        self.scrolled_window.add(self.output_label)
        self.main_box.add(self.button_box)
        self.main_box.add(self.flag_box)
        self.main_box.add(self.confirm_button)
        self.main_box.add(self.scrolled_window)
        self.add(self.main_box)

        self.show_all()

    def create_flag_box(self):
        self.checkboxes = {}
        for key in arguments.keys():
            checkbox = Gtk.CheckButton(label=arguments[key])
            self.checkboxes[checkbox] = key
            self.flag_box.add(checkbox)

    def folder_selector_dialog(self, title):
        dialog = Gtk.FileChooserDialog(
        title=title, parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        response = dialog.run()
        filename = dialog.get_filename()

        dialog.destroy()
        return response, filename

    def get_arguments(self):
        arguments = []
        for checkbox in self.checkboxes.keys():
            if checkbox.get_active():
                arguments.append(self.checkboxes[checkbox])
        return arguments

    def open_subprocess(self):
        self.output_buffer = ''
        args = [ self.input_path, self.output_path ] + self.get_arguments()
        print(args)
        self.subproc = subprocess.Popen(['python', '-u', self.binpath] + args, stdout=subprocess.PIPE)
        for line in io.TextIOWrapper(self.subproc.stdout, encoding='utf-8'):
            self.output_buffer += line
            self.output_label.set_text(self.output_buffer)

    def error_dialog(self, text, secondary_text):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CANCEL,
            text=text,
        )
        dialog.format_secondary_text(secondary_text)
        dialog.run()
        dialog.destroy()

    def confirm_dialog(self, text, secondary_text):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=text,
        )
        dialog.format_secondary_text(secondary_text)
        response = dialog.run()
        dialog.destroy()
        return response

    def on_button_clicked(self, source):
        if source == self.confirm_button:
            if self.input_path == None \
                    or not os.path.isdir(self.input_path):
                self.error_dialog('No input path', 'You have to select a directory with files to convert.')
            elif self.output_path == None \
                    or not os.path.isdir(self.output_path):
                self.error_dialog('No output path', 'You have to select a directory where the converted files can go.')

            Thread(target=self.open_subprocess).start()
        elif source == self.input_button:
            response, filename = self.folder_selector_dialog('Select folder to convert')
            if response == Gtk.ResponseType.OK:
                self.input_button.set_label(filename)
                self.input_path = filename
        elif source == self.output_button:
            response, filename = self.folder_selector_dialog('Select an output folder')
            if response == Gtk.ResponseType.OK:
                self.output_button.set_label(filename)
                self.output_path = filename

def quit_application(app, event):
    if not app.subproc == None and app.subproc.returncode == None:
        response = app.confirm_dialog('A process is still running', 'Do you want to kill the process and exit?')
        if response == Gtk.ResponseType.OK:
            app.subproc.send_signal(signal.SIGINT)
            print('Killed subprocess')
        else:
            return True
    Gtk.main_quit(app)

def main(binpath='raw-to-jpg'):
    win = Application(binpath)

    # Go into gtk min loop
    Gtk.main()
