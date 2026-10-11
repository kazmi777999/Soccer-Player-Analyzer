from dataclasses import dataclass


@dataclass
class Player:
    name: str
    team: str
    position: str
    goals: int
    assists: int
    matches: int
    minutes: int

    def goal_contributions(self):
        return (
            self.goals +
            self.assists
        )

    def goals_per_90(self):
        if self.minutes <= 0:
            return 0.0

        return (
            self.goals /
            self.minutes
        ) * 90

    def assists_per_90(self):
        if self.minutes <= 0:
            return 0.0

        return (
            self.assists /
            self.minutes
        ) * 90  

