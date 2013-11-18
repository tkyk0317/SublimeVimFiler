# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import os
import os.path


# set utf-8 encoding(for japanese language).
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# global variables.
ROOT_DIR = "/"
PREV_DIR = "../"
HOME_DIR = "HOME"
DELIMITER_DIR = "/"
BUFFER_NAME = "dir.vimfiler"
SYNTAX_FILE = "Packages/SublimeVimFiler/SublimeVimFiler.tmLanguage"


class FileSystemManager:

    cur_path = ""

    @staticmethod
    def set_cur_dir(path):
        FileSystemManager.cur_path = path

    @staticmethod
    def get_cur_dir():
        return FileSystemManager.cur_path

    @staticmethod
    def get_abs_path(path):
        return FileSystemManager.cur_path + DELIMITER_DIR + path

    @staticmethod
    def get_current_dir_list(dir_path):
        list_dir = os.listdir(dir_path)
        list_dir.sort()

        # if not root dir, insert prev directory.
        if ROOT_DIR != dir_path:
            list_dir.insert(0, PREV_DIR)
        return list_dir

    @staticmethod
    def is_dir(path):
        return os.path.isdir(path)

    @staticmethod
    def is_file(path):
        return os.path.isfile(path)


class WriteResult:

    @staticmethod
    def write(view, edit, dir_list):
        # delete all.
        view.erase(edit, sublime.Region(0, view.size()))

        # show result.
        for path in dir_list:
            view.insert(edit, view.size(), (path + "\n"))

        # cursor move to BOF.
        view.run_command("move_to", {"to": "bof"})


class VimFilerCommand(sublime_plugin.TextCommand):

    cur_dir_list = []
    cur_path = ""

    def __init__(self, view):
        super(VimFilerCommand, self).__init__(view)
        self.window = self.view.window()

    def run(self, edit):
        # show quick panel.
        self.cur_path = self.get_current_dir()
        self.cur_dir_list = \
            FileSystemManager.get_current_dir_list(self.cur_path)
        self.show_result(self.cur_dir_list, edit)

        # set current directory.
        FileSystemManager.set_cur_dir(self.cur_path)

    def show_result(self, dir_list, edit):
        output_file = self.get_output_file()

        # show result.
        WriteResult.write(output_file, edit, dir_list)

    def get_output_file(self):
        output_file = self.window.new_file()
        output_file.set_syntax_file(SYNTAX_FILE)
        output_file.set_name(BUFFER_NAME)
        output_file.set_scratch(True)
        return output_file

    def get_current_dir(self):
        file_name = self.view.file_name()

        # return root dir when file_name is None.
        if None == file_name:
            return ROOT_DIR
        else:
            return os.path.dirname(file_name)


class ViewManager:

    def __init__(self, view):
        self.view_string = \
            view.substr(sublime.Region(0, view.size())).split("\n")

    def get_line(self, index):
        return self.view_string[index]

    def get_abs_path(self, index):
        return FileSystemManager.get_abs_path(self.get_line(index))


class VimFilerOpenDirCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # get path of current line.
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())
        path = ViewManager(self.view).get_abs_path(row)

        # write directory list.
        if FileSystemManager.is_dir(path):
            # show result.
            dir_list = FileSystemManager.get_current_dir_list(path)
            WriteResult.write(self.view, edit, dir_list)

            # update current dir path.
            FileSystemManager.set_cur_dir(path)


class VimFilerOpenPrevDirCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # return when root dir.
        if ROOT_DIR == FileSystemManager.get_cur_dir():
            return

        # get prev dir.
        prev_path = FileSystemManager.get_abs_path(PREV_DIR)
        dir_list = FileSystemManager.get_current_dir_list(prev_path)
        WriteResult.write(self.view, edit, dir_list)

        # update current dir path.
        FileSystemManager.set_cur_dir(prev_path)


class VimFilerOpenHomeDirCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # get home dir.
        home_dir = os.environ[HOME_DIR]
        print home_dir
        dir_list = FileSystemManager.get_current_dir_list(home_dir)
        WriteResult.write(self.view, edit, dir_list)

        # update current dir path.
        FileSystemManager.set_cur_dir(home_dir)


class VimFilerOpenFileCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())
        path = ViewManager(self.view).get_abs_path(row)

        # check file.
        if FileSystemManager.is_file(path):
            self.view.window().open_file(path)
