import uuid
from sqlmodel import select
from datetime import datetime
from typing import List, Optional

from nonebot import get_driver
from nonebot_plugin_datastore import create_session

from .move import Move
from .board import Board
from .config import Config
from .model import GameRecord
from .engine import UCCIEngine

cchess_config = Config.parse_obj(get_driver().config.dict())


class Player:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __eq__(self, player: "Player") -> bool:
        return self.id == player.id

    def __str__(self) -> str:
        return self.name


class AiPlayer(Player):
    def __init__(self, level: int = 4):
        self.level = level
        self.id = 1000 + level
        self.name = f"AI lv.{level}"
        self.engine = UCCIEngine(cchess_config.cchess_engine_path)
        time_list = [100, 400, 700, 1000, 1500, 2000, 3000, 5000]
        self.time = time_list[level - 1]
        depth_list = [5, 5, 5, 5, 8, 12, 17, 25]
        self.depth = depth_list[level - 1]

    async def get_move(self, position: str) -> Move:
        return await self.engine.bestmove(position, time=self.time, depth=self.depth)


class Game(Board):
    def __init__(self):
        super().__init__()
        self.player_red: Optional[Player] = None
        self.player_black: Optional[Player] = None
        self.id = uuid.uuid4().hex
        self.start_time = datetime.now()
        self.update_time = datetime.now()

    @property
    def player_next(self) -> Optional[Player]:
        return self.player_red if self.moveside else self.player_black

    @property
    def player_last(self) -> Optional[Player]:
        return self.player_black if self.moveside else self.player_red

    @property
    def is_battle(self) -> bool:
        return not isinstance(self.player_red, AiPlayer) and not isinstance(
            self.player_black, AiPlayer
        )

    def close_engine(self):
        if isinstance(self.player_red, AiPlayer):
            self.player_red.engine.close()
        if isinstance(self.player_black, AiPlayer):
            self.player_black.engine.close()

    async def save_record(self, session_id: str):
        statement = select(GameRecord).where(GameRecord.id == self.id)
        async with create_session() as session:
            record: Optional[GameRecord] = await session.scalar(statement)
            if not record:
                record = GameRecord(id=self.id, session_id=session_id)
            if self.player_red:
                record.player_red_id = str(self.player_red.id)
                record.player_red_name = self.player_red.name
            if self.player_black:
                record.player_black_id = str(self.player_black.id)
                record.player_black_name = self.player_black.name
            record.start_time = self.start_time
            self.update_time = datetime.now()
            record.update_time = self.update_time
            record.start_fen = self.start_fen
            record.moves = " ".join([str(move) for move in self.moves])
            record.is_game_over = self.is_game_over()
            session.add(record)
            await session.commit()

    @classmethod
    async def load_record(cls, session_id: str) -> Optional["Game"]:
        async def load_player(id: str, name: str) -> Optional[Player]:
            if not id:
                return None
            if len(id) > 4:
                return Player(int(id), name)
            else:
                level = int(id[-1])
                if not (1 <= level <= 8):
                    level = 4
                player = AiPlayer(level)
                await player.engine.open()
                return player

        statement = select(GameRecord).where(
            GameRecord.session_id == session_id, GameRecord.is_game_over == False
        )
        async with create_session() as session:
            records: List[GameRecord] = (await session.exec(statement)).all()  # type: ignore
        if not records:
            return None
        record = sorted(records, key=lambda x: x.update_time)[-1]
        game = cls()
        game.id = record.id
        game.player_red = await load_player(
            record.player_red_id, record.player_red_name
        )
        game.player_black = await load_player(
            record.player_black_id, record.player_black_name
        )
        game.start_time = record.start_time
        game.update_time = record.update_time
        start_fen = record.start_fen
        moves = [Move.from_ucci(move) for move in record.moves.split(" ")]
        game.from_fen(start_fen)
        for move in moves:
            game.push(move)
        return game
