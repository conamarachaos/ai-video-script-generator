"""Animated loader utility for displaying progress during API calls."""

import asyncio
import threading
import time
from typing import Optional, List
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from contextlib import contextmanager
import random


class AnimatedLoader:
    """Animated loader to show during API calls."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the loader with a console."""
        self.console = console or Console()
        self.live = None
        self.stop_event = threading.Event()
        self.thread = None
        
        # Different spinner styles
        self.spinners = [
            "dots", "dots2", "dots3", "dots8", "dots9", "dots12",
            "line", "line2", "pipe", "simpleDots", "simpleDotsScrolling",
            "star", "star2", "flip", "hamburger", "growVertical",
            "growHorizontal", "balloon", "balloon2", "noise", "bounce",
            "boxBounce", "boxBounce2", "triangle", "arc", "circle",
            "squareCorners", "circleQuarters", "circleHalves", "squish",
            "toggle", "toggle2", "toggle3", "toggle4", "toggle5",
            "toggle6", "toggle7", "toggle8", "toggle9", "toggle10",
            "toggle11", "toggle12", "toggle13", "arrow", "arrow2",
            "arrow3", "bouncingBar", "bouncingBall", "pong", "shark"
        ]
        
        # Fun loading messages
        self.messages = [
            "🤖 Thinking deeply...",
            "🧠 Processing your request...",
            "✨ Crafting the perfect response...",
            "🎭 Consulting the AI muses...",
            "📝 Writing something amazing...",
            "🎨 Creating content magic...",
            "🚀 Launching creative engines...",
            "💡 Generating brilliant ideas...",
            "🔮 Peering into the creative cosmos...",
            "⚡ Powering up the AI...",
            "🎪 Orchestrating the agents...",
            "🎯 Focusing on your needs...",
            "🌟 Summoning creative spirits...",
            "📚 Consulting the knowledge base...",
            "🎬 Directing your video script...",
            "🎤 Preparing expert insights...",
            "🔧 Fine-tuning the response...",
            "🎉 Almost there...",
            "☕ Brewing something special...",
            "🌈 Adding finishing touches..."
        ]
        
        self.current_message_index = 0
        self.message_change_interval = 2.0  # Change message every 2 seconds
        self.last_message_change = time.time()
        
    def _get_random_message(self) -> str:
        """Get a random loading message."""
        return random.choice(self.messages)
    
    def _rotate_message(self) -> str:
        """Rotate through messages sequentially."""
        current_time = time.time()
        if current_time - self.last_message_change > self.message_change_interval:
            self.current_message_index = (self.current_message_index + 1) % len(self.messages)
            self.last_message_change = current_time
        return self.messages[self.current_message_index]
    
    @contextmanager
    def loading(self, initial_message: str = None, spinner_style: str = "dots12"):
        """Context manager for showing loader during operations.
        
        Args:
            initial_message: Initial message to display
            spinner_style: Style of spinner to use
        """
        if initial_message is None:
            initial_message = self._get_random_message()
        
        # Start the loader
        self.start(initial_message, spinner_style)
        try:
            yield self
        finally:
            # Stop the loader
            self.stop()
    
    def start(self, message: str = None, spinner_style: str = "dots12"):
        """Start the animated loader."""
        if message is None:
            message = self._get_random_message()
        
        self.stop_event.clear()
        self.current_message_index = 0
        self.last_message_change = time.time()
        
        # Choose spinner style
        if spinner_style not in self.spinners:
            spinner_style = "dots12"
        
        spinner = Spinner(spinner_style, text=Text(message, style="cyan"))
        self.live = Live(spinner, console=self.console, refresh_per_second=10)
        self.live.start()
        
        # Start thread to update messages
        self.thread = threading.Thread(target=self._update_messages, args=(spinner_style,))
        self.thread.daemon = True
        self.thread.start()
    
    def _update_messages(self, spinner_style: str):
        """Update loading messages periodically."""
        while not self.stop_event.is_set():
            time.sleep(0.1)  # Small sleep to reduce CPU usage
            
            # Update message periodically
            new_message = self._rotate_message()
            if self.live:
                spinner = Spinner(spinner_style, text=Text(new_message, style="cyan"))
                self.live.update(spinner)
    
    def update_message(self, message: str):
        """Update the loader message."""
        if self.live:
            # Keep the same spinner but update text
            spinner = self.live.renderable
            if isinstance(spinner, Spinner):
                spinner.text = Text(message, style="cyan")
                self.live.update(spinner)
    
    def stop(self):
        """Stop the animated loader."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)
        if self.live:
            self.live.stop()
            self.live = None


class MultiStageLoader:
    """Loader that shows different stages of processing."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the multi-stage loader."""
        self.console = console or Console()
        self.stages = []
        self.current_stage = 0
        self.loader = AnimatedLoader(console)
    
    def add_stage(self, message: str):
        """Add a processing stage."""
        self.stages.append(message)
    
    def next_stage(self):
        """Move to the next stage."""
        if self.current_stage < len(self.stages):
            self.loader.update_message(self.stages[self.current_stage])
            self.current_stage += 1
    
    @contextmanager
    def loading(self, stages: List[str] = None):
        """Context manager for multi-stage loading."""
        if stages:
            self.stages = stages
        
        if not self.stages:
            self.stages = [
                "🤖 Initializing AI agent...",
                "🧠 Processing your request...",
                "✨ Generating response...",
                "📝 Formatting output..."
            ]
        
        self.current_stage = 0
        with self.loader.loading(self.stages[0] if self.stages else "Processing..."):
            yield self
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


# Convenience functions
def create_loader(console: Optional[Console] = None) -> AnimatedLoader:
    """Create a new animated loader."""
    return AnimatedLoader(console)


def create_multi_stage_loader(console: Optional[Console] = None, stages: List[str] = None) -> MultiStageLoader:
    """Create a new multi-stage loader."""
    loader = MultiStageLoader(console)
    if stages:
        for stage in stages:
            loader.add_stage(stage)
    return loader


# Async wrapper for use with async functions
class AsyncLoader:
    """Async-compatible loader wrapper."""
    
    def __init__(self, loader: AnimatedLoader):
        """Initialize with an AnimatedLoader."""
        self.loader = loader
    
    async def __aenter__(self):
        """Async enter."""
        self.loader.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit."""
        self.loader.stop()
    
    def update(self, message: str):
        """Update loader message."""
        self.loader.update_message(message)


def async_loader(message: str = None, console: Optional[Console] = None) -> AsyncLoader:
    """Create an async-compatible loader."""
    loader = AnimatedLoader(console)
    if message:
        loader.current_message_index = loader.messages.index(message) if message in loader.messages else 0
    return AsyncLoader(loader)