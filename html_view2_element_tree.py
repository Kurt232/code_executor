from kernel.utils import ElementTree, EleAttr, UIElement
html_view = """
<FrameLayout id='0' status='selected'>
  <LinearLayout id='1'>
    <FrameLayout id='2'>
      <ViewGroup id='3' resource_id='decor_content_parent'>
        <FrameLayout id='4' resource_id='action_bar_container'>
          <ViewGroup id='5' resource_id='action_bar'>
            <p id='6'>Calendar</p>
            <aq id='7'>
              <button id='8' resource_id='search' alt='Search'></button>
              <button id='9' resource_id='change_view' alt='Change view'></button>
              <button id='10' alt='More options'></button>
            </aq>
          </ViewGroup>
        </FrameLayout>
        <FrameLayout id='11' resource_id='content'>
          <ViewGroup id='12' resource_id='calendar_coordinator'>
            <FrameLayout id='13' resource_id='fragments_holder'>
              <button id='14'>
                <RelativeLayout id='63' resource_id='month_calendar_holder'>
                  <ImageView id='64' resource_id='top_left_arrow'></ImageView>
                  <button id='65' resource_id='top_value'>July</button>
                  <ImageView id='66' resource_id='top_right_arrow'></ImageView>
                  <FrameLayout id='67' resource_id='month_view_wrapper'></FrameLayout>
                </RelativeLayout>
              </button>
            </FrameLayout>
            <button id='159' resource_id='calendar_fab' alt='New Event'></button>
          </ViewGroup>
        </FrameLayout>
      </ViewGroup>
    </FrameLayout>
  </LinearLayout>
</FrameLayout>
"""

import bs4
soup = bs4.BeautifulSoup(html_view, 'html.parser')

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
      is_checkable=is_checkable)
  
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

print(mapping.keys())
element_tree = ElementTree(mapping, valid_ele_ids)
print(element_tree.str)