from dataclasses import dataclass

@dataclass
class Budget:
    max_actions: int = 20
    max_minutes: int = 10
    def allows(self, action_count: int) -> bool:
        return action_count < self.max_actions

