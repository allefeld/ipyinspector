from inspect import getattr_static, getdoc          # PSF
from html import escape as htmlEscape               # PSF
from ipytree import Node, Tree                      # MIT
from IPython import get_ipython                     # BSD 3-Clause
from IPython.core.magic import register_line_magic
from IPython.display import display

# show object members which begin with an underscore?
includeUnderscore = False

# object types for which repr should be omitted
typeNoRepr = []

# style attributes for item elements (CSS)
itemStyle = 'font-family: Consolas, monospace'
nameStyle = 'color: purple'
typeStyle = 'color: black'
reprStyle = 'color: darkblue'

# maximum height of Inspector (CSS length)
maxHeight = '30em'

# icons for closed and open subtree (Font Awesome names)
openIcon = 'caret-right'
closeIcon = 'caret-down'

# maximum number of lines in docstring tooltip
maxDocLines = 30


def typeName(objType):
    objTypeName = objType.__name__
    objTypeModule = objType.__module__
    if objTypeModule is None or objTypeModule == str.__class__.__module__:
        objTypeQualifiedname = objTypeName
    else:
        objTypeQualifiedname = objTypeModule + '.' + objTypeName
    return objTypeName, objTypeQualifiedname


class Object(Node):

    def __init__(self, obj, objName=None):
        objType = type(obj)
        objTypeName, objTypeQualifiedname = typeName(objType)
        objRepr = repr(obj)

        objDoc = getdoc(objType)
        if objDoc is not None:
            objDoc = objDoc.split('\n')
            if len(objDoc) > maxDocLines:
                objDoc = objDoc[:maxDocLines - 1]
                objDoc.append('…')
            objDoc = '\n'.join(objDoc)

        label = []
        label.append(f'<span style="{itemStyle}">')
        if objName is not None:
            label.append(
                f'<span style="{nameStyle}">{htmlEscape(objName)}</span>: ')
        label.append(f'''<span style="{typeStyle}"
            title="{htmlEscape(objTypeQualifiedname)}">
            {htmlEscape(objTypeName)}</span> ''')
        if objTypeName not in typeNoRepr:
            label.append(f'<span style="{reprStyle}"')
            if objDoc is not None:
                label.append(f'title="{htmlEscape(objDoc)}"')
            label.append(f'>{htmlEscape(objRepr)}</span>')
        label.append('</span>')

        super().__init__(' '.join(label), show_icon=False)
        self.obj = obj
        self.open_icon = openIcon
        self.close_icon = closeIcon

    def populate(self):
        members = dir(self.obj)
        for memberName in members:
            if not memberName.startswith('_') or includeUnderscore:
                try:
                    memberObj = getattr_static(self.obj, memberName)
                    self.add_node(Object(memberObj, memberName))
                except AttributeError:
                    valueObj = getattr(self.obj, memberName)
                    self.add_node(Object(valueObj, '→ ' + memberName))
        self.obj = None

    def handleSelection(self):
        self.selected = False       # hack: detect every click as new selection
        if self.obj is not None:
            self.populate()
        else:
            self.opened = not self.opened


class ObjectInspector(Tree):

    def __init__(self, *objects, **namedObjects):
        super().__init__(multiple_selection=False)
        self.add_class('inspector-object')
        for obj in objects:
            self.add_node(Object(obj))
        for objName, obj in namedObjects.items():
            self.add_node(Object(obj, objName))
        self.observe(self.handleSelection, names='selected_nodes')
        self.layout.max_height = maxHeight
        self.layout.overflow_y = 'auto'

    def handleSelection(self, change):
        if change.new is not None and len(change.new) > 0:
            change.new[0].handleSelection()


class Data(Object):

    def populate(self):
        obj = self.obj
        if hasattr(obj, '__getitem__'):
            if hasattr(obj, 'keys'):
                # map
                for key in obj.keys():
                    self.add_node(Data(obj[key], repr(key)))
            elif hasattr(obj, '__len__'):
                # sequence
                for i in range(len(obj)):
                    self.add_node(Data(obj[i], repr(i)))
        elif hasattr(obj, '__iter__'):
            # set
            for item in obj:
                self.add_node(Data(item))
        self.obj = None


class DataInspector(Tree):

    def __init__(self, *objects, **namedObjects):
        super().__init__(multiple_selection=False)
        self.add_class('inspector-data')
        for obj in objects:
            self.add_node(Data(obj))
        for objName, obj in namedObjects.items():
            self.add_node(Data(obj, objName))
        self.observe(self.handleSelection, names='selected_nodes')
        self.layout.max_height = maxHeight
        self.layout.overflow_y = 'auto'

    def handleSelection(self, change):
        if change.new is not None and len(change.new) > 0:
            change.new[0].handleSelection()


@register_line_magic
def oi(line):
    if line != '':
        obj = get_ipython().ev(line)
        insp = ObjectInspector(obj)
    else:
        namedObjects = get_ipython().ev('locals()')
        insp = ObjectInspector(**namedObjects)
    display(insp)


@register_line_magic
def di(line):
    if line != '':
        obj = get_ipython().ev(line)
        insp = DataInspector(obj)
    else:
        namedObjects = get_ipython().ev('locals()')
        insp = DataInspector(**namedObjects)
    display(insp)
