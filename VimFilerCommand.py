# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import os
import os.path
import shutil


# set utf-8 encoding(for japanese language).
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# global variables.
DOT = "."
ENTER_CHAR = "\n"
ROOT_DIR = "/"
PREV_DIR = ".."
HOME_ENV = "HOME"
DELIMITER_DIR = "/"
BUFFER_NAME = "dir.vimfiler"
SYNTAX_FILE = "Packages/SublimeVimFiler/SublimeVimFiler.tmLanguage"
SETTINGS_FILE = "SublimeVimFiler.sublime-settings"


class SettingManager:

    option = {}
    HIDE_DOTFILES_KEY = "hide_dotfiles"
    BOOKMARK_FILE = "bookmark_file"

    @staticmethod
    def init():
        SettingManager.settings = sublime.load_settings(SETTINGS_FILE)

        # load value.
        SettingManager.option[SettingManager.HIDE_DOTFILES_KEY] = \
            SettingManager.settings.get(SettingManager.HIDE_DOTFILES_KEY, "")
        SettingManager.option[SettingManager.BOOKMARK_FILE] = \
            SettingManager.settings.get(SettingManager.BOOKMARK_FILE, "")

    @staticmethod
    def get(key):
        return SettingManager.option.get(key, "")

    @staticmethod
    def set(key, value):
        SettingManager.option[key] = value


class FileSystemManager:

    cur_path = ""

    @staticmethod
    def set_cur_dir(path):
        FileSystemManager.cur_path = os.path.abspath(path)
        sublime.status_message(FileSystemManager.cur_path)

    @staticmethod
    def get_cur_dir():
        return FileSystemManager.cur_path

    @staticmethod
    def get_abs_path(path):
        return FileSystemManager.cur_path + DELIMITER_DIR + path

    @staticmethod
    def get_current_dir_list(dir_path):
        dir_path = os.path.abspath(dir_path)
        list_dir = os.listdir(dir_path)
        list_dir.sort()

        # hide dotfiles.
        list_dir = FileSystemManager.hide_dotfiles(list_dir)

        # if not root dir, insert prev directory.
        if ROOT_DIR != dir_path:
            list_dir.insert(0, PREV_DIR)

        # add "/" for directory.
        list_dir = FileSystemManager.add_dir_delimiter(list_dir)

        return list_dir

    @staticmethod
    def hide_dotfiles(list_dir):
        # check hide_dotfiles settings.
        if True != SettingManager.get(SettingManager.HIDE_DOTFILES_KEY):
            return list_dir

        # hide dotfiles.
        hide_list = []
        for name in list_dir:
            # check beginning dot.
            if False == name.startswith(DOT):
                hide_list.append(name)
        return hide_list

    @staticmethod
    def add_dir_delimiter(dir_list):
        add_dir_list = []

        # add "/" delimiter.
        for dir_name in dir_list:
            tmp_path = FileSystemManager.get_abs_path(dir_name)
            # if direcotry, add "/".
            if FileSystemManager.is_dir(tmp_path):
                dir_name = dir_name + DELIMITER_DIR
            add_dir_list.append(dir_name)
        return add_dir_list

    @staticmethod
    def is_dir(path):
        return os.path.isdir(path)

    @staticmethod
    def is_file(path):
        return os.path.isfile(path)

    @staticmethod
    def is_exist(path):
        return os.path.exists(path)

    @staticmethod
    def is_link(path):
        return os.path.islink(path)

    @staticmethod
    def get_dir_name(path):
        return os.path.dirname(path)

    @staticmethod
    def create_dir(path):
        return os.mkdir(path)

    @staticmethod
    def get_expand_user_path(path):
        return os.path.expanduser(path)


class WriteResult:

    @staticmethod
    def write(view, edit, dir_list):
        # delete all.
        view.erase(edit, sublime.Region(0, view.size()))

        # show result.
        for path in dir_list:
            # check end element.
            if len(dir_list) - 1 != dir_list.index(path):
                view.insert(edit, view.size(), (path + ENTER_CHAR))
            else:
                view.insert(edit, view.size(), (path))

        # cursor move to BOF.
        view.run_command("move_to", {"to": "bof"})

    @staticmethod
    def update_result(view, edit):
        cur_dir = FileSystemManager.get_cur_dir()
        dir_list = FileSystemManager.get_current_dir_list(cur_dir)
        WriteResult.write(view, edit, dir_list)


class VimFilerCommand(sublime_plugin.TextCommand):

    cur_dir_list = []
    cur_path = ""

    def run(self, edit):
        # load settings file.
        SettingManager.init()

        # get current dir list.
        self.cur_path = self.get_current_dir()

        # set current directory.
        FileSystemManager.set_cur_dir(self.cur_path)

        # get current directory list.
        self.cur_dir_list = \
            FileSystemManager.get_current_dir_list(self.cur_path)

        # show result.
        self.show_result(self.cur_dir_list, edit)

    def show_result(self, dir_list, edit):
        output_file = self.get_output_file()

        # show result.
        WriteResult.write(output_file, edit, dir_list)

    def get_output_file(self):
        output_file = self.view.window().new_file()
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
            # update current dir path.
            FileSystemManager.set_cur_dir(path)

            # show result.
            dir_list = FileSystemManager.get_current_dir_list(path)
            WriteResult.write(self.view, edit, dir_list)


class VimFilerOpenPrevDirCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # return when root dir.
        if ROOT_DIR == FileSystemManager.get_cur_dir():
            return

        # get prev dir.
        prev_path = FileSystemManager.get_abs_path(PREV_DIR)
        FileSystemManager.set_cur_dir(prev_path)
        dir_list = FileSystemManager.get_current_dir_list(prev_path)
        WriteResult.write(self.view, edit, dir_list)


class VimFilerOpenHomeDirCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # get home dir.
        home_dir = os.environ[HOME_ENV]
        FileSystemManager.set_cur_dir(home_dir)
        dir_list = FileSystemManager.get_current_dir_list(home_dir)
        WriteResult.write(self.view, edit, dir_list)


class VimFilerOpenFileCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())
        path = ViewManager(self.view).get_abs_path(row)

        # check file.
        if FileSystemManager.is_file(path):
            self.view.window().open_file(path)


class VimFilerRenameCommand(sublime_plugin.TextCommand):

    CAPTION = u'Rename File/Directory'
    ERR_MSG = u'Exist Same File or Directory'
    COMP_MSG = u'Rename Complete'

    def run(self, edit):
        self.edit = edit
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())

        # check prev dir.
        if True == self.is_prevdir(row):
            return

        # show output panel.
        self.src_path = ViewManager(self.view).get_abs_path(row)
        self.show_rename_panel(self.src_path)

    def is_prevdir(self, index):
        cur_path = ViewManager(self.view).get_line(index)

        if cur_path.rstrip(ENTER_CHAR) == (PREV_DIR + DELIMITER_DIR):
            return True
        return False

    def show_rename_panel(self, path):
        window = self.view.window()
        window.show_input_panel(self.CAPTION, path, self.on_done, None, None)

    def on_done(self, dst_path):
        try:
            # rename.
            os.rename(self.src_path, dst_path)
            sublime.status_message(self.COMP_MSG)

            # update page.
            WriteResult.update_result(self.view, self.edit)
        except:
            sublime.message_dialog(self.ERR_MSG)


class VimFilerDeleteCommand(sublime_plugin.TextCommand):

    CAPTION = u'Delete File/Directory'
    COMP_MSG = u'Delete Complete'
    ERR_MSG = u'Not Exist Deleted Path'

    def run(self, edit):
        self.edit = edit
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())

        # check prev dir.
        if True == self.is_prevdir(row):
            return

        # show output panel.
        path = ViewManager(self.view).get_abs_path(row)
        self.show_rename_panel(path)

    def is_prevdir(self, index):
        cur_path = ViewManager(self.view).get_line(index)

        if cur_path.rstrip(ENTER_CHAR) == (PREV_DIR + DELIMITER_DIR):
            return True
        return False

    def show_rename_panel(self, path):
        window = self.view.window()
        window.show_input_panel(self.CAPTION, path, self.on_done, None, None)

    def on_done(self, delete_path):
        # check exist.
        if False == FileSystemManager.is_exist(delete_path):
            sublime.message_dialog(self.ERR_MSG)
            return

        # delete.
        if True == self.delete(delete_path):
            # update.
            sublime.status_message(self.COMP_MSG)
            WriteResult.update_result(self.view, self.edit)

    def delete(self, path):
        is_return = False

        # check directory or file.
        if True == FileSystemManager.is_dir(path) and \
           False == FileSystemManager.is_link(path):
            # check empty.
            dir_list = FileSystemManager.get_current_dir_list(path)
            if 0 == len(dir_list):
                os.rmdir(path)
            else:
                sublime.status_message("DELETE")
                shutil.rmtree(path, True)
            is_return = True
        else:
            os.remove(path)
            is_return = True

        return is_return


class VimFilerCreateFileCommand(sublime_plugin.TextCommand):

    CAPTION = u'Create File'
    COMP_MSG = u'Create File Complete'
    ERR_MSG = u'Create File Error(Same File or Not Exist Path)'

    def run(self, edit):
        # get current directory.
        self.edit = edit
        path = FileSystemManager.get_cur_dir() + DELIMITER_DIR

        # show output panel.
        self.show_rename_panel(path)

    def show_rename_panel(self, path):
        window = self.view.window()
        window.show_input_panel(self.CAPTION, path, self.on_done, None, None)

    def on_done(self, create_file):
        # check exist file.
        if True == FileSystemManager.is_exist(create_file):
            sublime.message_dialog(self.ERR_MSG)
            return

        # create file.
        open(create_file, "w").close()

        # update and open file.
        WriteResult.update_result(self.view, self.edit)
        self.view.window().open_file(create_file)
        sublime.status_message(self.COMP_MSG)


class VimFilerCreateDirCommand(sublime_plugin.TextCommand):

    CAPTION = u'Create Directory'
    COMP_MSG = u'Create Directory Complete'
    ERR_MSG = u'Create Directory Error(Same Directory or Not Exist Path)'

    def run(self, edit):
        # get current directory.
        self.edit = edit
        path = FileSystemManager.get_cur_dir() + DELIMITER_DIR

        # show output panel.
        self.show_rename_panel(path)

    def show_rename_panel(self, path):
        self.view.window().show_input_panel(self.CAPTION, path, self.on_done,
                                            None, None)

    def on_done(self, create_dir):
        # create directory.
        try:
            FileSystemManager.create_dir(create_dir)

            # update and open file.
            WriteResult.update_result(self.view, self.edit)
            sublime.status_message(self.COMP_MSG)
        except:
            sublime.message_dialog(self.ERR_MSG)


class VimFilerMoveCommand(sublime_plugin.TextCommand):

    ARROW = u' ->'
    ARROW_SUFFIX = u'>'
    CAPTION = u'Move File/Directory'
    COMP_MSG = u'Move File/Directory Complete'
    ERR_MSG = u'Move File/Directory Error(Not Exist Path)'
    ERR_MOVE_MSG = u'Not Exist Src File or Dst is not Directory'

    def run(self, edit):
        # get specified file/directory.
        self.edit = edit
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())
        self.src_path = ViewManager(self.view).get_abs_path(row)

        # create move message.
        msg = self.create_move_message(self.src_path)

        # show output panel.
        self.show_rename_panel(msg)

    def create_move_message(self, src_path):
        return src_path + self.ARROW + src_path

    def show_rename_panel(self, path):
        window = self.view.window()
        window.show_input_panel(self.CAPTION, path, self.on_done, None, None)

    def on_done(self, move_msg):
        # check ARROW string.
        if False == (self.ARROW in move_msg):
            return

        # split dst_path
        dst_path = move_msg.split(self.ARROW_SUFFIX)[1]

        # check src_path and dst_path.
        if False == self.check_path(self.src_path, dst_path):
            sublime.message_dialog(self.ERR_MOVE_MSG)
            return

        # move.
        shutil.move(self.src_path, dst_path)

        # update.
        WriteResult.update_result(self.view, self.edit)
        sublime.status_message(self.COMP_MSG)

    def check_path(self, src_path, dst_path):
        # check src_path is exist.
        if False == FileSystemManager.is_exist(src_path):
            return False
        # check dst_path is directory.
        if False == FileSystemManager.is_dir(dst_path):
            return False


class VimFilerAppearOrHideDotfilesCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # get change status.
        change_status = self.get_change_status()

        # change settings.
        SettingManager.set(SettingManager.HIDE_DOTFILES_KEY, change_status)

        # update.
        WriteResult.update_result(self.view, edit)

    def get_change_status(self):
        # get current status.
        cur_status = SettingManager.get(SettingManager.HIDE_DOTFILES_KEY)
        change_status = True

        # change status.
        if True == cur_status:
            change_status = False
        return change_status


class VimFilerRefreshCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # update.
        WriteResult.update_result(self.view, edit)


class VimFilerAddBookmarkCommand(sublime_plugin.TextCommand):

    COMP_MSG = u'Complete Regist Bookmark: '
    ERR_MSG = u'Exist Same Bookmark: '
    ERR_OPEN_MSG = u'Not Exist Bookmark File: '

    def run(self, edit):
        # regist bookmark.
        cur_dir = FileSystemManager.get_cur_dir()
        try:
            if True == self.regist(cur_dir):
                sublime.status_message(self.COMP_MSG + cur_dir)
            else:
                sublime.message_dialog(self.ERR_MSG + cur_dir)
        except:
            file_name = SettingManager.get(SettingManager.BOOKMARK_FILE)
            sublime.message_dialog(self.ERR_OPEN_MSG + file_name)

    def regist(self, bookmark):
        is_regist = False

        # get bookmark file.
        file_name = SettingManager.get(SettingManager.BOOKMARK_FILE)

        # open file.
        f = open(FileSystemManager.get_expand_user_path(file_name), "a+")

        # check same bookmark.
        lines = f.readlines()
        if False == self.check_same_bookmark(lines, bookmark + ENTER_CHAR):
            # write bookmark at end of file.
            is_regist = True
            f.seek(0, 2)
            f.write(bookmark + ENTER_CHAR)
        # close file.
        f.close()

        return is_regist

    def check_same_bookmark(self, bookmark_list, bookmark):
        if True == (bookmark in bookmark_list):
            return True
        return False


class VimFilerOpenBookmarkCommand(sublime_plugin.TextCommand):

    INVALID_INDEX = -1

    def run(self, edit):
        self.edit = edit

        # get bookmark.
        bookmark_list = self.get_bookmark_list()

        # show quick panel.
        self.show_quick_panel(bookmark_list)

    def get_bookmark_list(self):
        file_name = SettingManager.get(SettingManager.BOOKMARK_FILE)
        f = open(FileSystemManager.get_expand_user_path(file_name), "r")
        bookmark_list = f.readlines()
        f.close()
        return bookmark_list

    def show_quick_panel(self, bookmark_list):
        window = self.view.window()
        window.show_quick_panel(bookmark_list, self.on_done)

    def on_done(self, index):
        # quick pane is canceled.
        if self.INVALID_INDEX == index:
            return

        # get specified index.
        bookmark_list = self.get_bookmark_list()
        bookmark = bookmark_list[index].rstrip(ENTER_CHAR)

        # update current directory.
        FileSystemManager.set_cur_dir(bookmark)

        # open bookmark directory.
        dir_list = FileSystemManager.get_current_dir_list(bookmark)
        WriteResult.write(self.view, self.edit, dir_list)
