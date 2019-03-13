from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QBrush, QColor, QFontMetrics
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsItem, QGraphicsScene

from src.view.Edge import Edge
from view.collapse_expand_button import CollapseExpandButton


class Node(QGraphicsEllipseItem):
    i = 0
    NODE_MIN_WIDTH = 100
    NODE_MAX_WIDTH = 150
    NODE_HEIGHT = 50
    NODE_COLOR = (152, 193, 217)

    def __init__(self, x: float, y: float, scene: QGraphicsScene, title: str = None, parent: QGraphicsItem = None):
        """
        The constructor for a UI node
        :param x: x position for the center of the node
        :param y: y position for the center of the node
        :param title: title of the node displayed in the ui
        :param parent: parent of this graphics item
        """
        if title:
            self.title = title
        else:
            # give node a unique title
            self.title = "node {}".format(Node.i)
        Node.i += 1
        self.scene = scene
        self.children = []
        self.edges = []
        self.children_collapsed = False
        self.just_collapsed_upwards = False
        # store node position when collapsing upwards
        self.collapse_data = None
        # add node name label centered in the eclipse, elide if title is too long
        self.node_text = QGraphicsSimpleTextItem()
        metrics = QFontMetrics(self.node_text.font())
        elided_title = metrics.elidedText(self.title, Qt.ElideRight, self.NODE_MAX_WIDTH)
        self.node_text.setText(elided_title)
        self.node_text.setAcceptedMouseButtons(Qt.NoButton)
        self.node_text.setAcceptHoverEvents(False)
        text_width = self.node_text.boundingRect().width()
        text_height = self.node_text.boundingRect().height()
        self.node_text.setPos(x - (text_width / 2), y - (text_height / 2))
        # set node size based on text size
        if text_width > self.NODE_MIN_WIDTH - 10:
            rect = QRectF(x - (text_width + 10) / 2, y - self.NODE_HEIGHT / 2, text_width + 10, self.NODE_HEIGHT)
        else:
            rect = QRectF(x - self.NODE_MIN_WIDTH / 2, y - self.NODE_HEIGHT / 2, self.NODE_MIN_WIDTH, self.NODE_HEIGHT)
        # call super function now we know the node size
        super(Node, self).__init__(rect, parent)
        self.node_text.setParentItem(self)
        # indicates if node is being dragged
        self.dragging = False
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        # give node a random color
        # TODO: Determine color scheme for node types
        self.setBrush(QBrush(QColor(*self.NODE_COLOR)))
        # create the bottom collapse/expand button for this node
        self.bottom_collapse_expand_button = CollapseExpandButton(self)
        self.bottom_collapse_expand_button.setParentItem(self)
        self.bottom_collapse_expand_button.collapse.connect(self.collapse_children)
        self.bottom_collapse_expand_button.expand.connect(self.expand_children)
        # position the bottom button at the bottom-center of the node
        x = self.xpos() - self.bottom_collapse_expand_button.boundingRect().width() / 2
        y = self.ypos() + (self.NODE_HEIGHT / 2) - self.bottom_collapse_expand_button.boundingRect().height() / 2
        self.bottom_collapse_expand_button.setPos(x, y)
        # hidden by default, the button is only needed if the node has children
        self.bottom_collapse_expand_button.hide()
        # create the top collapse/expand button for this node
        self.top_collapse_expand_button = CollapseExpandButton(self)
        self.top_collapse_expand_button.setParentItem(self)
        self.top_collapse_expand_button.collapse.connect(self.collapse_upwards)
        self.top_collapse_expand_button.expand.connect(self.expand_upwards)
        # position the top button at the top-center of the node
        x = self.xpos() - self.top_collapse_expand_button.boundingRect().width() / 2
        y = self.ypos() - (self.NODE_HEIGHT / 2) - self.top_collapse_expand_button.boundingRect().height() / 2
        self.top_collapse_expand_button.setPos(x, y)

    def add_child(self, child):
        """
        Add a child node
        Inheritance looks like: parent > edge > child
        :param child: Another ui node
        """
        edge = Edge(self, child)
        edge.setParentItem(self)
        # edge should stay behind the expand/collapse button
        edge.stackBefore(self.bottom_collapse_expand_button)
        self.children.append(child)
        self.edges.append(edge)
        # show the expand/collapse button when the first child is added
        if not self.bottom_collapse_expand_button.isVisible():
            self.bottom_collapse_expand_button.show()

    def moveBy(self, x, y):
        super(Node, self).moveBy(x, y)
        if self.parentItem() and isinstance(self.parentItem(), Edge):
            self.parentItem().change_position()

    def setPos(self, *args):
        super(Node, self).setPos(*args)
        if self.parentItem() and isinstance(self.parentItem(), Edge):
            self.parentItem().change_position()

    def xoffset(self):
        """
        recursively adds the relative x distances from this node up until the root node.
        :return: the sum of the relative x distances
        """
        if self.parentItem():
            return self.pos().x() + self.parentItem().xoffset()
        else:
            return self.pos().x()

    def yoffset(self):
        """
        recursively adds the relative y distances from this node up until the root node.
        :return: the sum of the relative y distances
        """
        if self.parentItem():
            return self.pos().y() + self.parentItem().yoffset()
        else:
            return self.pos().y()

    def xpos(self):
        """
        Calculates the x position of this node using the x offset
        :return: the x position of the node
        """
        return self.rect().x() + self.rect().width() / 2 + self.xoffset()

    def ypos(self):
        """
        Calculates the y position of this node using the y offset
        :return: the y position of the node
        """
        return self.rect().y() + self.rect().height() / 2 + self.yoffset()

    def collapse_upwards(self):
        """
        Collapses the tree upwards only displaying this node and its children
        :return:
        """
        # store collapse data used to restore the state when expanding
        self.collapse_data = {
            "abs_pos": QPointF(self.xoffset(), self.yoffset()),
            "rel_pos": self.pos(),
            "abs_top_level_pos": QPointF(self.topLevelItem().xoffset(), self.topLevelItem().yoffset()),
            "parent": self.parentItem(),
            "top_level_item": self.topLevelItem()
        }
        # disconnect parent this prevents the node from being hidden
        self.setParentItem(None)
        # set absolute position to retain correct position
        self.setPos(self.collapse_data['abs_pos'])
        # hide parent nodes
        self.collapse_data['top_level_item'].hide()

    def expand_upwards(self):
        """
        Expands the tree upwards displaying all expanded parent nodes
        :return:
        """
        new_abs_pos = QPointF(self.xoffset(), self.yoffset())
        top_level_item = self.collapse_data['top_level_item']
        new_abs_top_level_pos = QPointF(top_level_item.xoffset(), top_level_item.yoffset())
        # reset parent item
        self.setParentItem(self.collapse_data['parent'])
        # reset relative position to parent
        self.setPos(self.collapse_data['rel_pos'] + (
                (new_abs_pos - self.collapse_data['abs_pos']) -
                (new_abs_top_level_pos - self.collapse_data['abs_top_level_pos'])
            )
        )
        # show expanded parent nodes
        self.topLevelItem().show()

    def collapse_children(self):
        """
        Collapses this node's children by hiding all child edges (and therefore the whole subtree)
        """
        for c in self.childItems():
            if isinstance(c, Edge):
                c.hide()
        self.children_collapsed = True

    def expand_children(self):
        """
        Expands this node's children by showing all child edges previously hidden by the collapse function
        """
        for c in self.childItems():
            if isinstance(c, Edge):
                c.show()
        self.children_collapsed = False

    def mousePressEvent(self, m_event):
        """
        Handles a mouse press on a node
        :param m_event: The mouse press event and its details
        """
        super(Node, self).mousePressEvent(m_event)

    def mouseMoveEvent(self, m_event):
        """
        Handles a mouse move over a node
        :param m_event: The mouse move event and its details
        """
        super(Node, self).mouseMoveEvent(m_event)
        if self.dragging:
            # move the node with the mouse and adjust the edges to the new position
            dx = m_event.scenePos().x() - m_event.lastScenePos().x()
            dy = m_event.scenePos().y() - m_event.lastScenePos().y()
            self.setPos(self.pos().x() + dx, self.pos().y() + dy)
            # reposition incoming edge
            if isinstance(self.parentItem(), Edge):
                self.parentItem().change_position()
