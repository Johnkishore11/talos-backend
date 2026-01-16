# Workshop Management

Unified tool for managing workshops in the database.

## Usage

### List all workshops
```bash
python workshop_manager.py list
```

### Add a workshop
```bash
python workshop_manager.py add <workshop_key>
```

Example:
```bash
python workshop_manager.py add byog
python workshop_manager.py add cybersecurity
```

### Delete a workshop
```bash
python workshop_manager.py delete <workshop_id>
```

Example:
```bash
python workshop_manager.py delete byog-workshop
python workshop_manager.py delete cybersecurity-ai-workshop
```

## Adding New Workshops

1. Open `workshops_data.py`
2. Add your workshop definition to the `WORKSHOPS` dictionary
3. Run `python workshop_manager.py add <your_workshop_key>`

## Workshop Data Structure

Each workshop should include:
- `workshop_id`: Unique identifier (slug format)
- `title`: Workshop title
- `description`: Short description
- `main_description`: Detailed description (optional)
- `rules`: Rules and guidelines (optional)
- `organisers`: List of organizers with name, phone, role (optional)
- `instructor`: Instructor name(s)
- `date`: Workshop date (YYYY-MM-DD)
- `time`: Workshop time
- `duration`: Duration (e.g., "2 Hours")
- `venue`: Venue name
- `image_url`: Workshop image URL
- `max_participants`: Maximum participants (optional)
- `registration_fee`: Fee in rupees
- `status`: "open" or "closed"
