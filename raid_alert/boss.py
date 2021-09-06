from datetime import datetime


class Boss():

    def __init__(self, name, level, status, spawn_date, time_of_death=None):
        self.name = name
        self.level = level
        self.status = status
        self.spawn_date = spawn_date
        self.spawn_time = None
        self.time_of_death = time_of_death
        self.has_spawned = False
        self.has_died = False
        self.lifespan = None
        self.time_dead = None

    def update(self, fields):
        self.has_spawned, self.has_died = False, False
        if fields[2] == 'dead' and self.status == 'alive':
            self.time_of_death = datetime.now()
            if self.spawn_time is not None:
                self.lifespan = self.time_of_death - self.spawn_time
                self.lifespan = str(self.lifespan).split('.')[0]  # remove miliseconds
            self.has_died = True
        elif fields[2] == 'alive' and self.status == 'dead':
            self.spawn_time = datetime.now()
            self.has_spawned = True
            if self.time_of_death is not None:
                self.time_dead = self.spawn_time - self.time_of_death
                self.time_dead = str(self.time_dead).split('.')[0]  # remove miliseconds
        self.status = fields[2]
        self.spawn_date = fields[3]
