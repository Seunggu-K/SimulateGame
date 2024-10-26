from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import random
import pandas as pd
from datetime import datetime

class Unit(Agent):
    def __init__(self, unique_id, faction, number, model):
        super().__init__(unique_id, model)
        self.faction = faction
        self.number = number

    def step(self):
        if self.pos is None:
            # x = self.random.randrange(self.model.grid.width)
            # y = self.random.randrange(self.model.grid.height)
            # self.model.grid.place_agent(self, (x, y))

            while True:
                x = random.randrange(self.model.grid.width)
                y = random.randrange(self.model.grid.height)
                if self.model.grid.is_cell_empty((x, y)):
                    break
                    
            self.model.grid.place_agent(self, (x, y))
        
        self.move()
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cellmates:
            if agent != self and agent.faction != self.faction:
                self.battle(agent)

                if self.number == 0:
                    # 행동 결과를 DataFrame에 추가
                    new_row = pd.DataFrame([{
                        'chapter': self.model.chapter,
                        'active_agent_id': self.unique_id,
                        'active_agent_faction': self.faction,
                        'target_agent_id': None,
                        'target_agent_faction': None,
                        'action_type': 'destroy',
                        'active_agent_number': self.number,
                        'target_agent_number': None,
                        'active_agent_position_before': self.pos,
                        'active_agent_position_after': self.pos
                    }])
                    self.model.df_result = pd.concat([self.model.df_result, new_row], ignore_index=True)
                    self.model.grid.remove_agent(self)
                    self.model.schedule.remove(self)
                
                if agent.number == 0:
                    # 행동 결과를 DataFrame에 추가
                    new_row = pd.DataFrame([{
                        'chapter': agent.model.chapter,
                        'active_agent_id': agent.unique_id,
                        'active_agent_faction': agent.faction,
                        'target_agent_id': None,
                        'target_agent_faction': None,
                        'action_type': 'destroy',
                        'active_agent_number': agent.number,
                        'target_agent_number': None,
                        'active_agent_position_before': agent.pos,
                        'active_agent_position_after': agent.pos
                    }])
                    self.model.df_result = pd.concat([self.model.df_result, new_row], ignore_index=True)
                    self.model.grid.remove_agent(agent)
                    self.model.schedule.remove(agent)

            elif agent != self and agent.faction == self.faction:
                self.merge(agent)
                self.model.grid.remove_agent(agent)
                self.model.schedule.remove(agent)
    
    def battle(self, agent):
        # player1_difference = self.number - agent.number
        # player2_difference = agent.number - self.number
        player1_dice = random.randint(1,6)
        player2_dice = random.randint(1,6)
        player1_score = player1_dice / 4 * self.number
        player2_score = player2_dice / 4 * agent.number
        
        # 병력 손실 비율 설정 (예시로 두 점수의 차이의 절반을 손실로 설정)
        if player1_score > player2_score:
            loss_ratio = (player1_score - player2_score) / (2 * self.number)
            self.number -= int(self.number * loss_ratio)  # 플레이어 1의 병력 감소
            agent.number -= int(agent.number * loss_ratio / 2)  # 플레이어 2의 병력 감소
        elif player2_score > player1_score:
            loss_ratio = (player2_score - player1_score) / (2 * agent.number)
            agent.number -= int(agent.number * loss_ratio)  # 플레이어 2의 병력 감소
            self.number -= int(self.number * loss_ratio / 2)  # 플레이어 1의 병력 감소
        else:
            # 무승부 시 병력 소모율 낮게 설정
            self.number -= player1_dice
            agent.number -= player2_dice

        # 행동 결과를 DataFrame에 추가
        new_row = pd.DataFrame([{
            'chapter': self.model.chapter,
            'active_agent_id': self.unique_id,
            'active_agent_faction': self.faction,
            'target_agent_id': agent.unique_id,
            'target_agent_faction': agent.faction,
            'action_type': 'battle',
            'active_agent_number': self.number,
            'target_agent_number': agent.number,
            'active_agent_position_before': self.pos,
            'active_agent_position_after': self.pos
        }])
        self.model.df_result = pd.concat([self.model.df_result, new_row], ignore_index=True)


    def merge(self, agent):
        self.number += agent.number

        # 병합 결과를 DataFrame에 추가
        new_row = pd.DataFrame([{
            'chapter': self.model.chapter,
            'active_agent_id': self.unique_id,
            'active_agent_faction': self.faction,
            'target_agent_id': agent.unique_id,
            'target_agent_faction': agent.faction,
            'action_type': 'merge',
            'active_agent_number': self.number,
            'target_agent_number': agent.number,
            'active_agent_position_before': self.pos,
            'active_agent_position_after': self.pos
        },{
            'chapter': self.model.chapter,
            'active_agent_id': agent.unique_id,
            'active_agent_faction': agent.faction,
            'target_agent_id': None,
            'target_agent_faction': None,
            'action_type': 'destroy',
            'active_agent_number': agent.number,
            'target_agent_number': None,
            'active_agent_position_before': agent.pos,
            'active_agent_position_after': agent.pos
        }])
        self.model.df_result = pd.concat([self.model.df_result, new_row], ignore_index=True)

    def move(self):
        current_position = self.pos
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

        # 행동 결과를 DataFrame에 추가
        new_row = pd.DataFrame([{
            'chapter': self.model.chapter,
            'active_agent_id': self.unique_id,
            'active_agent_faction': self.faction,
            'target_agent_id': None,
            'target_agent_faction': None,
            'action_type': 'move',
            'active_agent_number': self.number,
            'target_agent_number': None,
            'active_agent_position_before': current_position,
            'active_agent_position_after': self.pos
        }])
        self.model.df_result = pd.concat([self.model.df_result, new_row], ignore_index=True)


class Board(Model):
    def __init__(self, width, height, num_my_units, num_enemy_units):
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.num_my_units = num_my_units
        self.num_enemy_units = num_enemy_units
        self.chapter = 0

        self.df_result = pd.DataFrame(columns=['chapter','active_agent_id','active_agent_faction','target_agent_id','target_agent_faction','action_type','active_agent_number','target_agent_number','active_agent_position_before','active_agent_position_after'])

        # for i in range(self.num_enemy_units + self.num_my_units):
        #     unit = Unit(i, 0 if i < self.num_enemy_units else 1, 50, self)
        #     self.schedule.add(unit)
        #     x = self.random.randrange(self.grid.width)
        #     y = self.random.randrange(self.grid.height)
        #     self.grid.place_agent(unit, (x, y))

        for i in range(self.num_enemy_units + self.num_my_units):
            unit = Unit(i, 0 if i < self.num_enemy_units else 1, 50, self)
            self.schedule.add(unit)
            
            # 중복되지 않는 위치를 찾기
            while True:
                x = random.randrange(self.grid.width)
                y = random.randrange(self.grid.height)
                if self.grid.is_cell_empty((x, y)):
                    break
                    
            self.grid.place_agent(unit, (x, y))

        # for i in range(self.num_my_units):
        #     unit = Unit(i, 0, 50, self)
        #     self.schedule.add(unit)
        #     x = self.random.randrange(self.grid.width)
        #     y = self.random.randrange(self.grid.height)
        #     self.grid.place_agent(unit, (x, y))

        # for i in range(self.num_my_units, self.num_enemy_units):
        #     unit = Unit(i, 1, 50, self)
        #     self.schedule.add(unit)
        #     x = self.random.randrange(self.grid.width)
        #     y = self.random.randrange(self.grid.height)
        #     self.grid.place_agent(unit, (x, y))

    def step(self):
        self.schedule.step()


model = Board(10, 10, 5, 5)
for i in range(10):
    model.step()
    model.chapter = i

model.df_result.to_csv(f"./log/{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.csv", index=False)
