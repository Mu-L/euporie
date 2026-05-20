"""Define a docking split container widget."""

from __future__ import annotations

import logging
from enum import Enum, auto
from functools import partial
from typing import TYPE_CHECKING, NamedTuple

from apptk.application.current import get_app
from apptk.border import OutsetGrid
from apptk.cache import SimpleCache
from apptk.filters import Condition
from apptk.layout.containers import (
    ConditionalContainer,
    DynamicContainer,
    Float,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
)
from apptk.layout.decor import DropShadow
from apptk.layout.dimension import Dimension as D
from apptk.layout.mouse import MouseHandlerWrapper
from apptk.mouse_events import MouseButton, MouseEventType
from apptk.widgets.tab_bar import TabBarControl, TabBarTab

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from apptk.border import GridStyle
    from apptk.color import Color
    from apptk.formatted_text.base import AnyFormattedText
    from apptk.key_binding.key_bindings import NotImplementedOrNone
    from apptk.layout.containers import AnyContainer, Container
    from apptk.layout.dimension import AnyDimension
    from apptk.mouse_events import MouseEvent

log = logging.getLogger(__name__)


class DockPosition(Enum):
    """Position where a panel can be docked."""

    CENTER = auto()
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()


class DockingPanel(NamedTuple):
    """A panel that can be docked in a DockingSplit.

    Args:
        title: The tab title for this panel.
        content: The container content to display.
        closeable: Whether the panel can be closed.
    """

    title: AnyFormattedText
    content: AnyContainer
    closeable: bool = False


class DockingGroup:
    """A leaf node in the docking tree containing tabbed panels.

    This represents a group of panels displayed as tabs. Users can drag
    tabs to rearrange them within the group or dock them elsewhere.

    Args:
        panels: Initial list of panels in this group.
        active: Index of the initially active panel.
        docking_split: Reference to the parent DockingSplit for drag coordination.
    """

    def __init__(
        self,
        panels: list[DockingPanel],
        active: int = 0,
        docking_split: DockingSplit | None = None,
    ) -> None:
        """Initialize the docking group."""
        self.panels = list(panels)
        self._active = min(active, max(0, len(panels) - 1))
        self.docking_split = docking_split
        self._container_cache: SimpleCache = SimpleCache(maxsize=1)
        self._built_container: AnyContainer | None = None

    @property
    def active(self) -> int:
        """Return the index of the active panel."""
        return self._active

    @active.setter
    def active(self, value: int) -> None:
        """Set the active panel index."""
        if self.panels:
            self._active = max(0, min(value, len(self.panels) - 1))
        else:
            self._active = 0

    def active_content(self) -> AnyContainer:
        """Return the currently active panel's content."""
        if self.panels:
            return self.panels[self.active].content
        return Window()

    def load_tabs(self) -> list[TabBarTab]:
        """Generate TabBarTab entries for the tab bar control."""
        tabs = []
        for i, panel in enumerate(self.panels):
            tabs.append(
                TabBarTab(
                    title=panel.title,
                    on_activate=partial(self._activate_tab, i),
                    on_close=partial(self._close_tab, i) if panel.closeable else None,
                    closeable=panel.closeable,
                )
            )
        return tabs

    def _activate_tab(self, index: int) -> None:
        """Activate a tab by index."""
        self.active = index

    def _close_tab(self, index: int) -> None:
        """Close a tab by index."""
        if 0 <= index < len(self.panels):
            self.panels.pop(index)
            if self.active >= len(self.panels):
                self.active = max(0, len(self.panels) - 1)
            if self.docking_split:
                self.docking_split.cleanup_empty_groups()
                self.docking_split.rebuild()

    def remove_panel(self, index: int) -> DockingPanel:
        """Remove and return a panel at the given index.

        Args:
            index: The index of the panel to remove.

        Returns:
            The removed panel.
        """
        panel = self.panels.pop(index)
        if self.active >= len(self.panels):
            self.active = max(0, len(self.panels) - 1)
        return panel

    def insert_panel(self, panel: DockingPanel, index: int | None = None) -> None:
        """Insert a panel at the given index.

        Args:
            panel: The panel to insert.
            index: Position to insert at. If None, appends to end.
        """
        if index is None:
            self.panels.append(panel)
            self.active = len(self.panels) - 1
        else:
            self.panels.insert(index, panel)
            self.active = index


class DockingNode:
    """A split node in the docking tree.

    Contains two children arranged either horizontally or vertically.

    Args:
        direction: "horizontal" for top/bottom split, "vertical" for left/right.
        first: The first child (top or left).
        second: The second child (bottom or right).
    """

    def __init__(
        self,
        direction: str,
        first: DockingGroup | DockingNode,
        second: DockingGroup | DockingNode,
    ) -> None:
        """Initialize the docking node."""
        self.direction = direction
        self.first = first
        self.second = second


class DragState:
    """State tracking for an active drag operation.

    Args:
        source_group: The group the tab is being dragged from.
        tab_index: The index of the tab being dragged.
    """

    def __init__(self, source_group: DockingGroup, tab_index: int) -> None:
        """Initialize drag state."""
        self.source_group = source_group
        self.tab_index = tab_index
        self.target_group: DockingGroup | None = None
        self.position: DockPosition = DockPosition.CENTER


class DockingTabBarControl(TabBarControl):
    """A tab bar control that supports drag-to-dock.

    Extends TabBarControl to detect mouse drag events on tabs and
    communicate with the parent DockingSplit to initiate docking operations.
    """

    def __init__(
        self,
        group: DockingGroup,
        docking_split: DockingSplit,
        **kwargs: object,
    ) -> None:
        """Initialize the docking tab bar control.

        Args:
            group: The DockingGroup this tab bar belongs to.
            docking_split: The parent DockingSplit managing docking state.
            **kwargs: Additional arguments passed to TabBarControl.
        """
        self.group = group
        self.docking_split = docking_split
        super().__init__(
            tabs=group.load_tabs,
            active=lambda: group.active,
            **kwargs,
        )

    def mouse_handler(self, mouse_event: MouseEvent) -> NotImplementedOrNone:
        """Handle mouse events, detecting drag initiation."""
        # Let the parent handle close buttons, scroll, and tab activation first
        result = super().mouse_handler(mouse_event)
        if result is None:
            # Parent handled it (e.g., close button click) — cancel any drag
            if self.docking_split.drag_state is not None:
                self.docking_split.drag_state = None
                self.docking_split.reset_drop_zones()
            return None

        row = mouse_event.position.y
        col = mouse_event.position.x

        if row == 1 and mouse_event.button == MouseButton.LEFT:
            if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                # Determine which tab was clicked
                tab_index = self._get_tab_at_col(col)
                if tab_index is not None:
                    self.docking_split.start_drag(self.group, tab_index)
                    # Also activate the tab
                    self.group.active = tab_index
                    return None

            elif mouse_event.event_type == MouseEventType.MOUSE_MOVE:
                if self.docking_split.drag_state is not None:
                    # Update drag position
                    self.docking_split.update_drag(mouse_event)
                    return None

            elif mouse_event.event_type == MouseEventType.MOUSE_UP:
                if self.docking_split.drag_state is not None:
                    self.docking_split.end_drag()
                    return None

        return result

    def _get_tab_at_col(self, col: int) -> int | None:
        """Determine which tab index is at the given column position.

        Args:
            col: The column position to check.

        Returns:
            The tab index at that position, or None if no tab is there.
        """
        pos = self.spacing
        for i, width in enumerate(self.tab_widths):
            if pos <= col < pos + width:
                return i
            pos += width + self.spacing
        return None


class DropZone:
    """A drop zone overlay that highlights during drag operations."""

    def __init__(
        self,
        docking_split: DockingSplit,
        group: DockingGroup,
        position: DockPosition,
        color: Color | str = "#000000",
    ) -> None:
        """Initialize the drop zone control."""
        self.docking_split = docking_split
        self.group = group
        self.position = position
        self.shadow = DropShadow(amount=0, target=color)
        self.container = MouseHandlerWrapper(
            content=self.shadow, handler=self.mouse_handler
        )
        self.docking_split._drop_zones.append(self)

    def mouse_handler(self, mouse_event: MouseEvent) -> NotImplementedOrNone:
        """Handle mouse events to set the drop zone during drag.

        Returns:
            None if handled, NotImplemented otherwise.
        """
        drag_state = self.docking_split.drag_state
        if drag_state is None:
            self.shadow.amount = 0
            return NotImplemented

        if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
            self.docking_split.reset_drop_zones(active=self)
            drag_state.target_group = self.group
            drag_state.position = self.position
            self.shadow.amount = 0.5
            return None

        elif (
            mouse_event.event_type == MouseEventType.MOUSE_UP
            and mouse_event.button == MouseButton.LEFT
        ):
            drag_state.target_group = self.group
            drag_state.position = self.position
            self.docking_split.end_drag()
            return None

        return NotImplemented

    def __pt_container__(self) -> Container:
        """Return the container."""
        return self.container


class DockingSplit:
    """A container that supports docking panels by dragging tabs.

    Panels can be arranged in tabs (stacked) or tiled by dragging a tab
    to the edge of a group. Dragging to the left/right creates a vertical
    split, dragging to the top/bottom creates a horizontal split, and
    dragging to the center adds the panel as a tab.

    Args:
        panels: Initial list of panels to display.
        style: Style string for the container.
        width: Width dimension.
        height: Height dimension.
        border: Grid style for borders.
        h_padding: Horizontal padding between vertical splits.
        h_padding_char: Character used for horizontal padding.
        v_padding: Vertical padding between horizontal splits.
        v_padding_char: Character used for vertical padding.
    """

    def __init__(
        self,
        panels: Sequence[DockingPanel],
        style: str | Callable[[], str] = "",
        width: AnyDimension = None,
        height: AnyDimension = None,
        border: GridStyle = OutsetGrid,
        h_padding: int = 0,
        h_padding_char: str | None = "│",
        v_padding: int = 0,
        v_padding_char: str | None = "─",
    ) -> None:
        """Initialize the docking split."""
        self.style = style
        self.width = width
        self.height = height
        self.border = border
        self.h_padding = h_padding
        self.h_padding_char = h_padding_char
        self.v_padding = v_padding
        self.v_padding_char = v_padding_char
        self.drag_state: DragState | None = None
        self._drop_zones: list[DropZone] = []

        # Create initial root as a single group with all panels
        self.root: DockingGroup | DockingNode = DockingGroup(
            panels=list(panels),
            active=0,
            docking_split=self,
        )

        self.container = HSplit(
            [DynamicContainer(self._build_layout)],
            style=style,
            width=width,
            height=height,
        )

    def _build_layout(self) -> AnyContainer:
        """Build the layout from the docking tree."""
        return self._build_node(self.root)

    def _build_node(self, node: DockingGroup | DockingNode) -> AnyContainer:
        """Recursively build the container layout from a tree node.

        Args:
            node: The tree node to build.

        Returns:
            A container representing this node.
        """
        if isinstance(node, DockingGroup):
            return self._build_group(node)
        else:
            first = self._build_node(node.first)
            second = self._build_node(node.second)
            if node.direction == "horizontal":
                return HSplit(
                    [first, second],
                    style="class:docking-split",
                    padding=self.v_padding,
                    padding_char=self.v_padding_char,
                )
            else:
                return VSplit(
                    [first, second],
                    style="class:docking-split",
                    padding=self.h_padding,
                    padding_char=self.h_padding_char,
                )

    def _build_group(self, group: DockingGroup) -> AnyContainer:
        """Build the container for a single docking group.

        Returns a cached container for the group, only creating it once.
        The group is wrapped in a FloatContainer with per-zone Float overlays
        that appear during drag operations.

        Args:
            group: The group to build.

        Returns:
            A container with a tab bar, content area, and drop zone overlays.
        """
        if group._built_container is None:
            tab_bar = DockingTabBarControl(
                group=group,
                docking_split=self,
                grid=self.border,
            )

            is_dragging = Condition(lambda: self.drag_state is not None)

            def _make_zone(
                position: DockPosition,
                *,
                width: AnyDimension = None,
                height: AnyDimension = None,
            ) -> AnyContainer:
                return HSplit(
                    [DropZone(self, group, position)],
                    width=width,
                    height=height,
                )

            group._built_container = HSplit(
                [
                    Window(
                        tab_bar,
                        style="class:docking.tab-bar",
                        height=2,
                    ),
                    FloatContainer(
                        content=DynamicContainer(group.active_content),
                        floats=[
                            Float(
                                content=ConditionalContainer(
                                    VSplit(
                                        [
                                            _make_zone(
                                                DockPosition.LEFT,
                                                width=D(weight=1),
                                            ),
                                            HSplit(
                                                [
                                                    _make_zone(
                                                        DockPosition.TOP,
                                                        height=D(weight=1),
                                                    ),
                                                    _make_zone(
                                                        DockPosition.CENTER,
                                                        height=D(weight=3),
                                                    ),
                                                    _make_zone(
                                                        DockPosition.BOTTOM,
                                                        height=D(weight=1),
                                                    ),
                                                ],
                                                width=D(weight=3),
                                            ),
                                            _make_zone(
                                                DockPosition.RIGHT,
                                                width=D(weight=1),
                                            ),
                                        ]
                                    ),
                                    filter=is_dragging,
                                ),
                                top=0,
                                right=0,
                                bottom=0,
                                left=0,
                            ),
                        ],
                    ),
                ],
                style="class:docking.group",
            )

        return group._built_container

    def start_drag(self, group: DockingGroup, tab_index: int) -> None:
        """Begin a drag operation.

        Args:
            group: The group containing the tab being dragged.
            tab_index: The index of the tab being dragged.
        """
        if len(group.panels) > 0:
            self.drag_state = DragState(source_group=group, tab_index=tab_index)

    def update_drag(self, mouse_event: MouseEvent) -> None:
        """Update drag state based on mouse position.

        Args:
            mouse_event: The current mouse event.
        """
        if self.drag_state is None:
            return

        # Position detection is handled by DropZoneControl based on where
        # the mouse is within the target group's area. If the mouse event reaches
        # here, it is no longer over a drop zone.
        self.drag_state.target_group = None
        self.reset_drop_zones()

    def reset_drop_zones(self, active: DropZone | None = None) -> None:
        """Reset inactive drop zone shadows.

        Args:
            active: The drop zone that should remain highlighted.
        """
        for drop_zone in self._drop_zones:
            if drop_zone is not active:
                drop_zone.shadow.amount = 0

    def end_drag(self) -> None:
        """Complete a drag operation, docking the panel."""
        if self.drag_state is None:
            self.reset_drop_zones()
            return

        state = self.drag_state
        self.drag_state = None
        self.reset_drop_zones()

        target_group = state.target_group
        if target_group is None:
            return

        source_group = state.source_group
        tab_index = state.tab_index
        position = state.position

        # Don't do anything if dropping on same group center with only one tab
        if source_group is target_group and position == DockPosition.CENTER:
            return

        # Don't dock if source only has one panel and target is same group
        if source_group is target_group and len(source_group.panels) <= 1:
            return

        # Remove panel from source
        if tab_index >= len(source_group.panels):
            return
        panel = source_group.remove_panel(tab_index)

        if position == DockPosition.CENTER:
            # Add as a tab to the target group
            target_group.insert_panel(panel)
        else:
            # Create a new group for the dragged panel
            new_group = DockingGroup(
                panels=[panel],
                active=0,
                docking_split=self,
            )

            # Determine split direction and order
            if position in (DockPosition.LEFT, DockPosition.RIGHT):
                direction = "vertical"
                if position == DockPosition.LEFT:
                    first, second = new_group, target_group
                else:
                    first, second = target_group, new_group
            else:
                direction = "horizontal"
                if position == DockPosition.TOP:
                    first, second = new_group, target_group
                else:
                    first, second = target_group, new_group

            # Create new split node
            new_node = DockingNode(
                direction=direction,
                first=first,
                second=second,
            )

            # Replace target_group in the tree with new_node
            self._replace_node(target_group, new_node)

        # Clean up empty groups
        self.cleanup_empty_groups()
        self.rebuild()

    def _replace_node(
        self,
        old: DockingGroup | DockingNode,
        new: DockingGroup | DockingNode,
    ) -> None:
        """Replace a node in the tree with a new node.

        Args:
            old: The node to replace.
            new: The replacement node.
        """
        if self.root is old:
            self.root = new
            return

        # Search tree for parent of old
        self._replace_in_subtree(self.root, old, new)

    def _replace_in_subtree(
        self,
        parent: DockingGroup | DockingNode,
        old: DockingGroup | DockingNode,
        new: DockingGroup | DockingNode,
    ) -> bool:
        """Recursively search and replace a node in the tree.

        Args:
            parent: Current node being searched.
            old: The node to find and replace.
            new: The replacement node.

        Returns:
            True if the replacement was made.
        """
        if not isinstance(parent, DockingNode):
            return False

        if parent.first is old:
            parent.first = new
            return True
        elif parent.second is old:
            parent.second = new
            return True

        return self._replace_in_subtree(
            parent.first, old, new
        ) or self._replace_in_subtree(parent.second, old, new)

    def cleanup_empty_groups(self) -> None:
        """Remove empty groups from the tree and collapse unnecessary splits."""
        self.root = self._cleanup_node(self.root)

    def _cleanup_node(
        self, node: DockingGroup | DockingNode
    ) -> DockingGroup | DockingNode:
        """Recursively clean up empty groups and collapse single-child splits.

        Args:
            node: The node to clean up.

        Returns:
            The cleaned-up node (may be a different node if collapsed).
        """
        if isinstance(node, DockingGroup):
            return node

        # Recursively clean children
        node.first = self._cleanup_node(node.first)
        node.second = self._cleanup_node(node.second)

        # If first child is empty group, return second
        if isinstance(node.first, DockingGroup) and not node.first.panels:
            return node.second

        # If second child is empty group, return first
        if isinstance(node.second, DockingGroup) and not node.second.panels:
            return node.first

        return node

    def rebuild(self) -> None:
        """Trigger a rebuild of the layout."""
        # The DynamicContainer will pick up changes automatically
        get_app().invalidate()

    def __pt_container__(self) -> Container:
        """Return the container."""
        return self.container
