"""Memory facade backed by the shared task repository."""
from .database import get_memories as _get_memories
from .database import save_memory as _save_memory

get_memories = _get_memories
save_memory = _save_memory

def init_memory() -> None:
    """Memory tables are initialized together with the main database schema."""
