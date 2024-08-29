import abc
import dataclasses
import numpy as np

from typing import Any, Optional, Self

from kernel.utils import ElementTree, EleAttr, UIElement

@dataclasses.dataclass(frozen=True)
class State():
  """State of the Android environment.

  Attributes:
    pixels: RGB array of current screen.
    forest: Raw UI forest; see android_world_controller.py for more info.
    ui_elements: Processed children and stateful UI elements extracted from
      forest.
  """

  pixels: np.ndarray
  element_tree: ElementTree

  @classmethod
  def create_and_infer_elements(
      cls,
      pixels: np.ndarray,
      element_tree: ElementTree,
  ) -> Self:
    """Creates a new instance, inferring UI elements from the forest."""

    return cls(pixels, element_tree)

class AsyncEnv(abc.ABC):
  """Interface for interacting with a real-time Android device.

  Computing environments, such as Android, run in real-time, independently of
  the agent interacting with it. All observations and actions are asynchronous
  and OS does not pause when providing observations or when accepting actions.
  Changes from action execution may take some time to appear.
  """

  @abc.abstractmethod
  def reset(self, go_home: bool = False) -> State:
    """Go home on reset.

    Args:
      go_home: Whether to go home during the reset.
    """

  @abc.abstractmethod
  def get_state(self, wait_to_stabilize: bool = False) -> State:
    """Gets the state of the environment; i.e., screenshot & UI tree.

    In practice this will usually be called after executing an action. Logic
    should be implemented, perhaps a simple time.sleep, to ensure the
    environment updates after the action.

    Args:
      wait_to_stabilize: Whether to wait for the screen to stabilize before
        returning state.

    Returns:
      Observation containing RGB array of screen, the accessibility forest,
        and UI elements derived from the forest. See android_world_controller.py
        for
        more detail.
    """

  @abc.abstractmethod
  def execute_action(self, action: dict) -> None:
    """Executes action on the environment."""

  @property
  @abc.abstractmethod
  def device_screen_size(self) -> tuple[int, int]:
    """Returns the screen size of the environment in pixels: (width, height)."""

  @property
  @abc.abstractmethod
  def logical_screen_size(self) -> tuple[int, int]:
    """Retrieves the logical screen size of the Android device.

    While the physical size is a fixed attribute of the display, the logical
    size is flexible and varies based on system settings such as the orientation
    or if the resolution is changed.

    Returns: The (width, height) in pixels, denoting the logical dimensions of
    the screen. Width and height values are aligned with the device's current
    orientation, meaning width is always logical horizontal direction (like in
    the landscape orientation width will be the physical vertical direction).
    """

  @abc.abstractmethod
  def close(self) -> None:
    """Closes the environment."""
    
    
class AsyncMockEnv(AsyncEnv):
  
  def __init__(self, ui_view_sequence: list[str], ui_action_sequence: list[tuple], screen_size: tuple[int, int]=None):
    '''
    ui_view_sequence: list of UI state html str
    ui_action_sequence: list of UI action tuple (element, action, action args) # todo:: maybe need to convert format
    '''
    self.ui_state_sequence = self.init_state_sequence(ui_view_sequence)
    self.ui_action_sequence = ui_action_sequence
    self.screen_size = screen_size
    self.current_state_index = 0
    
  @staticmethod
  def init_state_sequence(ui_view_sequence: list[str]):  
    state_list = []
    import bs4
    for view in ui_view_sequence:
      soup = bs4.BeautifulSoup(view, 'html.parser')
      mapping = {}
      valid_ele_ids = []

      for tag in soup.find_all(True):
        print(tag.name, tag.attrs)
        attrs = tag.attrs
        
        idx = int(attrs.get('id'))
        assert idx is not None
        
        # Collect children IDs
        children_ids = []
        for child in tag.find_all(True, recursive=False):
          child_id = int(child.attrs.get('id'))
          if child_id:
            children_ids.append(child_id)
        
        if len(children_ids) == 0:
          valid_ele_ids.append(idx)
        
        resource_id = attrs.get('resource_id')
        alt = attrs.get('alt')
        status = attrs.get('status')
        is_selected = None
        is_checked = None
        if status:
          is_selected = is_checked = status == 'selected'
        content = tag.string if tag.string else None
        
        is_clickable = False
        is_long_clickable = False
        is_scrollable = False
        is_editable = False
        is_checkable = False
        if tag.name == 'input':
          is_editable = True
        elif tag.name == 'checkbox':
          is_checkable = True
        elif tag.name == 'button':
          is_clickable = True
          is_long_clickable = True
        elif tag.name == 'scrollbar':
          is_scrollable = True
        if tag.name == 'p': # usually can click
          is_clickable = True
          is_long_clickable = True
        element: UIElement = UIElement(
            resource_name=resource_id, 
            class_name=tag.name, 
            text=content, 
            content_description=alt,
            is_visible=True,
            is_enabled=True,
            is_clickable=is_clickable, 
            is_long_clickable=is_long_clickable, 
            is_scrollable=is_scrollable, 
            is_editable=is_editable, 
            is_checkable=is_checkable,
            is_checked=is_checked,
            is_selected=is_selected)
        
        ele_attr = EleAttr(idx, children_ids, element)
        ele_attr.type_ = tag.name
        ele_attr.type = tag.name
        
        text = element.text if element.text else ''
        text = text.replace('\n', ' \\ ')
        text = text[:50] if len(text) > 50 else text
        ele_attr.content = text
        ele_attr.alt = element.content_description
        
        ele_attr.status = [status] if status else []
        ele_attr.local_id = len(valid_ele_ids)
        
        mapping[idx] = ele_attr
      
      element_tree = ElementTree(mapping, valid_ele_ids)
      state_list.append(State.create_and_infer_elements(None, element_tree))
    return state_list
  
  def reset(self, go_home: bool = False) -> State:
    """Go home on reset.

    Args:
      go_home: Whether to go home during the reset.
    """
    self.current_state_index = 0
    return self.get_state()

  def get_state(self, wait_to_stabilize: bool = False) -> State:
    """Gets the state of the environment; i.e., screenshot & UI tree.

    In practice this will usually be called after executing an action. Logic
    should be implemented, perhaps a simple time.sleep, to ensure the
    environment updates after the action.

    Args:
      wait_to_stabilize: Whether to wait for the screen to stabilize before
        returning state.

    Returns:
      Observation containing RGB array of screen, the accessibility forest,
        and UI elements derived from the forest. See android_world_controller.py
        for
        more detail.
    """
    return self.ui_state_sequence[self.current_state_index]

  def execute_action(self, action: dict) -> None:
    """Executes action on the environment."""
    # todo:: check the action
    # if action is valid, then update the state index
    self.current_state_index += 1

  @property
  def device_screen_size(self) -> tuple[int, int]:
    """Returns the screen size of the environment in pixels: (width, height)."""
    return self.screen_size

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    """Retrieves the logical screen size of the Android device.

    While the physical size is a fixed attribute of the display, the logical
    size is flexible and varies based on system settings such as the orientation
    or if the resolution is changed.

    Returns: The (width, height) in pixels, denoting the logical dimensions of
    the screen. Width and height values are aligned with the device's current
    orientation, meaning width is always logical horizontal direction (like in
    the landscape orientation width will be the physical vertical direction).
    """
    return self.screen_size

  def close(self) -> None:
    """Closes the environment."""
    pass