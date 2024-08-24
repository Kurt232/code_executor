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
  def execute_action(self, target_ele: EleAttr, **action_kwargs) -> None:
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
      # todo:: parse the html str
      # dfs to traverse each node to initialize the ELeAttr
      soup = bs4.BeautifulSoup(view, 'html.parser')
      mapping = {}, valid_ele_ids = []
      stack = [soup]
      while stack:
        node = stack.pop()
        idx = node.attrs.get('id')
        # todo::
        ele = UIElement() # TODO::
        attr_ele = EleAttr(idx)
        # todo:: some attributes need to add manually
        attr_ele.set_type(node.attrs)
        # the detail you can see: kernel.utils @forest_to_element_tree
        
        mapping[idx] = attr_ele
        valid_ele_ids.append(idx)
        for child in node.children:
          stack.append(child)
      
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

  def execute_action(self, target_ele: EleAttr, **action_kwargs) -> None:
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