# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import os
import shutil
import datetime
import unicodedata
import pwd
import stat
import mimetypes
import subprocess
import re
import threading

# set utf-8 encoding(for japanese language).
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# global variables.
UTF8 = "utf-8"
DOT = "."
SPACE_CHAR = " "
ENTER_CHAR = "\n"
PREV_DIR = ".."
ROOT_DIR = "/"
HOME_ENV = "HOME"
DELIMITER_DIR = os.sep
UPDATE_TIME_DELIMITER = ","
UPDATE_TIME_FORMAT = "%y-%m-%d %H:%M:%S"
UPDATE_TIME_LEN = 17
MARGIN = 6
PERMISSION_SPACE = 2
BUFFER_NAME = "dir.vimfiler"
SYNTAX_FILE = "Packages/SublimeVimFiler/SublimeVimFiler.tmLanguage"
SETTINGS_FILE = "SublimeVimFiler.sublime-settings"
OWNER_INDEX = 0
PERMISIION_INDEX = 1
UPDATE_TIME_INDEX = 2
READ_BIT = 4
WRITE_BIT = 2
EXECUTE_BIT = 1


class ProcessTime:

    @staticmethod
    def get_time():
        import time
        return time.time() * 1000


class MimeTypeManager:

    PDF_MIMETYPE = "pdf"
    WORD_MIMETYPE = "word"
    EXCEL_MIMETYPE = "excel"
    POWER_POINT_MIMETYPE = "powerpoint"
    PRESENTATION_MIMETYPE = "officedocument.presentationml"
    SPREAD_SHEET_MIMETYPE = "officedocument.spreadsheetml"
    MIND_MAP_MIMETYPE = "mindmap"
    CHM_MIMETYPE = "chemdraw"
    TEXT_MIMETYPE = "text"

    @staticmethod
    def get_mime_type(abs_path):
        types, sub_type = mimetypes.guess_type(abs_path)
        mime_type = MimeTypeManager.TEXT_MIMETYPE

        # check mime type.
        if None != types:
            if MimeTypeManager.PDF_MIMETYPE in types:
                mime_type = MimeTypeManager.PDF_MIMETYPE
            elif MimeTypeManager.WORD_MIMETYPE in types:
                mime_type = MimeTypeManager.WORD_MIMETYPE
            elif (MimeTypeManager.EXCEL_MIMETYPE) in types or (MimeTypeManager.SPREAD_SHEET_MIMETYPE in types):
                mime_type = MimeTypeManager.EXCEL_MIMETYPE
            elif (MimeTypeManager.POWER_POINT_MIMETYPE) in types or (MimeTypeManager.PRESENTATION_MIMETYPE in types):
                mime_type = MimeTypeManager.POWER_POINT_MIMETYPE
            elif MimeTypeManager.CHM_MIMETYPE in types:
                mime_type = MimeTypeManager.CHM_MIMETYPE
        else:
            if os.path.splitext(abs_path)[1] in SettingManager.get(SettingManager.MIND_MAP_EX):
                mime_type = MimeTypeManager.MIND_MAP_MIMETYPE
        return mime_type


class SettingManager:

    option = {}
    HIDE_DOTFILES_KEY = "hide_dotfiles"
    BOOKMARK_FILE = "bookmark_file"
    LIMIT_LEN = "limit_length"
    PDF_COMMAND = "pdf"
    OFFICE_COMMAND = "office"
    MIND_MAP_COMMAND = "mind_map"
    MIND_MAP_EX = "mind_map_ex"
    CHM_COMMAND = "chm"

    @staticmethod
    def init():
        SettingManager.settings = sublime.load_settings(SETTINGS_FILE)

        # load value.
        SettingManager.option[SettingManager.HIDE_DOTFILES_KEY] = \
            SettingManager.settings.get(SettingManager.HIDE_DOTFILES_KEY, True)
        SettingManager.option[SettingManager.BOOKMARK_FILE] = \
            SettingManager.settings.get(SettingManager.BOOKMARK_FILE, "")
        SettingManager.option[SettingManager.LIMIT_LEN] = \
            SettingManager.settings.get(SettingManager.LIMIT_LEN, 40)
        SettingManager.option[SettingManager.PDF_COMMAND] = \
            SettingManager.settings.get(SettingManager.PDF_COMMAND, "")
        SettingManager.option[SettingManager.OFFICE_COMMAND] = \
            SettingManager.settings.get(SettingManager.OFFICE_COMMAND, "")
        SettingManager.option[SettingManager.MIND_MAP_COMMAND] = \
            SettingManager.settings.get(SettingManager.MIND_MAP_COMMAND, "")
        SettingManager.option[SettingManager.MIND_MAP_EX] = \
            SettingManager.settings.get(SettingManager.MIND_MAP_EX, "")
        SettingManager.option[SettingManager.CHM_COMMAND] = \
            SettingManager.settings.get(SettingManager.CHM_COMMAND, "")

    @staticmethod
    def get(key):
        return SettingManager.option.get(key, "")

    @staticmethod
    def set(key, value):
        SettingManager.option[key] = value


class Utility:

    WFA = u'WFA'

    @staticmethod
    def string_width(string):
        return sum([Utility.__get_char_width(c) for c in string])

    @staticmethod
    def __get_char_width(c):
        char_width = unicodedata.east_asian_width(c)
        return 2 if (char_width in Utility.WFA) else 1

    @staticmethod
    def get_char_num(string):
        char_len = 0
        width = 0
        limit = SettingManager.get(SettingManager.LIMIT_LEN)
        for c in string:
            width = width + Utility.__get_char_width(c)
            if width < limit:
                char_len = char_len + 1
            else:
                break
        return char_len

    @staticmethod
    def rm_dir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            [os.remove(os.path.join(root, name)) for name in files]
            [os.rmdir(os.path.join(root, name)) for name in dirs]
        os.rmdir(path)

    @staticmethod
    def rcopy_file(src_path, dst_path):
        # create root directory.
        dst_root = src_path.rstrip(DELIMITER_DIR)
        dst_root = dst_root.split(DELIMITER_DIR)
        dst_root = dst_root[len(dst_root) - 1]
        dst_root = os.path.join(dst_path, dst_root)

        # check exist directory.
        if False == FileSystemManager.is_exist(dst_root):
            FileSystemManager.create_dir(dst_root)

        # copy file.
        for src_root, dirs, files in os.walk(src_path):
            # create dst directory.
            dst = os.path.join(dst_root, src_root.replace(src_path, ''))
            if False == FileSystemManager.is_exist(dst):
                FileSystemManager.create_dir(dst)
            # copy file.
            for file in files:
                copy_src = os.path.join(src_root, file)
                copy_dst = os.path.join(dst, file)
                shutil.copy2(copy_src, copy_dst)


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
        return os.path.join(FileSystemManager.cur_path, path)

    @staticmethod
    def get_current_dir_list(dir_path):
        # create directory dict.
        dir_path = os.path.abspath(dir_path)
        dir_dict = FileSystemManager.create_dict_list(dir_path)

        # hide dotfiles.
        dir_dict = FileSystemManager.hide_dot_files(dir_dict)
        return dir_dict

    @staticmethod
    def create_dict_list(path):
        list_dir = os.listdir(path.decode(UTF8))
        return dict([(FileSystemManager.__get_dir_tuple(n)) for n in list_dir])

    @staticmethod
    def __get_dir_tuple(dir_name):
        abs_path = FileSystemManager.get_abs_path(dir_name)
        # if directory, add "/".
        if FileSystemManager.is_dir(abs_path):
            dir_name = dir_name + DELIMITER_DIR
        return dir_name, FileSystemManager.__get_dir_info(abs_path)

    @staticmethod
    def __get_dir_info(abs_path):
        owner = FileSystemManager.__get_owner(abs_path)
        permission = FileSystemManager.__get_per_info(abs_path)
        update_time = FileSystemManager.__get_update_time(abs_path)
        return [owner, permission, update_time]

    @staticmethod
    def __get_owner(abs_path):
        return FileSystemManager.get_owner(abs_path)

    @staticmethod
    def __get_per_info(abs_path):
        return FileSystemManager.get_permission(abs_path)

    @staticmethod
    def __get_update_time(abs_path):
        return FileSystemManager.get_update_time(abs_path)

    @staticmethod
    def hide_dot_files(dir_dict):
        # check hide_dotfiles settings.
        if True != SettingManager.get(SettingManager.HIDE_DOTFILES_KEY):
            return dir_dict
        return dict([(k, v) for k, v in dir_dict.items() if False == k.startswith(DOT)])

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

    @staticmethod
    def get_update_time(path):
        last_modified = os.stat(path).st_mtime
        return datetime.datetime.fromtimestamp(last_modified).strftime(UPDATE_TIME_FORMAT)

    @staticmethod
    def get_permission(path):
        per = oct(stat.S_IMODE(os.stat(path)[stat.ST_MODE]))
        return FileSystemManager.convert_permission(per[-4:])

    @staticmethod
    def convert_permission(permission):
        # convert permission.
        p = [FileSystemManager.__get_permission(bit) for bit in permission[1:]]
        return ''.join(p)

    @staticmethod
    def __get_permission(bit):
        n = int(bit, 10)
        return ("r" if READ_BIT & n else "-") + ("w" if WRITE_BIT & n else "-") + ("x" if EXECUTE_BIT & n else "-")

    @staticmethod
    def get_owner(path):
        return pwd.getpwuid(os.stat(path)[stat.ST_UID])[0]

    @staticmethod
    def sort_dir_dict(dir_dict):
        return sorted(dir_dict.items())

    @staticmethod
    def sort_dir_dict_key(dir_dict):
        return sorted(dir_dict.keys())


class WriteResult:

    @staticmethod
    def write(view, edit, dir_dict):
        # get width of view.
        w = int(view.viewport_extent()[0] / view.em_width())
        view.erase(edit, sublime.Region(0, view.size()))

        # write result.
        dir_list = FileSystemManager.sort_dir_dict_key(dir_dict)
        end_name = dir_list[len(dir_list) - 1]
        [WriteResult.__write(view, edit, w, k, v, end_name) for k, v in FileSystemManager.sort_dir_dict(dir_dict)]

        # cursor move to BOF.
        view.run_command("move_to", {"to": "bof"})

    @staticmethod
    def __write(view, edit, width, dir_name, info, end_dir_name):
        owner = info[OWNER_INDEX]
        per = info[PERMISIION_INDEX]
        update_time = info[UPDATE_TIME_INDEX]

        # get write dir name.
        write_dir = WriteResult.__get_dir_string(dir_name, width)

        # create insert string.
        space_num = WriteResult.__get_space_num(width, [write_dir, owner, per, update_time])
        w_str = write_dir + (space_num * SPACE_CHAR) + owner + (SPACE_CHAR) + per + (SPACE_CHAR) + update_time

        # write string.
        if dir_name != end_dir_name:
            view.insert(edit, view.size(), w_str + ENTER_CHAR)
        else:
            view.insert(edit, view.size(), w_str)

    @staticmethod
    def __get_dir_string(dir_name, width):
        char_len = Utility.get_char_num(dir_name)
        char_len_width = Utility.string_width(dir_name[:char_len].decode(UTF8))

        # check char len is over display width(3/5).
        limit_width = int(width * 3 / 5)
        if char_len_width > limit_width:
            # decrease ten characters.
            return WriteResult.__get_dir_string(dir_name[:(char_len - 10)], width)
        return dir_name[:char_len].decode(UTF8)

    @staticmethod
    def __get_space_num(width, write_list):
        return width - sum([Utility.string_width(string.decode(UTF8)) for string in write_list]) - MARGIN

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
        FileSystemManager.set_cur_dir(self.cur_path)

        # get current directory list.
        self.cur_dir_list = FileSystemManager.get_current_dir_list(self.cur_path)

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

    def get_target_view(self):
        views = self.view.window().views()
        for v in views:
            if BUFFER_NAME == v.name():
                return v
        return None


class ViewManager:

    def __init__(self, view):
        cur_dir = FileSystemManager.get_cur_dir()
        dir_dict = FileSystemManager.get_current_dir_list(cur_dir)
        self.dir_list = FileSystemManager.sort_dir_dict_key(dir_dict)
        # read all view string.
        #view.substr(sublime.Region(0, view.size())).split("\n")

    def get_line_dir(self, index):
        return self.dir_list[index]

    def get_abs_path(self, index):
        return FileSystemManager.get_abs_path(self.get_line_dir(index))


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
            self.open(path.decode(UTF8))

    def open(self, abs_path):
        # open file by file mime types.
        mime_type = MimeTypeManager.get_mime_type(abs_path)
        if MimeTypeManager.EXCEL_MIMETYPE == mime_type or MimeTypeManager.WORD_MIMETYPE == mime_type or \
           MimeTypeManager.POWER_POINT_MIMETYPE == mime_type:
            command = SettingManager.get(SettingManager.OFFICE_COMMAND)
            subprocess.Popen([command, abs_path])
        elif MimeTypeManager.PDF_MIMETYPE == mime_type:
            command = SettingManager.get(SettingManager.PDF_COMMAND)
            subprocess.Popen([command, abs_path])
        elif MimeTypeManager.MIND_MAP_MIMETYPE == mime_type:
            command = SettingManager.get(SettingManager.MIND_MAP_COMMAND)
            subprocess.Popen([command, abs_path])
        elif MimeTypeManager.CHM_MIMETYPE == mime_type:
            command = SettingManager.get(SettingManager.CHM_COMMAND)
            subprocess.Popen([command, abs_path])
        else:
            self.view.window().open_file(abs_path)

    def create_command(self, command, abs_path):
        return '"' + command + SPACE_CHAR + abs_path + '"'


class VimFilerRenameCommand(sublime_plugin.TextCommand):

    CAPTION = u'Rename File/Directory'
    ERR_MSG = u'Exist Same File or Directory'
    COMP_MSG = u'Rename Complete'

    def run(self, edit):
        self.edit = edit
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())

        # show output panel.
        self.src_path = ViewManager(self.view).get_abs_path(row)
        self.show_rename_panel(self.src_path)

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

        # show output panel.
        path = ViewManager(self.view).get_abs_path(row)
        self.show_rename_panel(path)

    def show_rename_panel(self, path):
        window = self.view.window()
        window.show_input_panel(self.CAPTION, path, self.on_done, None, None)

    def on_done(self, delete_path):
        # check exist.
        if False == FileSystemManager.is_exist(delete_path):
            sublime.message_dialog(self.ERR_MSG)
            return

        # delete.
        self.delete(delete_path)
        sublime.status_message(self.COMP_MSG)
        WriteResult.update_result(self.view, self.edit)

    def delete(self, path):
        # check directory or file.
        if True == FileSystemManager.is_dir(path) and False == FileSystemManager.is_link(path):
            Utility.rm_dir(path)
        else:
            os.remove(path)


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
        msg = self.create_message(self.src_path)

        # show output panel.
        self.show_panel(msg)

    def create_message(self, src_path):
        return src_path + self.ARROW + src_path

    def show_panel(self, path):
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
        return True


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

        # delete empty line.
        lines = f.readlines()
        f.close()
        return [mark for mark in lines if ENTER_CHAR != mark]

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

        # check exist path.
        if True == FileSystemManager.is_exist(bookmark):
            # update current directory.
            FileSystemManager.set_cur_dir(bookmark)

            # open bookmark directory.
            dir_list = FileSystemManager.get_current_dir_list(bookmark)
            WriteResult.write(self.view, self.edit, dir_list)


class VimFilerEditBookmarkCommand(sublime_plugin.TextCommand):

    INVALID_INDEX = -1

    def run(self, edit):
        # get bookmark file.
        bookmark_file = SettingManager.get(SettingManager.BOOKMARK_FILE)
        bookmark_path = FileSystemManager.get_expand_user_path(bookmark_file)
        sublime.status_message(bookmark_path)
        # open bookmark file.
        self.view.window().open_file(bookmark_path)


class VimFilerCopyCommand(sublime_plugin.TextCommand):

    ARROW = u' ->'
    ARROW_SUFFIX = u'>'
    DST_SUFFIX = u'.copy'
    CAPTION = u'Copy File/Directory'
    COMP_MSG = u'Copy File/Directory Complete'
    ERR_MSG = u'Copy Error(Not Exist Path)'

    def run(self, edit):
        # get specified file/directory.
        self.edit = edit
        (row, col) = self.view.rowcol(self.view.sel()[0].begin())
        self.src_path = ViewManager(self.view).get_abs_path(row)

        # create copy message.
        msg = self.create_message(self.src_path)

        # show output panel.
        self.show_panel(msg)

    def create_message(self, src_path):
        return src_path + self.ARROW + src_path

    def show_panel(self, path):
        window = self.view.window()
        window.show_input_panel(self.CAPTION, path, self.on_done, None, None)

    def on_done(self, copy_msg):
        # check ARROW string.
        if False == (self.ARROW in copy_msg):
            return

        # check src_path and dst_path.
        if False == FileSystemManager.is_exist(self.src_path):
            sublime.message_dialog(self.ERR_MSG)
            return

        # split dst_path
        dst_path = copy_msg.split(self.ARROW_SUFFIX)[1]
        dst_path = self.get_dst_path(dst_path)

        # copy.
        try:
            self.copy(dst_path)
            WriteResult.update_result(self.view, self.edit)
            sublime.status_message(self.COMP_MSG)
        except:
            sublime.message_dialog(self.ERR_MSG)

    def copy(self, dst_path):
        if True == FileSystemManager.is_file(self.src_path):
            shutil.copy2(self.src_path, dst_path)
        elif True == FileSystemManager.is_dir(self.src_path):
            if False == FileSystemManager.is_exist(dst_path):
                # copy tree.
                shutil.copytree(self.src_path, dst_path, True)
            else:
                Utility.rcopy_file(self.src_path, dst_path)

    def get_dst_path(self, dst_path):
        # check src_path equal dst path.
        if self.src_path == dst_path:
            if True == FileSystemManager.is_dir(dst_path):
                dst_path = self.src_path.rstrip(DELIMITER_DIR)
                dst_path = dst_path + self.DST_SUFFIX
            else:
                dst_path = self.src_path + self.DST_SUFFIX
        return dst_path


class VimFilerGrepCommand(sublime_plugin.TextCommand):

    INVALID_INDEX = -1
    DEFAULT_PATTERN = u'.*'
    CAPTION = u'Grep File'
    COMP_MSG = u'Grep File Complete'
    GREP_PROCESS_MSG = u'Grep Process...............'

    def run(self, edit):
        self.edit = edit
        self.show_panel()

    def show_panel(self):
        window = self.view.window()
        window.show_input_panel(self.CAPTION, self.DEFAULT_PATTERN, self.on_input_done, None, None)

    def on_input_done(self, pattern):
        # grep start(in sub thread).
        thread = threading.Thread(target=self.start_thread, args=(pattern,))
        thread.start()

    def start_thread(self, pattern):
        # start grep.
        sublime.set_timeout(lambda: sublime.status_message(self.GREP_PROCESS_MSG), 50)
        self.search_list = self.get_search_list(pattern)

        # show grep result in quick panel.
        sublime.set_timeout(lambda: sublime.status_message(self.COMP_MSG), 50)
        sublime.set_timeout(lambda: self.view.window().show_quick_panel(self.search_list, self.on_selected_done), 50)

    def get_search_list(self, pattern):
        search_list = []
        # recursive search.
        for root, dirs, files in os.walk(FileSystemManager.get_cur_dir()):
            for f in files:
                f_path = os.path.join(root, f)
                # check pattern matching.
                if None != re.search(pattern, f_path, re.IGNORECASE):
                    search_list.append(f_path)
        return search_list

    def on_selected_done(self, index):
        if self.INVALID_INDEX == index:
            return

        # open file.
        find_path = self.search_list[index]
        if True == FileSystemManager.is_file(find_path):
            self.view.window().open_file(find_path)
