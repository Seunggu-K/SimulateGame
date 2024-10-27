from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import random
import pandas as pd
from datetime import datetime
import sqlite3
import pytz

class Unit(Agent):
    def __init__(self, unique_id, faction, number, model):
        super().__init__(unique_id, model)
        self.faction = faction # 진영 구분을 위한 변수
        self.number = number # 해당 부대의 인원 수

    # 해당 부대가 행동할 때마다 실행되는 함수
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
                    if self in self.model.schedule._agents:
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
                    if agent in self.model.schedule._agents:
                        self.model.schedule.remove(agent)

            elif agent != self and agent.faction == self.faction:
                self.merge(agent)
                self.model.grid.remove_agent(agent)
                if agent in self.model.schedule._agents:
                    self.model.schedule.remove(agent)
    
    # 해당 부대가 이동했을 때, 이동한 위치에 다른 진영의 부대가 있으면 실행되는 함수
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

    # 해당 부대가 이동했을 때, 이동한 위치에 같은 진영의 부대가 있으면 실행되는 함수
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

    # 해당 부대의 위치를 변경하는 함수
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
        self.running = True

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

    def step(self):
        # 조건을 확인하고, 만족하면 모델 중단
        if self.chapter != 0 and len(set(agent.faction for agent in self.schedule._agents)) == 1:
            self.running = False
            print("Stopping model as condition is met.")

        # 스케줄 실행 (조건 충족 시 실행되지 않음)
        if self.running:
            self.schedule.step()

board_width = 1
board_height = 1
my_unit_count = 1
enemy_unit_count = 1

model = Board(board_width, board_height, my_unit_count, enemy_unit_count)
for i in range(20):
    if model.running:
        model.step()
        model.chapter = i

# model.df_result.to_csv(f"./log/{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.csv", index=False)

kst = pytz.timezone('Asia/Seoul')
model.df_result['created_date'] = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
model.df_result['active_agent_position_before_X'] = model.df_result['active_agent_position_before'].apply(lambda pos: pos[0] if isinstance(pos, tuple) else None)
model.df_result['active_agent_position_before_Y'] = model.df_result['active_agent_position_before'].apply(lambda pos: pos[1] if isinstance(pos, tuple) else None)
model.df_result['active_agent_position_after_X'] = model.df_result['active_agent_position_after'].apply(lambda pos: pos[0] if isinstance(pos, tuple) else None)
model.df_result['active_agent_position_after_Y'] = model.df_result['active_agent_position_after'].apply(lambda pos: pos[1] if isinstance(pos, tuple) else None)
model.df_result.drop(columns=['active_agent_position_before', 'active_agent_position_after'], inplace=True)
model.df_result['board_width'] = board_width
model.df_result['board_height'] = board_height
model.df_result['my_unit_count'] = my_unit_count
model.df_result['enemy_unit_count'] = enemy_unit_count

conn = sqlite3.connect('./db/board.db')
model.df_result.to_sql('board', conn, if_exists='append', index=False)
conn.commit()  # 변경 사항을 커밋
conn.close()   # 연결을 닫음