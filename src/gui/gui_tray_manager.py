"""
GUI System Tray Manager for Desktop GUI Application

This module implements system tray integration using pystray, allowing the application
to minimize to the system tray and display status indicators.

Requirements implemented:
- 9.1: Minimize to system tray instead of exiting when close button is clicked
- 9.2: Display application icon in system tray
- 9.3: Restore main window when system tray icon is clicked
- 9.4: Display context menu with Show, Settings, Exit options
- 9.5: Settings toggle to enable/disable system tray integration
- 9.6: Visual indicator (animation or badge) while task is running
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Callable
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    pystray = None
    item = None

logger = logging.getLogger(__name__)


class GUITrayManager:
    """
    Manages system tray integration for the GUI application.
    
    Provides functionality to:
    - Show/hide application icon in system tray
    - Handle tray icon clicks and context menu
    - Display visual indicators for task execution
    - Minimize to tray instead of closing
    """
    
    def __init__(self, 
                 icon_path: Optional[str] = None,
                 app_name: str = "Local AI Dev",
                 show_window_callback: Optional[Callable] = None,
                 open_settings_callback: Optional[Callable] = None,
                 quit_app_callback: Optional[Callable] = None):
        """
        Initialize the system tray manager.
        
        Args:
            icon_path: Path to the icon file (ICO, PNG, or None for default)
            app_name: Name to display in tray tooltip
            show_window_callback: Function to call to show/restore main window
            open_settings_callback: Function to call to open settings
            quit_app_callback: Function to call to quit application
            
        Requirements: 9.2, 9.4
        """
        if not PYSTRAY_AVAILABLE:
            logger.warning("pystray not available, system tray disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.app_name = app_name
        self.icon_path = icon_path
        self.show_window_callback = show_window_callback
        self.open_settings_callback = open_settings_callback
        self.quit_app_callback = quit_app_callback
        
        self.icon: Optional[pystray.Icon] = None
        self.icon_thread: Optional[threading.Thread] = None
        self.is_running_task = False
        
        # Load icon image
        self.base_icon = self._load_icon()
        self.running_icon = self._create_running_icon()
        
        logger.info("System tray manager initialized")
    
    def _load_icon(self) -> Image.Image:
        """
        Load the application icon from file or create a default one.
        
        Returns:
            PIL Image object
            
        Requirements: 9.2
        """
        # Try to load icon from specified path
        if self.icon_path:
            icon_file = Path(self.icon_path)
            if icon_file.exists():
                try:
                    logger.info(f"Loading icon from {icon_file}")
                    return Image.open(icon_file)
                except Exception as e:
                    logger.warning(f"Failed to load icon from {icon_file}: {e}")
        
        # Try to find icon in standard locations
        search_paths = [
            Path(__file__).parent.parent / 'web' / 'assets' / 'icon.ico',
            Path(__file__).parent.parent / 'web' / 'assets' / 'favicon.ico',
            Path(__file__).parent.parent.parent / 'icon.ico',
        ]
        
        for path in search_paths:
            if path.exists():
                try:
                    logger.info(f"Loading icon from {path}")
                    return Image.open(path)
                except Exception as e:
                    logger.warning(f"Failed to load icon from {path}: {e}")
        
        # Create a default icon if none found
        logger.info("Creating default icon")
        return self._create_default_icon()
    
    def _create_default_icon(self) -> Image.Image:
        """
        Create a simple default icon.
        
        Returns:
            PIL Image object (64x64 px)
        """
        # Create a 64x64 icon with a simple design
        size = 64
        image = Image.new('RGB', (size, size), color='#2196F3')
        draw = ImageDraw.Draw(image)
        
        # Draw a simple "AI" text or shape
        # For simplicity, draw a circle
        margin = 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill='#1976D2',
            outline='#FFFFFF',
            width=3
        )
        
        return image
    
    def _create_running_icon(self) -> Image.Image:
        """
        Create an icon variant that indicates a task is running.
        
        Adds a visual indicator (colored badge) to the base icon.
        
        Returns:
            PIL Image object with running indicator
            
        Requirements: 9.6
        """
        # Make a copy of the base icon
        icon = self.base_icon.copy()
        draw = ImageDraw.Draw(icon)
        
        # Add a green badge/dot in the bottom-right corner
        size = icon.size[0]
        badge_size = size // 4
        badge_x = size - badge_size - 2
        badge_y = size - badge_size - 2
        
        # Draw green circle badge
        draw.ellipse(
            [badge_x, badge_y, badge_x + badge_size, badge_y + badge_size],
            fill='#4CAF50',
            outline='#FFFFFF',
            width=2
        )
        
        return icon
    
    def start(self, minimize_to_tray: bool = True) -> bool:
        """
        Start the system tray icon.
        
        Args:
            minimize_to_tray: Whether tray integration is enabled in settings
            
        Returns:
            True if started successfully, False otherwise
            
        Requirements: 9.2, 9.5
        """
        if not self.enabled:
            logger.info("System tray not available")
            return False
        
        if not minimize_to_tray:
            logger.info("System tray disabled in settings")
            return False
        
        if self.icon is not None:
            logger.warning("System tray already running")
            return False
        
        try:
            # Create system tray icon (Req 9.2)
            self.icon = pystray.Icon(
                self.app_name,
                self.base_icon,
                self.app_name,
                menu=self._create_menu()
            )
            
            # Start icon in separate thread (non-blocking)
            self.icon_thread = threading.Thread(
                target=self._run_icon,
                daemon=True,
                name="SystemTray"
            )
            self.icon_thread.start()
            
            logger.info("System tray started")
            return True
            
        except Exception as e:
            logger.exception("Failed to start system tray")
            self.icon = None
            return False
    
    def _run_icon(self) -> None:
        """Run the system tray icon (blocking call)."""
        if self.icon:
            try:
                self.icon.run()
            except Exception as e:
                logger.exception("Error in system tray icon loop")
    
    def _create_menu(self) -> pystray.Menu:
        """
        Create the system tray context menu.
        
        Returns:
            pystray.Menu object with Show, Settings, Exit items
            
        Requirements: 9.4
        """
        return pystray.Menu(
            item('Show', self._on_show, default=True),
            item('Settings', self._on_settings),
            pystray.Menu.SEPARATOR,
            item('Exit', self._on_quit)
        )
    
    def _on_show(self, icon, item) -> None:
        """
        Handle 'Show' menu item click or icon left-click.
        
        Restores the main window from tray.
        
        Requirements: 9.3, 9.4
        """
        logger.info("Show window requested from tray")
        if self.show_window_callback:
            self.show_window_callback()
    
    def _on_settings(self, icon, item) -> None:
        """
        Handle 'Settings' menu item click.
        
        Opens the settings panel.
        
        Requirements: 9.4
        """
        logger.info("Settings requested from tray")
        if self.open_settings_callback:
            self.open_settings_callback()
        # Also show the window
        if self.show_window_callback:
            self.show_window_callback()
    
    def _on_quit(self, icon, item) -> None:
        """
        Handle 'Exit' menu item click.
        
        Quits the application completely.
        
        Requirements: 9.4
        """
        logger.info("Quit requested from tray")
        if self.quit_app_callback:
            self.quit_app_callback()
    
    def stop(self) -> None:
        """
        Stop the system tray icon and cleanup resources.
        """
        if self.icon:
            try:
                logger.info("Stopping system tray")
                self.icon.stop()
                self.icon = None
                
                # Wait for thread to finish (with timeout)
                if self.icon_thread and self.icon_thread.is_alive():
                    self.icon_thread.join(timeout=2.0)
                
                logger.info("System tray stopped")
            except Exception as e:
                logger.exception("Error stopping system tray")
    
    def set_task_running(self, is_running: bool) -> None:
        """
        Update the tray icon to indicate whether a task is running.
        
        Args:
            is_running: True if task is running, False otherwise
            
        Requirements: 9.6
        """
        if not self.icon:
            return
        
        self.is_running_task = is_running
        
        try:
            # Update icon image (Req 9.6: visual indicator for running tasks)
            if is_running:
                self.icon.icon = self.running_icon
                self.icon.title = f"{self.app_name} - Running task"
                logger.debug("Updated tray icon to running state")
            else:
                self.icon.icon = self.base_icon
                self.icon.title = self.app_name
                logger.debug("Updated tray icon to idle state")
        except Exception as e:
            logger.exception("Error updating tray icon")
    
    def update_tooltip(self, message: str) -> None:
        """
        Update the tray icon tooltip message.
        
        Args:
            message: Tooltip message to display
        """
        if self.icon:
            try:
                self.icon.title = message
            except Exception as e:
                logger.exception("Error updating tooltip")
    
    def is_running(self) -> bool:
        """
        Check if the system tray icon is currently running.
        
        Returns:
            True if running, False otherwise
        """
        return self.icon is not None and self.icon.visible
