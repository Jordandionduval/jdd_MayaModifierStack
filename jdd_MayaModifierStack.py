from typing import *

import maya.cmds as cmds
import maya.mel as mel
from pymel.all import Callback

current_selection = cmds.ls(sl=True)

enable_debug = True


class RunMel:
    def __init__(self, command: str):
        print("[RunMel] Running MEL script \"" + command + "\"...")
        self._cmd = dict(
            createRef="bt_duplicateMeshReference",
        )

        self.eval_command(self._cmd[command])

    def eval_command(self, _cmd: str):
        try:
            res = mel.eval(_cmd)
            print(f"[RunMel] -- Operation Success --")
            return res
        except Exception:
            print(f"[RunMel] -- Unknown Error --")
            raise


class LayerMgr:
    def __init__(self, _selection):
        self.__cls_name = self.__class__.__name__
        self.stack_label = "_ModStack"
        self.layer_label = "_ModLayer"
        self.modifier_label = "_ModObject"

        self.sl = _selection

        if len(self.sl) != 1:
            cmds.error("Selection is not one object.")
        else:
            self.sl = self.sl[0]
        print(f"[{self.__cls_name}] -- Initiating task... --")
        if self.sl.find(self.modifier_label) != -1:
            self.init_obj = self.sl.split(self.modifier_label)[0]
        elif self.sl.find(self.layer_label) != -1:
            cmds.error("Selection must be a mesh object or a mesh modifier object.")
        elif self.sl.find(self.stack_label) != -1:
            cmds.error("Selection must be a mesh object or a mesh modifier object.")
        else:
            self.init_obj = self.sl

        self.shader = self.get_shader(self.init_obj)
        self.stack_name = self.init_obj + self.stack_label
        self.layer_name = self.init_obj + self.layer_label
        self.modifier_name = self.init_obj + self.modifier_label

        self.stack_active = self.stack_name
        self.layer_active = self.layer_name + "00"

        self.state_visible = True
        self.state_interact = True

        if enable_debug:
            print(f"---- INIT VARIABLES FOR {self.__cls_name} ----"
                  f"\nSelection: {self.sl}"
                  f"\nInitial Object: {self.init_obj}"
                  f"\nShader: {self.shader}"
                  f"\nStack Name: {self.stack_name}"
                  f"\nLayer Name: {self.layer_name}"
                  f"\nModifier Name: {self.modifier_name}"
                  f"\n---- CODE EXECUTION FOR {self.__cls_name} ----")

    def get_shader(self, target: str):
        # get shapes of target:
        shapes = cmds.ls(target, dag=1, o=1, s=1)
        # get shading groups from shapes:
        shading_grps = cmds.listConnections(shapes, type='shadingEngine')
        # get the shaders:
        shaders = cmds.ls(cmds.listConnections(shading_grps), materials=1)

        return shaders[0]

    def len_layers(self, stack: str):
        if enable_debug:
            print(f"[{self.__cls_name}.len_layers] Counting layers...")
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
        return res + "_ref"

    def validate_stack(self):
        __funcname = f"{self.__cls_name}.validate_stack"
        print(f"[{__funcname}] -- Initiating task... --")
        stack_list = cmds.ls(self.stack_name)
        print(self.stack_name)
        print(stack_list)
        try:
            if self.stack_name in stack_list:
                print(f"[{__funcname}] -- Operation Success --")
                return 0
            elif len(stack_list) <= 0:
                print(f"[{__funcname}] -- Stack missing --")
                return 1
            else:
                print(f"[{__funcname}] -- Unknown Error --")
                return -1
        except IndexError:
            print(f"[{__funcname}] -- Stack missing --")
            return 1

    def add_stack(self):
        __funcname = f"{self.__cls_name}.add_stack"
        print(f"[{__funcname}] -- Validating Stack... --")
        validation = self.validate_stack()
        if validation == 0:
            print(f"[{__funcname}] -- Stack already exists --")
            return

        print(f"[{__funcname}] -- Initiating task... --")
        cmds.group(n=self.stack_name, empty=True)
        self.add_layer(0, self.init_obj, self.sl)
        print(f"[{__funcname}] -- Operation Success --")
        return self.stack_name

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
        __funcname = f'{self.__cls_name}.add_layer'
        print(f"[{__funcname}] -- Validating Stack... --")
        validation = self.validate_stack()

        if validation == 1:
            print(f"[{__funcname}] -- Validation failed, creating stack... --")
            self.add_stack()

        print(f"[{__funcname}] -- Initiating task... --")
        if __num is None:
            __num = self.len_layers(self.stack_name)
        else:
            print(f"[{__funcname}] -- Using provided layer number: {__num} --")
        _layer_name = self.name_layer(__num)
        _mod_name = self.name_layer(__num, self.modifier_name)

        if __selection is None:
            __selection = cmds.ls(sl=True)[0]

        print(f"Selection: {__selection}")

        if __custom_object is None:
            print(f"[{__funcname}] -- Creating new modifier object... --")
            RunMel("createRef")
            _ref_object = self.find_selection_ref(__selection)
            _object_name = cmds.rename(_ref_object, _mod_name)
        else:
            print(f"[{__funcname}] -- Using provided layer object: {__custom_object} --")
            _ref_object = __custom_object
            _object_name = __custom_object

        # Rename Shape to avoid files sharing shape names, which creates
        # an error in the "DuplicateMeshReference" bonus tool module
        try:
            _ref_shape = cmds.listRelatives(_mod_name, s=True, f=True)
            _ref_shape = cmds.rename(_ref_shape, f"{_mod_name}_refShape")
        except ValueError:
            _ref_shape = cmds.listRelatives(__selection, s=True, f=True)
            _ref_shape = cmds.rename(_ref_shape, f"{_mod_name}_refShape")

        print(20 * '-' + str(_ref_shape))
        cmds.group(_object_name, n=_layer_name)
        cmds.parent(_layer_name, self.stack_name)

        # Apply material to created object to avoid green faces (no shaders)
        cmds.select(_layer_name)
        cmds.hyperShade(a=self.shader)

        print(f"[{__funcname}] -- Operation Success | New layer: {_layer_name} --")
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
        self.container_width = 200
        self.LM = layer_mgr
        self.stacks = []

        self.window = cmds.window()
        self.container = cmds.columnLayout(adj=True)

        self.stacks_frame = cmds.frameLayout(l='Stacks', collapsable=True, cl=True,
                                             p=self.container)
        self.stacks_divider = cmds.paneLayout(configuration='vertical2', p=self.stacks_frame)
        self.stacks_section_left = cmds.columnLayout(adj=True, p=self.stacks_divider)
        self.stacks_section_right = cmds.columnLayout(adj=True, p=self.stacks_divider)

        self.identify_active_stack = cmds.textField(ed=False, p=self.stacks_section_left,
                                                    tx=self.LM.stack_active,
                                                    backgroundColor=[.15, .15, .15])
        self.stacks_left_scroller = ''  # Set to '' as None type creates AttributeErrors
        self.stacks_list = []
        self.stacks_button_list = []

        self.stacks_right_buttonpanel = cmds.frameLayout(lv=False, p=self.stacks_section_right)
        self.init_stack_button = cmds.button(l="Initiate Stack", p=self.stacks_right_buttonpanel,
                                            command=Callback(self.init_stack))
        self.layers_update_button = cmds.button(l="Update", p=self.stacks_right_buttonpanel,
                                                command=Callback(self.update_stacks))
        self.layers_move_up = cmds.button(l="Up", p=self.stacks_right_buttonpanel,
                                          command=Callback(self.up_stacks))
        self.layers_move_down = cmds.button(l="Down", p=self.stacks_right_buttonpanel,
                                            command=Callback(self.down_stacks))

        self.layers_frame = cmds.frameLayout(l='Layers', collapsable=True, p=self.container)
        self.layers_divider = cmds.paneLayout(configuration='vertical2', p=self.layers_frame)
        self.layers_section_left = cmds.columnLayout(adj=True, p=self.layers_divider)
        self.layers_section_right = cmds.columnLayout(adj=True, p=self.layers_divider)

        self.identify_active_layer = cmds.textField(ed=False, p=self.layers_section_left,
                                                    tx=self.LM.layer_active,
                                                    backgroundColor=[.15, .15, .15])
        self.layers_left_scroller = ''  # Set to '' as None type creates AttributeErrors
        self.layers_list = []
        self.layers_button_list = []

        self.update_stacks()
        self.update_layers()

        self.layers_right_buttonpanel = cmds.frameLayout(lv=False, p=self.layers_section_right)
        self.add_layer_button = cmds.button(l="Add Layer", p=self.layers_right_buttonpanel,
                                            command=Callback(self.add_layer))
        self.layers_update_button = cmds.button(l="Update", p=self.layers_right_buttonpanel,
                                                command=Callback(self.update_layers))
        self.layers_move_up = cmds.button(l="Up", p=self.layers_right_buttonpanel,
                                          command=Callback(self.up_layers))
        self.layers_move_down = cmds.button(l="Down", p=self.layers_right_buttonpanel,
                                            command=Callback(self.down_layers))
        self.layers_print_button = cmds.button(l="Print", p=self.layers_right_buttonpanel,
                                               command=Callback(self.print))
        self.layers_toggle_vis_button = cmds.button(l="Visibility", p=self.layers_right_buttonpanel,
                                                    command=Callback(self.toggle_vis))
        self.layers_toggle_int_button = cmds.button(l="Interact", p=self.layers_right_buttonpanel,
                                                    command=Callback(self.toggle_int))
        self.dock = cmds.dockControl(area='left',
                                     fl=True,
                                     content=self.window,
                                     l="Modifier Stacks")
        cmds.showWindow()

    def update_stacks(self):
        res = cmds.ls(f"*{self.LM.stack_label}")
        if self.stacks_left_scroller is not '':
            cmds.deleteUI(self.stacks_left_scroller)
        self.stacks_left_scroller = cmds.scrollLayout(p=self.stacks_section_left,
                                                      cr=True)

        self.stacks_list = []
        self.stacks_button_list = []
        for i in res:
            self.stacks_list += [i]
            self.stacks_button_list += [cmds.button(l=i,
                                                    p=self.stacks_left_scroller,
                                                    command=Callback(self.activate_stack, i)
                                                    )]
        if enable_debug:
            print("----------------DEBUG----------------"
                  f"\nCurrent list: {res}"
                  f"\nCurrent layers: {self.stacks_list}"
                  f"\nCurrent buttons: {self.stacks_button_list}"
                  "\n------------------------------------")
        self.activate_stack(self.LM.stack_active)
        self.update_layers()
        return res

    def activate_stack(self, target):
        _old = self.LM.stack_active
        self.LM.stack_active = target

        index_old = self.stacks_list.index(_old)
        button_old = self.stacks_button_list[index_old]
        index_target = self.stacks_list.index(target)
        button_target = self.stacks_button_list[index_target]

        cmds.button(button_old, edit=True, backgroundColor=[.361, .361, .361])
        cmds.button(button_target, edit=True, backgroundColor=[.96, .96, .11])

        cmds.textField(self.identify_active_stack, edit=True, tx=target)
        self.LM.layer_active = cmds.listRelatives(target)[0]

    def update_layers(self):
        res = cmds.listRelatives(self.LM.stack_active)
        if self.layers_left_scroller is not '':
            cmds.deleteUI(self.layers_left_scroller)
        self.layers_left_scroller = cmds.scrollLayout(p=self.layers_section_left,
                                                      cr=True)

        self.layers_list = []
        self.layers_button_list = []
        for i in res:
            self.layers_list += [i]
            self.layers_button_list += [cmds.button(l=i,
                                                    p=self.layers_left_scroller,
                                                    command=Callback(self.activate_layer, i)
                                                    )]
        if enable_debug:
            print("----------------DEBUG----------------"
                  f"\nCurrent list: {res}"
                  f"\nCurrent layers: {self.layers_list}"
                  f"\nCurrent buttons: {self.layers_button_list}"
                  "\n------------------------------------")
        self.LM.update_modes()
        self.activate_layer(self.LM.layer_active)
        return res

    def activate_layer(self, target):
        _old = self.LM.layer_active
        self.LM.layer_active = target
        self.LM.update_modes(_old)
        self.LM.update_modes(self.LM.layer_active)

        index_old = self.layers_list.index(_old)
        button_old = self.layers_button_list[index_old]
        index_target = self.layers_list.index(target)
        button_target = self.layers_button_list[index_target]

        cmds.button(button_old, edit=True, backgroundColor=[.361, .361, .361])
        cmds.button(button_target, edit=True, backgroundColor=[.46, .76, .91])

        cmds.textField(self.identify_active_layer, edit=True, tx=target)

        cmds.select(cmds.listRelatives(target), replace=True)

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
        self.update_layers()
        self.activate_layer(new)

    def init_stack(self):
        new = self.LM.add_stack()

    # Removed temporarily, creates errors and tries to delete layer 00 everytime
    # instead of deleting the currently active layer

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
    #     self.update_layers()

    def move_stack(self, _sign: int):
        """
        Changes current active layer
        :param _sign: Amount of layers to skip, can be negative to go down.
        :return:
        """
        try:
            current_index = self.stacks_list.index(self.LM.stack_active)
            next_layer = self.stacks_list[current_index + _sign]
            print(next_layer)

            if cmds.ls(next_layer) == [] or current_index + _sign < 0:
                cmds.error("No more layers")
                return

            self.activate_stack(self.LM.stack_active)
        except ValueError:
            cmds.error("No active layers")

    def up_stacks(self):
        print("UP")
        self.move_stack(-1)

    def down_stacks(self):
        print("DOWN")
        self.move_stack(1)

    def move_layer(self, _sign: int):
        """
        Changes current active layer
        :param _sign: Amount of layers to skip, can be negative to go down.
        :return:
        """
        try:
            current_index = self.layers_list.index(self.LM.layer_active)
            next_layer = self.layers_list[current_index + _sign]
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

    def up_layers(self):
        print("UP")
        self.move_layer(-1)

    def down_layers(self):
        print("DOWN")
        self.move_layer(1)


if __name__ == "__main__":
    UI = UI_MayaModifierStack()
