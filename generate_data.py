import json

import data

with open("data.json", "w") as f:
    json.dump({'goals': data.goals, 'teachers': data.teachers}, f, indent=4,ensure_ascii=False)
