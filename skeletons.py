from transitions import Machine
import asyncio
import random
import concurrent


class Creature:
    states = ['idle', 'attacking', 'defending', 'dead']
    def __init__(self, name, alive=True, machine=None, max_health=100, damage=5, action_time=3, target=None):
        self.name = name
        self.alive = alive
        self.max_health = max_health
        self.health = 100
        self.defense = False
        self.target = target
        self.damage = damage

        self.action_time = action_time

        self.action_task = None

        self.machine = machine or Machine(model=self, states=Creature.states, initial='idle', before_state_change='ambient_sounds')
        self.machine.add_transition(trigger='begin_attack', source='idle', dest='attacking', after = 'on_begin_attack')
        self.machine.add_transition(trigger='interrupt', source='attacking', dest='idle', after = 'on_interrupt')
        self.machine.add_transition(trigger='begin_defense', source='idle', dest='defending', after = 'on_defend')
        self.machine.add_transition(trigger='action_complete', source='attacking', dest='idle', after='on_attack')
        self.machine.add_transition(trigger='action_complete', source='defending', dest='idle', after='stop_defense')

        for state in Creature.states:
            if state != 'dead':
                self.machine.add_transition(trigger='die', source=state, dest='dead', after='on_death')

    def emit_message(self, text):
        print(text)

    def check_alive(self):
        if self.health <= 0:
            self.alive = False
            self.die()

    def take_damage(self, dmg):
        if not self.defense:
            if self.state == 'attacking':
                self.interrupt()
                

            self.emit_message(self,self.name+ ' takes damage: '+ str(dmg))
            self.health = self.health - dmg
            self.check_alive()
        else:

            self.emit_message(self,self.name+ ' blocked the attack!')

    def ambient_sounds(self):
        general_text = []
        if self.health < 50:
            health_text = ["Creature has not much hp"]
        elif self.health < 25:
            health_text = ["Creature almost dead"]
        else:
            health_text = ["Creature looks pretty healthy"]

        sound= random.choice(general_text + health_text)

    def on_death(self):
        self.emit_message(self, self.name + ' died.')

    def on_interrupt(self):
        self.action_task.cancel()
        self.action_task = None
        self.emit_message(self, self.name + ' was interrupted by the attack!')

    def on_begin_attack(self):
        self.emit_message(self, self.name + ':'+'preparing attack')

    def on_attack(self):
        self.emit_message(self, self.name + ':'+'attack landed')
        if self.target:
            self.target.take_damage(self.damage)

    def on_defend(self):
        self.emit_message(self, self.name + ':'+'defense')
        self.defense = True

    def stop_defense(self):
        self.emit_message(self, self.name + ':'+'no defense')
        self.defense = False

    

class Skeleton(Creature):
    def __init__(self, name, loop = None, alive=True, machine=None, max_health=100,  damage=5,action_time=3, target=None, targets=None):
        super(Skeleton, self).__init__(name, alive, machine, max_health, damage,action_time, target)
        self.loop = loop or asyncio.get_event_loop()
        self.targets = targets or []

    async def run(self):
        while True:
            if self.alive:
                if not self.target or not self.target.alive:
                    if len([x for x in self.targets if x.alive]) == 0:
                        await asyncio.sleep(5)
                    else:
                        self.target = random.choice(self.targets)
                        self.emit_message(self, 'Skeleton picked a new target: {}'.format(self.target.name))

                if self.target:
                    if self.state == 'idle':
                        dice_roll = random.choice([1, 2])
                        if dice_roll == 1:
                            #defend
                            self.begin_defense()
                            self.action_task = self.loop.call_later(self.action_time, self.action_complete)
                        elif dice_roll:
                            #attack
                            self.begin_attack()
                            self.action_task = self.loop.call_later(self.action_time, self.action_complete)  
            else:
                break

            await asyncio.sleep(1)

class Player(Creature):
    def __init__(self, name, loop = None, alive=True, machine=None, max_health=100, damage=20, action_time=2, target=None, client=None):
        super(Player, self).__init__(name, alive, machine, max_health, damage, action_time, target)
        self.loop = loop or asyncio.get_event_loop()
        self.client = client

    async def attack(self):
        if self.alive and self.target and self.target.alive:
            if self.state == 'idle':
                    self.begin_attack()
                    self.action_task = self.loop.call_later(self.action_time, self.action_complete)    
            else:
                self.emit_message(self, "Can't attack now!")

    async def defend(self):
        if self.alive and self.target and self.target.alive:
            if self.state == 'idle':
                    self.begin_defense()
                    self.action_task = self.loop.call_later(self.action_time, self.action_complete)
            else:
                self.emit_message(self, "Can't defend now!")       

