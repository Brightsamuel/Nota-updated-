from datetime import datetime

class Note:
    def __init__(self, title, content, note_id=None, created_at=None, updated_at=None, is_pinned=0, is_locked=0, folder_id=None, tags=None):
        self.id = note_id
        self.title = title
        self.content = content
        self.created_at = self._parse_datetime(created_at)
        self.updated_at = self._parse_datetime(updated_at)
        self.is_pinned = is_pinned
        self.is_locked = is_locked
        self.folder_id = folder_id
        self.tags = tags  # Store tags as comma-separated string

    def _parse_datetime(self, dt_value):
        """Parse various datetime formats into a datetime object.
        
        Handles:
        - None values
        - Existing datetime objects
        - String timestamps in '%Y-%m-%d %H:%M:%S' format
        - SQLite objects with isoformat() method
        """
        if dt_value is None:
            return None
            
        # If already a datetime object, return as is
        if isinstance(dt_value, datetime):
            return dt_value
            
        # Try to parse string format
        if isinstance(dt_value, str):
            try:
                return datetime.strptime(dt_value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try alternative formats if needed
                try:
                    return datetime.fromisoformat(dt_value)
                except (ValueError, AttributeError):
                    return datetime.now()  # Fallback to current time if parsing fails
                    
        # Handle SQLite objects that may have isoformat method
        try:
            if hasattr(dt_value, 'isoformat'):
                dt_str = dt_value.isoformat()
                return datetime.fromisoformat(dt_str)
        except (ValueError, AttributeError):
            pass
            
        # Last resort: return current time
        return datetime.now()

    @classmethod
    def from_db_row(cls, row):
        """Create a Note object from a database row"""
        if row is None:
            return None

        # Handle missing columns safely without using .get()
        is_pinned = 0
        is_locked = 0
        folder_id = None
        tags = ""
        
        # Check if columns exist before accessing them
        if 'is_pinned' in row.keys():
            is_pinned = row['is_pinned']
        if 'is_locked' in row.keys():
            is_locked = row['is_locked']
        if 'folder_id' in row.keys():
            folder_id = row['folder_id']
        if 'tags' in row.keys():
            tags = row['tags'] if row['tags'] else ""
        
        return cls(
            title=row['title'],
            content=row['content'],
            note_id=row['id'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_pinned=is_pinned,
            is_locked=is_locked,
            folder_id=folder_id,
            tags=tags
        )
        
    def add_tag(self, new_tag):
        """Add a new tag if it doesn't already exist."""
        if not self.tags:
            self.tags = new_tag
        else:
            # Parse existing tags
            tag_list = [tag.strip() for tag in self.tags.split(',')]
            if new_tag not in tag_list:
                tag_list.append(new_tag)
                self.tags = ', '.join(tag_list)
    
    def remove_tag(self, tag_to_remove):
        """Remove a tag if it exists."""
        if not self.tags:
            return
        
        tag_list = [tag.strip() for tag in self.tags.split(',')]
        if tag_to_remove in tag_list:
            tag_list.remove(tag_to_remove)
            self.tags = ', '.join(tag_list)
            if not tag_list:  # No tags left
                self.tags = ""
    
    def get_tag_list(self):
        """Return a list of tags."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]