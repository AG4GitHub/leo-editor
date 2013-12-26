#@+leo-ver=5-thin
#@+node:tbrown.20070322113635: * @file bookmarks.py
#@+<< docstring >>
#@+node:tbrown.20070322113635.1: ** << docstring >>
''' Open bookmarks in a list, and show bookmarks in a pane.

Adds the ``bookmarks-open-bookmark`` command which opens the bookmark in the
selected node **if** the node has an ancestor which contains ``@bookmarks``
in its heading.  Useful for binding to double-click.

Also ``bookmarks-open-node``, like ``bookmarks-open-bookmark`` but without
the ancestor requirement.

*Note:* bookmarks treats file urls missing the ``file://`` part as urls,
which deviates from Leo's behavior elsewhere.  It also recognizes local UNLs
like ``#ToDo-->Critical`` as urls.

The ``bookmarks-show`` command will add a tab or pane (if free_layout is enabled)
showing the bookmarks **in the current subtree** with unique colors. You can
very quickly jump around between nodes in a file using this. 

Nodes can be added and removed from the display with the following mouse actions:
    
**left-click on bookmark**
    Jump to that node.
**left-click on background**
    Add a bookmark at the position clicked, unless already present,
    in which case the existing link is highlighted.
**control-left-click on bookmark**
    Remove bookmark.
**alt-left-click on bookmark**
    Edit clicked bookmark in bookmark list, to change link text.
**control-alt-left-click on bookmark**
    Update clicked bookmark to point to current node.
**alt-left-click on background**
    Edit bookmark list.
    
The ``quickMove.py`` plugin also provides actions for adding nodes to a bookmark list.

The free_layout Action button context menu will also allow you to add one of
these bookmark panes, and they will be saved and loaded again if the layout is
saved and loaded.

Commands
--------

bookmarks-open-bookmark
  Open the bookmark in the current node, checking that this node has
  a parent with ``@bookmarks`` in the title first.
bookmarks-open-node
  Open the bookmark / url in the current node.
bookmarks-show
  Mark the current node as the bookmark list for the current
  outline, and open a pane[*]_ listing any bookmarks the current node contains.
bookmarks-mark-as-target
  Mark this node as a bookmark container - does nothing unless followed by
  ``bookmarks-use-other-outline``.
bookmarks-use-other-outline
  Use the node identified with ``bookmarks-mark-as-target``, **which may
  be in another outline**, as the source of bookmarks for this outline.
  Open a pane[*]_ listing any bookmarks that node contains.
  
.. [*] If you already have a bookmark pane open, these command will open a
       second one.  Just close or ignore the first one, it will be gone next
       time the outline is opened.

'''
#@-<< docstring >>

#@@language python
#@@tabwidth -4

__version__ = "0.1"
#@+<< version history >>
#@+node:tbrown.20070322113635.2: ** << version history >>
#@+at
# 0.1 -- first release - TNB
#@-<< version history >>
#@+<< imports >>
#@+node:tbrown.20070322113635.3: ** << imports >>
import leo.core.leoGlobals as g

use_qt = False
if g.app.gui.guiName() == 'qt':
    try:
        from PyQt4 import QtGui, QtCore
        import hashlib
        use_qt = True
    except ImportError:
        use_qt = False


#@-<< imports >>

#@+others
#@+node:ekr.20100128073941.5371: ** init
def init():
    
    if g.unitTesting:
        return False

    ok = bool(use_qt)
    
    if ok:
        g.registerHandler('after-create-leo-frame', onCreate)
        
        # temporary until double-click is bindable in user settings
        if g.app.config.getBool('bookmarks-grab-dblclick'):
            g.registerHandler('icondclick1', lambda t,k: cmd_open_bookmark(k['c']))
        
    else:
        g.es_print("Requires Qt GUI")

    g.plugin_signon(__name__)

    return ok
#@+node:tbrown.20110712121053.19751: ** onCreate
def onCreate(tag, keys):
    
    c = keys.get('c')
    
    BookMarkDisplayProvider(c)
#@+node:tbrown.20120319161800.21489: ** bookmarks-open-*
def cmd_open_bookmark(c):

    if not c: return
    p = c.p
    bookmark = False
    for nd in p.parents():
        if '@bookmarks' in nd.h:
            bookmark = True
            break
    if bookmark:
        if hasattr(c, '_bookmarks'):
            c._bookmarks.current = p.v
        cmd_open_node(c)
           
def cmd_open_node(c):
    
    if not c: return
    p = c.p
    url = g.getUrlFromNode(p)
    if url:
        # No need to handle url hooks here.
        g.handleUrl(url,c=c,p=p)
#@+node:tbrown.20110712100955.39215: ** bookmarks-show
def cmd_show(c):
    
    if not use_qt: return 
    
    bmd = BookMarkDisplay(c)
    
    # Careful: we could be unit testing.
    splitter = bmd.c.free_layout.get_top_splitter()
    if splitter:
        splitter.add_adjacent(bmd.w, 'bodyFrame', 'above')
#@+node:tbrown.20131226095537.26309: ** bookmarks-switch
def cmd_switch(c):
    """switch between bookmarks and previous position in outline"""
    if not hasattr(c, '_bookmarks'):
        g.es("Bookmarks not active for this outline")
        return
    if c.p.v == c._bookmarks.current:
        ov = c._bookmarks.previous
    else:
        ov = c._bookmarks.current
        c._bookmarks.previous = c.p.v
        
    if not ov:
        g.es("No alternate position known")
        return
        
    oc = ov.context
    op = oc.vnode2position(ov)
    if not oc.positionExists(op):
        g.es("No alternate position known")
        return
    oc.selectPosition(op)
    oc.redraw()
    oc.bringToFront()
#@+node:tbrown.20131214112218.36871: ** bookmarks-mark
def cmd_mark_as_target(c):
    """Mark current node as Bookmarks list for use by another file,
    bookmarks-use-other-outline should be used after this command
    """
    g._bookmarks_target = c.p.get_UNL()
    g._bookmarks_target_v = c.p.v
    g.es("Node noted - now use\nbookmarks-use-other-outline\nin the "
        "outline you want to\nstore bookmarks in this node")

def cmd_use_other_outline(c):
    """Set bookmarks for this outline from a list (node) in
    a different outline
    """
    if not hasattr(g, '_bookmarks_target') or not g._bookmarks_target:
        g.es("Use bookmarks-mark-as-target first")
        return
    c.db['_leo_bookmarks_show'] = g._bookmarks_target
    
    bmd = BookMarkDisplay(c, g._bookmarks_target_v)
    
    splitter = c.free_layout.get_top_splitter()
    if splitter:
        splitter.add_adjacent(bmd.w, 'bodyFrame', 'above')
#@+node:tbrown.20110712100955.18924: ** class BookMarkDisplay
class BookMarkDisplay:
    """Manage a pane showing bookmarks"""
    #@+others
    #@+node:tbrown.20110712100955.18926: *3* __init__
    def __init__(self, c, v=None):
        
        self.c = c
        c._bookmarks = self
        
        # self.v - where the bookmarks for c are kept, may not be in c
        if v is None:
            v = self.v = c.p.v
        else:
            self.v = v
        
        # current (last used) bookmark
        self.current = self.v.children[0] if self.v.children else self.v
        self.previous = None  # position in outline, for outline / bookmarks switch
        
        self.already = -1  # used to indicate existing link when same link added again
           
        self.w = QtGui.QWidget()
        
        self.dark = c.config.getBool("color_theme_is_dark")
        
        # stuff for pane persistence
        self.w._ns_id = '_leo_bookmarks_show:'
        # v might not be in this outline
        c.db['_leo_bookmarks_show'] = v.context.vnode2position(v).get_UNL()
            
        # else:
            # c.frame.log.createTab(c.p.h[:10])
            # tabWidget = c.frame.log.tabWidget
            # self.w = tabWidget.widget(tabWidget.count()-1)
        
        self.w.setObjectName('show_bookmarks')
        self.w.setMinimumSize(10, 10)
        self.w.setLayout(QtGui.QVBoxLayout())
        self.w.layout().setContentsMargins(0,0,0,0)

        self.current_list = self.get_list()
        
        self.show_list(self.current_list)
        
        g.registerHandler('select1', self.update)
    #@+node:tbrown.20110712100955.18925: *3* color
    def color(self, text, dark=False):
        """make a consistent light background color for text"""
        
        if g.isPython3:
            text = g.toEncodedString(text,'utf-8')
        x = hashlib.md5(text).hexdigest()[-6:]
        add = int('bb',16) if not dark else int('33',16)
        x = tuple([int(x[2*i:2*i+2], 16)//4+add for i in range(3)])
        x = '%02x%02x%02x' % x
        return x
    #@+node:tbrown.20110712100955.39216: *3* get_list
    def get_list(self):
        """Return list of *unique* urls, uniqueness may need dropping."""
        
        # v might not be in this outline
        p = self.v.context.vnode2position(self.v)
        if not p:
            return
        
        # return [(i.h, i.b.split('\n', 1)[0])
                # for i in p.subtree()]
                
        def strip(s):
            if s.startswith('@url'):
                s = s[4:]
            return s.strip()

        result,urls = [],[]
        for p in p.subtree():
            if p.b and p.b[0] == '#':
                # prevent node url ending with name of file which exists being confused
                url = p.b.split('\n', 1)[0]
            else:
                url = g.getUrlFromNode(p)
                
            url = url.replace(' ', '%20')
            
            h = strip(p.h)
            data = (h,url)
            if url and data not in result and url not in urls:
                result.append(data)
                urls.append(url)

        return result
    #@+node:tbrown.20110712100955.39217: *3* show_list
    def show_list(self, links):
        
        p = self.v.context.vnode2position(self.v)
        if not p:
            return
        w = self.w
        for i in range(w.layout().count()-1, -1, -1):
            w.layout().removeItem(w.layout().itemAt(i))
        te = QtGui.QTextBrowser()
        w.layout().addWidget(te)
        te.setReadOnly(True)
        te.setOpenLinks(False)
        
        def capture_modifiers(event, te=te, prev=te.mousePressEvent, owner=self):
            te.modifiers = event.modifiers()
            te.pos = event.pos()
            if not te.anchorAt(event.pos()):  # clicked body, not anchor
                if event.modifiers() == QtCore.Qt.AltModifier:
                    owner.edit_bookmark(te, event.pos())
                    return
                if int(te.modifiers) == 0:
                    owner.add_bookmark(te, event.pos())
                    return
            return prev(event)
        
        te.mousePressEvent = capture_modifiers
        
        def anchorClicked(url, c=self.c, p=p, te=te, owner=self):
            
            if (QtCore.Qt.AltModifier | QtCore.Qt.ControlModifier) == te.modifiers:
                owner.update_bookmark(str(url.toString()))
                return
            if QtCore.Qt.AltModifier == te.modifiers:
                owner.edit_bookmark(te, te.pos)
                return
            if QtCore.Qt.ControlModifier == te.modifiers:
                owner.delete_bookmark(str(url.toString()))
            else:  # go to bookmark
                
                # update current bookmark
                url = str(url.toString()).replace(' ', '%20').strip()
                for nd in self.v.children:
                    if nd.b.strip() == url:
                        self.current = nd
                        break

                url = str(url.toString())
                # g.trace(url,te)
                # if QtCore.Qt.ShiftModifier & te.modifiers():
                    # sep = '\\' if '\\' in url else '/'
                    # url = sep.join(url.split(sep)[:-1])
                self.show_list(self.current_list)  # to clear red highlight of double added url
                g.handleUrl(url,c=c,p=p)
        
        te.connect(te, QtCore.SIGNAL("anchorClicked(const QUrl &)"), anchorClicked)
        html = []
        for idx, name_link in enumerate(links):
            name, link = name_link
            html.append("<a title='%s' href='%s' style='background: #%s; color: #%s; text-decoration: none;'>%s</a>"
                % (link, link, 
                   self.color(name, dark=self.dark) if self.already != idx else "ff0000", 
                   '073642' if not self.dark else '839496',
                        # FIXME, hardcoded, from solarized
                   name.replace(' ', '&nbsp;')))
        self.already = -1  # clear error condition
        html = '\n'.join(html)
        te.setHtml(html)
    #@+node:tbrown.20110712100955.39218: *3* update
    def update(self, tag, keywords):
        """re-show the current list of bookmarks, if it's changed"""
        
        if keywords['c'] is not self.c:
            return

        l = self.get_list()
        if l != self.current_list:
            self.current_list = l
            self.show_list(self.current_list)
        
        return None  # do not stop processing the select1 hook
    #@+node:tbrown.20130222093439.30271: *3* delete_bookmark
    def delete_bookmark(self, url):
        
        url = url.replace(' ', '%20')
        
        l = [i for i in self.get_list() if i[1] != url]

        if l != self.current_list:
            self.current_list = l
            self.show_list(self.current_list)
            
        for nd in self.v.children:
            if nd.b.strip() == url.strip():
                p1 = nd.context.vnode2position(nd)
                nd.context.deletePositionsInList([p1])
                nd.context.redraw()
                nd.context.setChanged(True)
                break
        
        return None  # do not stop processing the select1 hook
    #@+node:tbrown.20130601104424.55363: *3* update_bookmark
    def update_bookmark(self, old_url):
        
        new_url = self.c.p.get_UNL(with_file=True, with_proto=True)
        
        # COPIED from add_bookmark
        # check it's not already present
        try:
            self.already = [i[1] for i in self.current_list].index(new_url)
        except ValueError:
            self.already = -1
        if self.already != -1:
            g.es("Bookmark for this node already present")
            return self.show_list(self.current_list)
        
        index = [i[1] for i in self.current_list].index(old_url.replace(' ', '%20'))
        
        if index < 0:  # can't happen
            return
        
        self.v.children[index].b = new_url
        self.v.context.setChanged(True)
        
        g.es("Bookmark '%s' updated to current node" % self.v.children[index].h)
        
        return None  # do not stop processing the select1 hook
    #@+node:tbrown.20130222093439.30275: *3* edit_bookmark
    def edit_bookmark(self, te, pos):
        
        url = str(te.anchorAt(pos))
        
        if url:
            url = url.replace(' ', '%20')
            idx = [i[1] for i in self.current_list].index(url)
            nd = self.v.context.vnode2position(self.v.children[idx])
            
        else:
            
            nd = self.v.context.vnode2position(self.v)
            nd.expand()
            
        nd.v.context.selectPosition(nd)
        nd.v.context.bringToFront()
        
        return None  # do not stop processing the select1 hook
    #@+node:tbrown.20130222093439.30273: *3* add_bookmark
    def add_bookmark(self, te, pos):
        
        url = g.getUrlFromNode(self.c.p)
        if url:
            url = url.replace(' ', '%20')
        if not url or '//' not in url:
            # first line starting with '#' is misinterpreted as url
            url = None
            
        if not url:
            url = self.c.p.get_UNL(with_proto=True)
            
        # check it's not already present
        try:
            self.already = [i[1] for i in self.current_list].index(url)
        except ValueError:
            self.already = -1
            
        if self.already != -1:
            g.es("Bookmark for this node already present")
            return self.show_list(self.current_list)
        
        prev = str(te.anchorAt(QtCore.QPoint(pos.x()-12, pos.y())))
        next = str(te.anchorAt(QtCore.QPoint(pos.x()+12, pos.y())))
        
        new_list = []
        placed = False
        
        h = self.c.p.anyAtFileNodeName() or self.c.p.h
        while h and h[0] == '@':
            h = h[1:]
        
        new_anchor = h, url

        for anchor in self.current_list:
            
            if not placed and anchor[1] == next:
                placed = True
                new_list.append(new_anchor)
            
            new_list.append(anchor)
            
            if not placed and anchor[1] == prev:
                placed = True
                new_list.append(new_anchor)
                
        if not placed:
            new_list.append(new_anchor)
            
        idx = new_list.index(new_anchor)
        nd = self.v.context.vnode2position(self.v).insertAsNthChild(idx)
        nd.h = new_anchor[0]
        nd.b = new_anchor[1]
        nd.v.context.redraw()
            
        self.current_list = new_list
        
        self.show_list(self.current_list)
        
        return None  # do not stop processing the select1 hook
    #@-others
#@+node:tbrown.20110712121053.19746: ** class BookMarkDisplayProvider
class BookMarkDisplayProvider:
    #@+others
    #@+node:tbrown.20110712121053.19747: *3* __init__
    def __init__(self, c):
        self.c = c
        
        # if hasattr(c, 'free_layout') and hasattr(c.free_layout, 'get_top_splitter'):
            # Second hasattr temporary until free_layout merges with trunk
            
        splitter = c.free_layout.get_top_splitter()
        # Careful: we could be unit testing.
        if splitter:
            splitter.register_provider(self)
    #@+node:tbrown.20110712121053.19748: *3* ns_provides
    def ns_provides(self):
        return[('Bookmarks', '_leo_bookmarks_show')]
    #@+node:tbrown.20110712121053.19749: *3* ns_provide
    def ns_provide(self, id_):
        if id_.startswith('_leo_bookmarks_show'):
            
            c = self.c
            v = None
            
            if ':' in id_:
                gnx = id_.split(':')[1]
                if not gnx and '_leo_bookmarks_show' in c.db:
                    gnx = c.db['_leo_bookmarks_show']
                # first try old style local gnx lookup
                for i in c.all_nodes():
                    if str(i.gnx) == gnx:
                        v = i
                        break
                else:  # use UNL lookup
                    file_, UNL = gnx.split('#', 1)
                    other_c = g.openWithFileName(file_, old_c=c)
                    if other_c != c:
                        c.bringToFront()
                        g.es("NOTE: bookmarks for this outline\nare in a different outline:\n  '%s'"%file_)
                    
                    ok, depth, other_p = g.recursiveUNLFind(UNL.split('-->'), other_c)
                    if ok:
                        v = other_p.v
                    else:
                        g.es("Couldn't find '%s'"%gnx)
                    
            if v is None:
                v = c.p.v

            bmd = BookMarkDisplay(self.c, v=v)
            return bmd.w
    #@-others
#@-others
#@-leo
