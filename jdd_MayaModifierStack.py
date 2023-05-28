from typing import *

import maya.cmds as cmds
import maya.mel as mel
from pymel.all import Callback

current_selection = cmds.ls(sl=True)


def msg(_task: str, _query: int, _type: str = "l", _data: str = ""):
    if _type == "l":
        log = [
            f"[{_task}] -- Initiating task... --",  # 0
            f"[{_task}] -- Validating Stack... --",  # 1
            f"[{_task}] -- Creating new modifier object... --",  # 2
            f"[{_task}] -- Task ignored --",  # -1
        ]
        return log[_query]
    elif _type == "r":
        res = [
            f"[{_task}] -- Operation Success --",  # 0
            f"[{_task}] -- Stack missing --",  # 1
            f"[{_task}] -- Stack name invalid --",  # 2
            f"[{_task}] -- Value cannot be lower than 0 (Currently {_data}) --",  # 3
            f"[{_task}] -- Unknown Error --"  # -1
        ]
        return res[_query]
    elif _type == "i":
        info = [
            f"[{_task}] -- OP MSG --",  # 0
            f"[{_task}] -- Stack already exists --",  # 1
            f"[{_task}] -- Stack initialized, adding Layer 00 to stack... --",  # 2
            f"[{_task}] -- Using provided layer {_data} --",  # 3
        ]
        return info[_query]


class RunMel:
    def __init__(self, command: str):
        print("Running MEL script \"" + command + "\"...")
        self._cmd = dict(
            createRef="bt_duplicateMeshReference",
        )

        self.eval_command(self._cmd[command])

    def eval_command(self, _cmd: str):
        try:
            res = mel.eval(_cmd)
            print(msg("RunMel", 0, "r"))
            return res
        except Exception:
            print(msg("RunMel", -1, "r"))
            return None


class LayerMgr:
    def __init__(self, _selection):
        self.stack_label = "_ModStack"
        self.layer_label = "_ModLayer"
        self.modifier_label = "_ModObject"

        self.sl = _selection

        if len(self.sl) != 1:
            cmds.error("Selection is not one object.")
        else:
            self.sl = self.sl[0]
        print(msg("update_init_obj", 0, "l"))
        if self.sl.find(self.modifier_label) != -1:
            self.init_obj = self.sl.split(self.modifier_label)[0]
        elif self.sl.find(self.layer_label) != -1:
            cmds.error("Selection must be a mesh object or a mesh modifier object.")
        elif self.sl.find(self.stack_label) != -1:
            cmds.error("Selection must be a mesh object or a mesh modifier object.")
        else:
            self.init_obj = self.sl

        self.stack_name = self.init_obj + self.stack_label
        self.layer_name = self.init_obj + self.layer_label
        self.modifier_name = self.init_obj + self.modifier_label

        self.stack_active = self.stack_name
        self.layer_active = self.layer_name + "00"

        self.state_visible = True
        self.state_interact = True

        print("---- INIT VARIABLES ----")
        print("Selection: ", self.sl)
        print("Initial Object: ", self.init_obj)
        print("Stack Name: ", self.stack_name)
        print("Layer Name: ", self.layer_name)
        print("Modifier Name: ", self.modifier_name)
        print("---- CODE EXECUTION ----")

        self.add_stack()

    def len_layers(self, stack: str):
        print(msg("len_layers", 0, "l"))
        try:
            layers = cmds.listRelatives(stack)
        except ValueError:
            return 0
        return len(layers)

    def name_layer(self, num: int, prefix: str = None):
        if prefix is None:
            prefix = self.layer_name
        num = str(num).zfill(2)
        return prefix + num

    def validate_selection(self,
                           sl: str = cmds.ls(sl=True)[0]
                           ) -> str:
        if sl.find(self.modifier_label) != -1:
            res = sl.split(self.modifier_label)[0]
        elif sl.find(self.layer_label) != -1:
            cmds.error("Selection must be a mesh object or a mesh modifier object.")
            raise
        elif sl.find(self.stack_label) != -1:
            cmds.error("Selection must be a mesh object or a mesh modifier object.")
            raise
        else:
            res = sl
        return res

    def find_selection_ref(self,
                           sl: str = cmds.ls(sl=True)[0]
                           ) -> str:
        if sl.find(self.layer_label) != -1:
            if sl == self.layer_name + '00':
                res = self.init_obj
            else:
                res = self.name_layer(num=int(sl.split(self.layer_name)[-1]),
                                      prefix=self.modifier_name)
        elif sl.find(self.stack_label) != -1:
            cmds.error("Selection must be a mesh object, mesh modifier object or mesh layer object.")
            raise
        else:
            res = sl
        print(f"DEBUG ---------- res: {res} | sl: {sl}")
        return res + "_ref"

    def validate_stack(self):
        print(msg("validate_stack", 0, "l"))
        stack_list = cmds.ls(self.stack_name)
        print(self.stack_name)
        print(stack_list)
        try:
            if self.stack_name in stack_list:
                print(msg("validate_stack", 0, "r"))
                return 0
            elif len(stack_list) <= 0:
                print(msg("validate_stack", 1, "r"))
                return 1
            else:
                print(msg("validate_stack", -1, "r"))
                return -1
        except IndexError:
            print(msg("validate_stack", 1, "r"))
            return 1

    def add_stack(self):
        print(msg("add_stack", 1, "l"))
        validation = self.validate_stack()
        if validation == 0:
            print(msg("add_layer", 1, "i"))
            return

        print(msg("add_stack", 0, "l"))
        cmds.group(n=self.stack_name, empty=True)
        print(msg("add_stack", 2, "i"))
        self.add_layer(0, self.init_obj, self.sl)
        print(msg("add_stack", 0, "r"))

    def add_layer(self,
                  __num: int = None,
                  __custom_object: str = None,
                  __selection=None
                  ) -> str:
        """
        Adds a new layer to the active stack.
        :param __num: INTERNAL USE ONLY. By default, will generate a new number at the end.
        :param __custom_object: INTERNAL USE ONLY. By default, creates a new modifier object.
        :param __selection: INTERNAL USE ONLY. By default, uses initial selection.
        :return: New layer's name
        """
        print(msg("add_layer", 1, "l"))
        validation = self.validate_stack()

        if validation == 1:
            print(msg("add_layer", 1, "r"))
            self.add_stack()

        print(msg("add_layer", 0, "l"))
        if __num is None:
            __num = self.len_layers(self.stack_name)
        else:
            print(msg("add_layer", 3, "i", _data=f"number: {__num}"))
        _layer_name = self.name_layer(__num)
        _mod_name = self.name_layer(__num, self.modifier_name)

        if __selection is None:
            __selection = cmds.ls(sl=True)[0]

        print(f"Selection: {__selection}")

        if __custom_object is None:
            print(msg("add_layer", 2, "l"))
            RunMel("createRef")
            _object_name = cmds.rename(self.find_selection_ref(__selection), _mod_name)
        else:
            print(msg("add_layer", 3, "i", _data=f"object: {__custom_object}"))
            _object_name = __custom_object

        cmds.group(_object_name, n=_layer_name)
        cmds.parent(_layer_name, self.stack_name)
        print(msg("add_layer", 0, "r"))
        return _layer_name

    def set_visibility(self, state: bool, target: str):
        """
        Sets visibility for a layer.
        :param state: If True, target is visible.
        :param target: Layer group
        :return:
        """
        if state:
            cmds.showHidden(target)
        else:
            cmds.hide(target)

    def set_interact(self, state: bool, target: str):
        """
        Sets interaction type for a layer.
        :param state: If True, target can be selected. Otherwise, can't be selected and shows as wireframe.
        :param target: Layer group
        :return:
        """
        if state:
            cmds.setAttr(target + ".overrideEnabled", 0)
            cmds.setAttr(target + ".overrideDisplayType", 0)
        else:
            cmds.setAttr(target + ".overrideEnabled", 1)
            cmds.setAttr(target + ".overrideDisplayType", 1)

    def toggle_visibility(self):
        layers = cmds.listRelatives(self.stack_active)
        layers.remove(self.layer_active)

        print(self.state_visible)
        if self.state_visible:
            for i in layers:
                self.set_visibility(False, i)
                self.state_visible = False
        else:
            for i in layers:
                self.set_visibility(True, i)
                self.state_visible = True

    def toggle_interact(self):
        layers = cmds.listRelatives(self.stack_active)
        layers.remove(self.layer_active)

        if self.state_interact:
            for i in layers:
                self.set_interact(False, i)
                self.state_interact = False
        else:
            for i in layers:
                self.set_interact(True, i)
                self.state_interact = True

    def reset_modes(self, _layer: str = None):
        layers = cmds.listRelatives(self.stack_active)

        for i in layers:
            self.set_visibility(True, i)
            self.set_interact(True, i)
            self.state_visible = True
            self.state_interact = True

    def update_modes(self, _layer: str = None):
        if _layer is None:
            layers = cmds.listRelatives(self.stack_active)
            layers.remove(self.layer_active)

            for i in layers:
                self.set_visibility(self.state_visible, i)
                self.set_interact(self.state_interact, i)

            self.set_visibility(True, self.layer_active)
            self.set_interact(True, self.layer_active)
        else:
            if _layer != self.layer_active:
                self.set_visibility(self.state_visible, _layer)
                self.set_interact(self.state_interact, _layer)
            else:
                self.set_visibility(True, self.layer_active)
                self.set_interact(True, self.layer_active)

    def toggle_modes(self, _layer: str = None):
        if _layer is None:
            layers = cmds.listRelatives(self.stack_active)
            layers.remove(self.layer_active)

            for i in layers:
                self.set_visibility(self.state_visible, i)
                self.set_interact(self.state_interact, i)

            self.set_visibility(not self.state_visible, self.layer_active)
            self.set_interact(not self.state_interact, self.layer_active)
        else:
            if _layer == self.layer_active:
                self.set_visibility(not self.state_visible, self.layer_active)
                self.set_interact(not self.state_interact, self.layer_active)
            else:
                self.set_visibility(self.state_visible, _layer)
                self.set_interact(self.state_interact, _layer)


class UI_MayaModifierStack:
    def __init__(self, layer_mgr=LayerMgr(cmds.ls(sl=True))):
        self.LM = layer_mgr

        self.window = cmds.window()
        self.main_layout = cmds.paneLayout(configuration='vertical2')
        self.sub_layout_left = cmds.columnLayout(adj=True, p=self.main_layout)

        self.current_active = cmds.textField(ed=False, p=self.sub_layout_left,
                                             tx=self.LM.layer_active)
        self.frame_left = ''
        self.layer_list = []
        self.button_list = []
        self.update_list()

        self.sub_layout_right = cmds.columnLayout(adj=True, p=self.main_layout)
        self.frame_right = cmds.frameLayout(lv=False, p=self.sub_layout_right)
        self.add_layer_button = cmds.button(l="Add Layer", p=self.frame_right,
                                            command=Callback(self.add_layer))
        self.update_button = cmds.button(l="Update", p=self.frame_right,
                                         command=Callback(self.update_list))
        self.move_up = cmds.button(l="Up", p=self.frame_right,
                                   command=Callback(self.go_up))
        self.move_down = cmds.button(l="Down", p=self.frame_right,
                                     command=Callback(self.go_down))
        self.print_button = cmds.button(l="Print", p=self.frame_right,
                                        command=Callback(self.print))
        self.toggle_vis_button = cmds.button(l="Visibility", p=self.frame_right,
                                             command=Callback(self.toggle_vis))
        self.toggle_int_button = cmds.button(l="Interact", p=self.frame_right,
                                             command=Callback(self.toggle_int))
        self.dock = cmds.dockControl(area='left',
                                     fl=True,
                                     content=self.window,
                                     l="Modifier Stacks")
        cmds.showWindow()

    def update_list(self):
        res = cmds.listRelatives(self.LM.stack_active)

        cmds.deleteUI(self.frame_left)
        self.frame_left = cmds.scrollLayout(p=self.sub_layout_left,
                                            cr=True)

        self.layer_list = []
        self.button_list = []
        for i in res:
            self.layer_list += i
            self.button_list += cmds.button(l=i,
                                            p=self.frame_left,
                                            command=Callback(self.activate_layer, i),
                                            backgroundColor=[118, 195, 233],
                                            enableBackground=False)
        print(f"Current list: {res}")
        self.LM.update_modes()
        return res

    def get_layer_button(self, _query: str):
        _index = self.layer_list.index(_query)
        return self.button_list[_index]

    def activate_layer(self, target):
        print(target)
        _old = self.LM.layer_active
        self.LM.layer_active = target
        self.LM.update_modes(_old)
        self.LM.update_modes(self.LM.layer_active)

        button_old = self.get_layer_button(_old)
        button_target = self.get_layer_button(target)

        cmds.button(button_old, edit=True, enableBackground=False)
        cmds.button(button_target, edit=True, enableBackground=True)

        cmds.textField(self.current_active, edit=True, tx=target)

    def toggle_vis(self):
        print("VIS")
        self.LM.toggle_visibility()
        print("SUCCESS")

    def toggle_int(self):
        print("INT")
        self.LM.toggle_interact()
        print("SUCCESS")

    def print(self):
        print("TEMP")

    def add_layer(self):
        new = self.LM.add_layer()
        self.update_list()
        self.activate_layer(new)

    # def remove_layer(self):
    #     if self.LM.layer_active == self.layer_list[0]:
    #         cmds.error('Layer zero is not removable.')
    #
    #     cmds.delete(self.LM.layer_active)
    #
    #     _layers = cmds.listRelatives(self.LM.stack_active)
    #     for i in range(len(_layers)):
    #         cmds.rename(self.LM.name_layer(i))
    #     self.LM.reset_modes()
    #     self.update_list()

    def move_layer(self, _sign: int):
        """
        Changes current active layer
        :param _sign: Amount of layers to skip, can be negative to go down.
        :return:
        """
        try:
            current_index = self.layer_list.index(self.LM.layer_active)
            next_layer = self.layer_list[current_index + _sign]
            print(next_layer)

            if cmds.ls(next_layer) == [] or current_index + _sign < 0:
                cmds.error("No more layers")
                return

            _old = self.LM.layer_active
            self.activate_layer(next_layer)
            self.LM.update_modes(_old)
            self.LM.update_modes(self.LM.layer_active)
        except ValueError:
            cmds.error("No active layers")

    def go_up(self):
        print("UP")
        self.move_layer(1)

    def go_down(self):
        print("DOWN")
        self.move_layer(-1)


if __name__ == "__main__":
    UI = UI_MayaModifierStack()
