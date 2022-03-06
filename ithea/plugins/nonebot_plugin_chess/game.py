import uuid
import chess
import chess.svg
import chess.engine
from sqlmodel import select
from chess import Board, Move
from datetime import datetime
from typing import List, Optional

from nonebot import get_driver
from nonebot_plugin_htmlrender import html_to_pic
from nonebot_plugin_datastore import create_session

from .config import Config
from .model import GameRecord

chess_config = Config.parse_obj(get_driver().config.dict())


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
        self.engine_path = chess_config.chess_engine_path.resolve()
        time_list = [50, 100, 150, 200, 300, 400, 500, 1000]
        self.time = time_list[level - 1] / 1000
        depth_list = [5, 5, 5, 5, 5, 8, 13, 22]
        self.depth = depth_list[level - 1]

    async def open_engine(self):
        if not self.engine_path.exists():
            raise FileNotFoundError("找不到UCI引擎！")
        _, engine = await chess.engine.popen_uci(str(self.engine_path))
        self.engine = engine

    async def get_move(self, board: Board) -> Optional[Move]:
        result = await self.engine.play(
            board, chess.engine.Limit(time=self.time, depth=self.depth)
        )
        return result.move

    async def close_engine(self):
        await self.engine.quit()


class Game:
    def __init__(self):
        self.board = Board()
        self.player_white: Optional[Player] = None
        self.player_black: Optional[Player] = None
        self.id = uuid.uuid4().hex
        self.start_time = datetime.now()
        self.update_time = datetime.now()

    @property
    def player_next(self) -> Optional[Player]:
        return (
            self.player_white if self.board.turn == chess.WHITE else self.player_black
        )

    @property
    def player_last(self) -> Optional[Player]:
        return (
            self.player_black if self.board.turn == chess.WHITE else self.player_white
        )

    @property
    def is_battle(self) -> bool:
        return not isinstance(self.player_white, AiPlayer) and not isinstance(
            self.player_black, AiPlayer
        )

    async def close_engine(self):
        if isinstance(self.player_white, AiPlayer):
            await self.player_white.close_engine()
        if isinstance(self.player_black, AiPlayer):
            await self.player_black.close_engine()

    async def draw(self) -> bytes:
        lastmove = self.board.move_stack[-1] if self.board.move_stack else None
        check = lastmove.to_square if lastmove and self.board.is_check() else None
        orientation = (
            self.board.turn
            if self.is_battle
            else chess.WHITE
            if isinstance(self.player_black, AiPlayer)
            else chess.BLACK
        )
        svg = chess.svg.board(
            self.board,
            orientation=orientation,
            lastmove=lastmove,
            check=check,
            size=1000,
        )
        return await html_to_pic(
            f'<html><body style="margin: 0;">{svg}</body></html>',
            viewport={"width": 100, "height": 100},
        )

    async def save_record(self, session_id: str):
        statement = select(GameRecord).where(GameRecord.id == self.id)
        async with create_session() as session:
            record: Optional[GameRecord] = await session.scalar(statement)
            if not record:
                record = GameRecord(id=self.id, session_id=session_id)
            if self.player_white:
                record.player_white_id = str(self.player_white.id)
                record.player_white_name = self.player_white.name
            if self.player_black:
                record.player_black_id = str(self.player_black.id)
                record.player_black_name = self.player_black.name
            record.start_time = self.start_time
            self.update_time = datetime.now()
            record.update_time = self.update_time
            record.start_fen = self.board.starting_fen
            record.moves = " ".join([str(move) for move in self.board.move_stack])
            record.is_game_over = self.board.is_game_over()
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
                await player.open_engine()
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
        game.player_white = await load_player(
            record.player_white_id, record.player_white_name
        )
        game.player_black = await load_player(
            record.player_black_id, record.player_black_name
        )
        game.start_time = record.start_time
        game.update_time = record.update_time
        start_fen = record.start_fen
        game.board = Board(start_fen)
        for move in record.moves.split(" "):
            game.board.push_uci(move)
        return game
